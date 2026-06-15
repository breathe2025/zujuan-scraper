FROM python:3.12-slim

WORKDIR /app

# 先安装 Playwright，它会自动处理浏览器依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Chromium 及其系统依赖
RUN python -m playwright install --with-deps chromium

COPY . .

EXPOSE 5000

CMD ["python", "server.py", "--port", "5000"]
