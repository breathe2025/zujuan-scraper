FROM python:3.12-slim

WORKDIR /app

# 使用国内镜像加速 pip
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 安装 Playwright 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Chromium 浏览器（国内镜像加速）
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
RUN python -m playwright install --with-deps chromium

COPY . .

EXPOSE 5000

CMD ["python", "server.py", "--port", "5000"]
