import torch
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class NewsRecommender:
    def __init__(self, slack_client: WebClient, channel_id: str):
        self.slack_client = slack_client
        self.channel_id = channel_id
        self.model = SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L3-v2')
        self.cache_file = 'news_cache.json'
        self.cache = self._load_cache()
        
    def _load_cache(self) -> Dict:
        """캐시 파일 로드"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"캐시 파일 로드 실패: {str(e)}")
        return {'sent_news': []}
        
    def _save_cache(self):
        """캐시 파일 저장"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"캐시 파일 저장 실패: {str(e)}")
            
    def _is_news_sent(self, news_item: Dict) -> bool:
        """뉴스가 이미 전송되었는지 확인"""
        # 24시간 이내의 캐시만 유지
        current_time = datetime.now()
        self.cache['sent_news'] = [
            news for news in self.cache['sent_news']
            if datetime.fromisoformat(news['sent_time']) > current_time - timedelta(hours=24)
        ]
        
        # URL 기반 중복 체크
        return any(
            news['link'] == news_item['link'] 
            for news in self.cache['sent_news']
        )
        
    def _is_similar_news(self, news_item: Dict, threshold: float = 0.85) -> bool:
        """유사한 뉴스가 이미 전송되었는지 확인"""
        if not self.cache['sent_news']:
            return False
            
        # 현재 뉴스의 임베딩 생성
        current_embedding = self.model.encode(news_item['summary'])
        
        # 캐시된 뉴스들과 유사도 비교
        for cached_news in self.cache['sent_news']:
            cached_embedding = self.model.encode(cached_news['summary'])
            similarity = torch.nn.functional.cosine_similarity(
                torch.tensor(current_embedding),
                torch.tensor(cached_embedding),
                dim=0
            )
            if similarity > threshold:
                return True
        return False
        
    def get_representative_news(self, news_items: List[Dict]) -> Dict:
        """Find the most representative news article using embeddings"""
        if not news_items:
            return None
            
        # 이미 전송된 뉴스 제외
        valid_news = [
            item for item in news_items
            if not self._is_news_sent(item) and not self._is_similar_news(item)
        ]
        
        if not valid_news:
            logger.info("모든 뉴스가 이미 전송되었거나 유사한 뉴스가 존재합니다.")
            return None
            
        # Extract summaries and create embeddings
        summaries = [item['summary'] for item in valid_news]
        embeddings = self.model.encode(summaries)
        
        # Calculate mean embedding
        mean_embedding = torch.mean(torch.tensor(embeddings), dim=0)
        
        # Find the article closest to the mean embedding
        distances = torch.norm(torch.tensor(embeddings) - mean_embedding, dim=1)
        most_representative_idx = torch.argmin(distances).item()
        
        return valid_news[most_representative_idx]
        
    def send_recommendation(self, news_item: Dict):
        """Send the recommended news to Slack"""
        try:
            # RSS와 Naver 뉴스의 키 차이 처리
            press = news_item.get('press', news_item.get('source', 'Unknown Source'))
            
            message = f"📰 *대표 뉴스 추천*\n\n*{news_item['title']}*\n{news_item['link']}\n출처: {press}\n\n{news_item['summary']}"
            
            self.slack_client.chat_postMessage(
                channel=self.channel_id,
                text=message,
                parse="mrkdwn"
            )
            
            # 캐시에 전송된 뉴스 추가
            self.cache['sent_news'].append({
                'title': news_item['title'],
                'link': news_item['link'],
                'summary': news_item['summary'],
                'sent_time': datetime.now().isoformat()
            })
            self._save_cache()
            
            logger.info(f"대표 뉴스 추천 메시지 전송 완료: {news_item['title'][:30]}...")
            
        except SlackApiError as e:
            logger.error(f"Slack 메시지 전송 실패: {str(e)}")
        except KeyError as e:
            logger.error(f"필수 키가 누락되었습니다: {str(e)}. 뉴스 항목: {news_item}") 