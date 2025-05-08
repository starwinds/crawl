FROM python:3.9-slim

# Set timezone to KST
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install PyTorch first
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install sentence-transformers and its dependencies
RUN pip install --no-cache-dir \
    sentence-transformers \
    transformers \
    scikit-learn \
    nltk

# Install other requirements
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt')"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/results

# Create entrypoint script
RUN echo '#!/bin/bash\n\
\n\
# Function to start a process and log its output\n\
start_process() {\n\
    local script=$1\n\
    local log_file=$2\n\
    echo "Starting $script..."\n\
    if [ "$RUN_NOW" = "true" ]; then\n\
        python $script --run-now\n\
    else\n\
        python $script >> $log_file 2>&1 &\n\
    fi\n\
}\n\
\n\
# Set RUN_NOW based on argument\n\
if [ "$1" = "--run-now" ]; then\n\
    export RUN_NOW=true\n\
else\n\
    export RUN_NOW=false\n\
fi\n\
\n\
# Start crawlers\n\
start_process "crawler.py" "/app/logs/crawler.log"\n\
start_process "rss_main.py" "/app/logs/rss_crawler.log"\n\
\n\
# Keep container running if not in run-now mode\n\
if [ "$RUN_NOW" = "false" ]; then\n\
    tail -f /app/logs/*.log\n\
fi' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD []