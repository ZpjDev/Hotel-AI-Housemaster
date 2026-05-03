FROM python:3.11-slim

WORKDIR /app

# 使用国内镜像源加速
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 微信云托管要求使用 80 端口
EXPOSE 80

# 确保数据目录存在
RUN mkdir -p /app/data

# 启动服务，监听 80 端口（微信云托管要求）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--workers", "2"]
