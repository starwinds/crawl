import json
import time
from datetime import datetime
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import argparse
import schedule
import logging
from typing import List, Dict
import requests
from urllib.parse import quote

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('crawler.log')
    ]
)
logger = logging.getLogger(__name__)

class NaverNewsCrawler:
    def __init__(self, config):
        logger.info("크롤러 초기화 중...")
        self.config = config
        
        # 네이버 API 클라이언트 ID와 시크릿 설정
        self.client_id = config['naver_api']['client_id']
        self.client_secret = config['naver_api']['client_secret']
        
        # Slack 클라이언트 초기화
        if config['slack_settings']['enabled']:
            self.slack_client = WebClient(token=config['slack_settings']['bot_token'])
            self.channels = config['slack_settings']['channels']
        else:
            self.slack_client = None
        logger.info("크롤러 초기화 완료")

    def search_news(self, keyword: str, category: str, num_articles: int = 5) -> List[Dict]:
        """뉴스 검색 및 수집"""
        logger.info(f"'{keyword}' 검색 시작... (카테고리: {category})")
        
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        
        params = {
            "query": keyword,
            "display": num_articles,
            "sort": "date"
        }
        
        try:
            response = requests.get(
                "https://openapi.naver.com/v1/search/news.json",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            result = response.json()
            news_items = []
            
            for item in result.get('items', []):
                news_item = {
                    'category': category,
                    'keyword': keyword,
                    'title': item['title'].replace('<b>', '').replace('</b>', ''),
                    'press': item.get('publisher', '언론사 정보 없음'),
                    'summary': item['description'].replace('<b>', '').replace('</b>', ''),
                    'link': item['link'],
                    'crawled_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                news_items.append(news_item)
                logger.info(f"뉴스 항목 추가됨: {news_item['title'][:30]}...")
                
                # Slack으로 즉시 전송
                self.send_to_slack(news_item, category)
            
            logger.info(f"총 {len(news_items)}개의 뉴스 항목 수집 완료")
            return news_items
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API 요청 중 오류 발생: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"뉴스 검색 중 오류 발생: {str(e)}")
            return []

    def send_to_slack(self, news_item: Dict, category: str):
        """뉴스 항목을 해당 카테고리의 Slack 채널로 전송"""
        if not self.slack_client:
            return

        try:
            channel_name = self.config['search_keywords'][category]['channel']
            channel_id = self.channels.get(channel_name, self.channels['general'])
            
            message = self.config['slack_settings']['message_format'].format(
                title=news_item['title'],
                link=news_item['link'],
                press=news_item['press'],
                summary=news_item['summary']
            )
            
            self.slack_client.chat_postMessage(
                channel=channel_id,
                text=message,
                parse="mrkdwn"
            )
            logger.info(f"Slack 메시지 전송 완료: {channel_name} 채널 - {news_item['title'][:30]}...")
            
        except SlackApiError as e:
            logger.error(f"Slack 메시지 전송 실패: {str(e)}")

    def save_results(self, news_items: List[Dict], category: str):
        """수집된 뉴스를 JSON 파일로 저장"""
        if not news_items:
            return
            
        os.makedirs('results', exist_ok=True)
        filename = f"results/news_{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=2)
        
        logger.info(f"결과가 {filename}에 저장되었습니다.")

    def run_crawling(self):
        """크롤링 실행"""
        try:
            all_news_items = []
            
            for category, category_config in self.config['search_keywords'].items():
                logger.info(f"\n=== {category} 카테고리 크롤링 시작 ===")
                
                for keyword in category_config['keywords']:
                    news_items = self.search_news(
                        keyword=keyword,
                        category=category,
                        num_articles=category_config['max_articles']
                    )
                    all_news_items.extend(news_items)
                
                self.save_results(
                    [item for item in all_news_items if item['category'] == category],
                    category
                )
                
                logger.info(f"=== {category} 카테고리 크롤링 완료 ===\n")
                
        except Exception as e:
            logger.error(f"크롤링 중 오류 발생: {str(e)}")

def load_config(config_path='config.json'):
    """설정 파일 로드"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"설정 파일 형식이 잘못되었습니다: {config_path}")
        raise

def setup_schedule(crawler):
    """스케줄 설정"""
    schedule_settings = crawler.config['schedule_settings']
    if not schedule_settings['enabled']:
        return

    for execution_time in schedule_settings['execution_times']:
        schedule.every().day.at(execution_time).do(crawler.run_crawling)
        logger.info(f"스케줄 등록: 매일 {execution_time}에 실행")

def main():
    parser = argparse.ArgumentParser(description='네이버 뉴스 크롤러')
    parser.add_argument('--run-now', action='store_true', help='크롤러 즉시 실행')
    args = parser.parse_args()

    try:
        config = load_config()
        crawler = NaverNewsCrawler(config)

        if args.run_now:
            logger.info("크롤러를 즉시 실행합니다.")
            crawler.run_crawling()
            return

        setup_schedule(crawler)
        
        logger.info("크롤러가 스케줄 모드로 실행됩니다.")
        logger.info(f"실행 시간: {', '.join(config['schedule_settings']['execution_times'])}")
        
        # 무한 루프로 스케줄 실행
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 스케줄 체크

    except KeyboardInterrupt:
        logger.info("프로그램이 사용자에 의해 종료되었습니다.")
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()
