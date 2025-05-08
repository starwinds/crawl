import feedparser
import json
from datetime import datetime
import os
import logging
from typing import List, Dict
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import requests
from bs4 import BeautifulSoup
from googletrans import Translator
from news_recommender import NewsRecommender

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rss_crawler.log')
    ]
)
logger = logging.getLogger(__name__)

class RSSNewsCrawler:
    def __init__(self, config):
        logger.info("RSS 크롤러 초기화 중...")
        self.config = config
        
        # Slack 클라이언트 초기화
        if config['slack_settings']['enabled']:
            self.slack_client = WebClient(token=config['slack_settings']['bot_token'])
            self.channels = config['slack_settings']['channels']
            # 뉴스 추천기 초기화
            recommendation_channel = config['slack_settings']['recommendation_channel']
            self.news_recommender = NewsRecommender(
                self.slack_client,
                self.channels[recommendation_channel]
            )
        else:
            self.slack_client = None
            
        # 번역기 초기화
        self.translator = Translator()
        logger.info("RSS 크롤러 초기화 완료")

    def fetch_feed(self, feed_url: str) -> List[Dict]:
        """RSS 피드에서 뉴스 항목 가져오기"""
        logger.info(f"RSS 피드 가져오기: {feed_url}")
        
        try:
            feed = feedparser.parse(feed_url)
            news_items = []
            
            for entry in feed.entries:
                # 기사 내용 요약
                summary = self._summarize_article(entry.link)
                
                news_item = {
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.published if hasattr(entry, 'published') else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'summary': summary,
                    'source': feed.feed.title if hasattr(feed.feed, 'title') else 'Unknown Source',
                    'crawled_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                news_items.append(news_item)
                logger.info(f"RSS 뉴스 항목 추가됨: {news_item['title'][:30]}...")
                
                # Slack으로 즉시 전송
                self.send_to_slack(news_item)
            
            logger.info(f"총 {len(news_items)}개의 RSS 뉴스 항목 수집 완료")
            return news_items
            
        except Exception as e:
            logger.error(f"RSS 피드 파싱 중 오류 발생: {str(e)}")
            return []

    def _summarize_article(self, url: str) -> str:
        """기사 내용 요약 및 번역"""
        try:
            logger.info(f"기사 내용 추출 시도: {url}")
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 사이트별 맞춤형 선택자
            if 'techcrunch.com' in url:
                logger.info("TechCrunch 기사 처리 중...")
                # TechCrunch의 기사 내용은 여러 div에 분산되어 있음
                article_content = soup.find('div', class_='article-content')
                if not article_content:
                    article_content = soup.find('div', class_='content')
                if not article_content:
                    article_content = soup.find('div', class_='entry-content')
            elif 'zdnet.com' in url:
                logger.info("ZDNet 기사 처리 중...")
                # ZDNet의 기사 내용은 여러 가능한 클래스에 있음
                article_content = soup.find('div', class_='storyBody')
                if not article_content:
                    logger.info("storyBody 클래스 찾기 실패, 다음 선택자 시도...")
                    article_content = soup.find('div', class_='article-content')
                if not article_content:
                    logger.info("article-content 클래스 찾기 실패, 다음 선택자 시도...")
                    article_content = soup.find('div', class_='story-body')
                if not article_content:
                    logger.info("story-body 클래스 찾기 실패, 다음 선택자 시도...")
                    article_content = soup.find('div', class_='story-body-container')
                if not article_content:
                    logger.info("story-body-container 클래스 찾기 실패, 다음 선택자 시도...")
                    article_content = soup.find('article')
                if not article_content:
                    logger.info("article 태그 찾기 실패, 다음 선택자 시도...")
                    # ZDNet의 경우 메인 콘텐츠가 div#content에 있을 수 있음
                    article_content = soup.find('div', id='content')
                if not article_content:
                    logger.info("div#content 찾기 실패, 다음 선택자 시도...")
                    # ZDNet의 경우 메인 콘텐츠가 div.main-content에 있을 수 있음
                    article_content = soup.find('div', class_='main-content')
                if not article_content:
                    logger.info("div.main-content 찾기 실패, 다음 선택자 시도...")
                    # ZDNet의 경우 메인 콘텐츠가 div.article-body에 있을 수 있음
                    article_content = soup.find('div', class_='article-body')
            
            if article_content:
                logger.info("기사 내용을 찾았습니다. 요약 생성 중...")
                # 첫 3문단을 요약으로 사용
                paragraphs = article_content.find_all('p')
                if not paragraphs:
                    logger.info("p 태그를 찾을 수 없습니다. div 내의 텍스트를 직접 추출합니다.")
                    # p 태그가 없는 경우, div 내의 텍스트를 직접 추출
                    paragraphs = [article_content]
                
                summary = ' '.join([p.text.strip() for p in paragraphs[:3]])
                
                # 요약이 200자 이상이면 자르기
                if len(summary) > 200:
                    summary = summary[:200] + '...'
                
                # 영어인 경우 한글로 번역
                if self._is_english(summary):
                    logger.info("영어 기사 감지, 번역 시작...")
                    summary = self._translate_to_korean(summary)
                
                logger.info("기사 요약 완료")
                return summary
            
            logger.warning(f"기사 내용을 찾을 수 없습니다. URL: {url}")
            return "기사 내용을 추출할 수 없습니다."
            
        except Exception as e:
            logger.error(f"기사 요약 중 오류 발생: {str(e)}")
            return "기사 내용을 요약할 수 없습니다."

    def _is_english(self, text: str) -> bool:
        """텍스트가 영어인지 확인"""
        try:
            # 영어 문자와 공백의 비율이 70% 이상이면 영어로 간주
            english_chars = sum(1 for c in text if c.isalpha() and ord(c) < 128)
            total_chars = sum(1 for c in text if c.isalpha())
            return (english_chars / total_chars) > 0.7 if total_chars > 0 else False
        except:
            return False

    def _translate_to_korean(self, text: str) -> str:
        """googletrans를 사용하여 영어를 한글로 번역"""
        try:
            # 번역 시도
            translated = self.translator.translate(text, src='en', dest='ko')
            return translated.text
        except Exception as e:
            logger.error(f"번역 중 오류 발생: {str(e)}")
            return text

    def send_to_slack(self, news_item: Dict):
        """뉴스 항목을 Slack 채널로 전송"""
        if not self.slack_client:
            return

        try:
            # 항상 rss-news 채널 사용
            channel_id = self.channels['rss-news']
            
            message = self.config['slack_settings']['message_format'].format(
                title=news_item['title'],
                link=news_item['link'],
                press=news_item['source'],
                summary=news_item['summary']
            )
            
            self.slack_client.chat_postMessage(
                channel=channel_id,
                text=message,
                parse="mrkdwn"
            )
            logger.info(f"Slack 메시지 전송 완료: RSS 뉴스 - {news_item['title'][:30]}...")
            
        except SlackApiError as e:
            logger.error(f"Slack 메시지 전송 실패: {str(e)}")
        except KeyError as e:
            logger.error(f"필수 키가 누락되었습니다: {str(e)}. 뉴스 항목: {news_item}")

    def save_results(self, news_items: List[Dict]):
        """수집된 뉴스를 JSON 파일로 저장"""
        if not news_items:
            return
            
        os.makedirs('results', exist_ok=True)
        filename = f"results/rss_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=2)
        
        logger.info(f"RSS 결과가 {filename}에 저장되었습니다.")

    def run_crawling(self):
        """RSS 크롤링 실행"""
        try:
            all_news_items = []
            
            for feed_url in self.config['rss_settings']['feeds']:
                logger.info(f"\n=== RSS 피드 크롤링 시작: {feed_url} ===")
                news_items = self.fetch_feed(feed_url)
                all_news_items.extend(news_items)
                logger.info(f"=== RSS 피드 크롤링 완료 ===\n")
            
            # 요약이 있는 뉴스만 필터링
            valid_news_items = [item for item in all_news_items if item['summary'] and item['summary'] != "기사 내용을 추출할 수 없습니다."]
            
            # 대표 뉴스 추천
            if valid_news_items and self.slack_client:
                representative_news = self.news_recommender.get_representative_news(valid_news_items)
                if representative_news:
                    self.news_recommender.send_recommendation(representative_news)
            
            self.save_results(all_news_items)
                
        except Exception as e:
            logger.error(f"RSS 크롤링 중 오류 발생: {str(e)}") 