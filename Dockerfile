# 使用官方 Python 镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY bot.py .

# 设置环境变量（可在docker run时覆盖）
ENV WS_URL="ws://10.70.210.49:3001/?access_token=Y15055724418yang"
ENV DEEPSEEK_API_KEY="sk-dab127c60046464a851e703ebc5b0ffd"

# 容器启动命令
CMD ["python", "bot.py"]