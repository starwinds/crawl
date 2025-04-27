# Naver News Crawler

네이버 뉴스 API를 사용하여 뉴스를 수집하고 Slack으로 전송하는 크롤러입니다.

## 기능

- 네이버 뉴스 API를 통한 뉴스 검색
- 카테고리별 키워드 검색
- Slack 채널로 뉴스 전송
- JSON 파일로 결과 저장
- 스케줄링 기능

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/yourusername/naver-news-crawler.git
cd naver-news-crawler
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

3. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

## 설정 방법

1. `config.json` 파일을 복사하여 `config.local.json` 파일 생성
```bash
cp config.json config.local.json
```

2. `config.local.json` 파일에서 다음 항목들을 실제 값으로 교체:
   - `YOUR_NAVER_CLIENT_ID`: 네이버 개발자 센터에서 발급받은 Client ID
   - `YOUR_NAVER_CLIENT_SECRET`: 네이버 개발자 센터에서 발급받은 Client Secret
   - `YOUR_SLACK_BOT_TOKEN`: Slack 봇 토큰
   - `YOUR_TECH_CHANNEL_ID`: Slack 채널 ID들

## 사용 방법

1. 즉시 실행
```bash
python crawler.py --run-now
```

2. 스케줄 모드로 실행
```bash
python crawler.py
```

## 스케줄 설정

`config.json` 파일의 `schedule_settings` 섹션에서 실행 시간을 설정할 수 있습니다:

```json
"schedule_settings": {
    "enabled": true,
    "execution_times": ["09:00", "15:00", "21:00"]
}
```

## 라이선스

MIT License 