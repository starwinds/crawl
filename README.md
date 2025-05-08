# News Crawler and Recommender

뉴스 크롤링 및 AI 기반 대표 뉴스 추천 시스템

## 주요 기능

1. 네이버 뉴스 크롤링
   - 카테고리별 키워드 기반 뉴스 수집
   - Slack 채널로 실시간 전송
   - JSON 파일로 결과 저장

2. RSS 피드 크롤링
   - TechCrunch, ZDNet 등 해외 IT 뉴스 수집
   - 자동 번역 기능 (영어 → 한글)
   - Slack 채널로 실시간 전송
   - JSON 파일로 결과 저장

3. AI 기반 대표 뉴스 추천
   - Hugging Face의 sentence-transformers/paraphrase-MiniLM-L3-v2 모델 사용
   - 뉴스 요약 내용 기반 대표성 분석
   - 저사양 서버 환경에 최적화
   - Slack today1pick 채널로 추천 뉴스 전송

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. config.json 설정:
   - Naver API 클라이언트 ID/시크릿
   - Slack Bot 토큰
   - 채널 ID 설정
   - 검색 키워드 설정
   - RSS 피드 URL 설정

## 실행 방법

1. 즉시 실행:
```bash
# 네이버 뉴스 크롤러
python crawler.py --run-now

# RSS 크롤러
python rss_main.py --run-now
```

2. 스케줄 모드 실행:
```bash
# 네이버 뉴스 크롤러
python crawler.py

# RSS 크롤러
python rss_main.py
```

## 설정 파일 (config.json)

```json
{
    "naver_api": {
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_CLIENT_SECRET"
    },
    "slack_settings": {
        "enabled": true,
        "bot_token": "YOUR_BOT_TOKEN",
        "channels": {
            "tech-news": "CHANNEL_ID",
            "economy-news": "CHANNEL_ID",
            "edu-news": "CHANNEL_ID",
            "rss-news": "CHANNEL_ID",
            "today1pick": "CHANNEL_ID"
        },
        "recommendation_channel": "today1pick"
    }
}
```

## 로그 확인

- 네이버 뉴스 크롤러: `crawler.log`
- RSS 크롤러: `rss_crawler.log`

## 최근 업데이트

- AI 기반 대표 뉴스 추천 기능 추가
- RSS 크롤러에 대표 뉴스 추천 기능 통합
- 요약이 없는 뉴스 항목 자동 필터링
- Slack 메시지 포맷 개선
- 에러 처리 및 로깅 개선

## 주의사항

1. 네이버 API 사용 시 API 키가 필요합니다.
2. Slack 메시지 전송을 위해서는 Slack 봇 토큰이 필요합니다.
3. RSS 피드의 영어 기사는 googletrans를 사용하여 한글로 자동 번역됩니다.
4. Docker 사용 시 로그 파일은 호스트 시스템의 `./logs` 디렉토리에 저장됩니다. 