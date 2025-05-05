FROM python:3.9-slim

# Set timezone to KST
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set environment variables
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Create entrypoint script
RUN echo '#!/bin/bash\n\
if [ "$1" = "--run-now" ]; then\n\
    python crawler.py --run-now\n\
    python rss_main.py --run-now\n\
else\n\
    python crawler.py >> /app/logs/crawler.log 2>&1 &\n\
    python rss_main.py >> /app/logs/rss_crawler.log 2>&1\n\
fi' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD []