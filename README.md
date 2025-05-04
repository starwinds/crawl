# 네이버 뉴스 & RSS 뉴스 크롤러

네이버 뉴스 API와 RSS 피드를 사용하여 뉴스를 수집하고 Slack으로 전송하는 크롤러입니다.

## 주요 기능

1. **네이버 뉴스 크롤러**
   - 네이버 뉴스 API를 사용하여 뉴스 수집
   - 카테고리별 키워드 검색
   - Slack 채널별 뉴스 전송
   - 스케줄링된 시간에 자동 실행

2. **RSS 뉴스 크롤러**
   - RSS 피드에서 뉴스 수집
   - 영어 기사 자동 한글 번역
   - Slack의 rss-news 채널로 전송
   - 스케줄링된 시간에 자동 실행

## 설치 및 설정

1. **필요 패키지 설치**
```bash
pip install -r requirements.txt
```

2. **설정 파일 구성**
- `config.json` 파일에 다음 정보 설정:
  - 네이버 API 클라이언트 ID와 시크릿
  - Slack 봇 토큰
  - Slack 채널 ID
  - RSS 피드 URL 목록
  - 스케줄 실행 시간

## 실행 방법

1. **테스트 모드 (즉시 실행)**
```bash
# 네이버 뉴스 크롤러
python crawler.py --run-now

# RSS 뉴스 크롤러
python rss_main.py --run-now
```

2. **스케줄 모드 (백그라운드 실행)**
```bash
# 네이버 뉴스 크롤러
python crawler.py

# RSS 뉴스 크롤러
python rss_main.py
```

3. **Docker 사용**
```bash
# 테스트 모드
docker run --name news-crawler-test naver-news-crawler --run-now

# 스케줄 모드
docker run -d --name news-crawler -v $(pwd)/logs:/app/logs naver-news-crawler
```

## 로그 및 결과

- 네이버 뉴스 크롤러 로그: `crawler.log`
- RSS 뉴스 크롤러 로그: `rss_crawler.log`
- 수집된 뉴스 결과: `results/` 디렉토리

## 주의사항

1. 네이버 API 사용 시 API 키가 필요합니다.
2. Slack 메시지 전송을 위해서는 Slack 봇 토큰이 필요합니다.
3. RSS 피드의 영어 기사는 googletrans를 사용하여 한글로 자동 번역됩니다.
4. Docker 사용 시 로그 파일은 호스트 시스템의 `./logs` 디렉토리에 저장됩니다. 