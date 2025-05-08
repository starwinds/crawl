import torch
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)

class NewsRecommender:
    def __init__(self, slack_client: WebClient, channel_id: str):
        self.slack_client = slack_client
        self.channel_id = channel_id
        self.model = SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L3-v2')
        
    def get_representative_news(self, news_items: List[Dict]) -> Dict:
        """Find the most representative news article using embeddings"""
        if not news_items:
            return None
            
        # Extract summaries and create embeddings
        summaries = [item['summary'] for item in news_items]
        embeddings = self.model.encode(summaries)
        
        # Calculate mean embedding
        mean_embedding = torch.mean(torch.tensor(embeddings), dim=0)
        
        # Find the article closest to the mean embedding
        distances = torch.norm(torch.tensor(embeddings) - mean_embedding, dim=1)
        most_representative_idx = torch.argmin(distances).item()
        
        return news_items[most_representative_idx]
        
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
            logger.info(f"대표 뉴스 추천 메시지 전송 완료: {news_item['title'][:30]}...")
            
        except SlackApiError as e:
            logger.error(f"Slack 메시지 전송 실패: {str(e)}")
        except KeyError as e:
            logger.error(f"필수 키가 누락되었습니다: {str(e)}. 뉴스 항목: {news_item}") 