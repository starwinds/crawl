import argparse
import schedule
import time
import logging
import json
from rss_crawler import RSSNewsCrawler

def load_config(config_path='config.json'):
    """설정 파일 로드"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        raise
    except json.JSONDecodeError:
        logging.error(f"설정 파일 형식이 잘못되었습니다: {config_path}")
        raise

def setup_schedule(crawler):
    """스케줄 설정"""
    schedule_settings = crawler.config['schedule_settings']
    if not schedule_settings['enabled']:
        return

    for execution_time in schedule_settings['execution_times']:
        schedule.every().day.at(execution_time).do(crawler.run_crawling)
        logging.info(f"RSS 스케줄 등록: 매일 {execution_time}에 실행")

def main():
    parser = argparse.ArgumentParser(description='RSS 뉴스 크롤러')
    parser.add_argument('--run-now', action='store_true', help='크롤러 즉시 실행')
    args = parser.parse_args()

    try:
        config = load_config()
        crawler = RSSNewsCrawler(config)

        if args.run_now:
            logging.info("RSS 크롤러를 즉시 실행합니다.")
            crawler.run_crawling()
            return

        setup_schedule(crawler)
        
        logging.info("RSS 크롤러가 스케줄 모드로 실행됩니다.")
        logging.info(f"실행 시간: {', '.join(config['schedule_settings']['execution_times'])}")
        
        # 무한 루프로 스케줄 실행
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 스케줄 체크

    except KeyboardInterrupt:
        logging.info("프로그램이 사용자에 의해 종료되었습니다.")
    except Exception as e:
        logging.error(f"프로그램 실행 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    main() 