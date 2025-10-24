# 多阶段构建 - 后端服务
FROM python:3.8-slim as backend

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 配置pip镜像源
RUN pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p models uploads logs

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python3", "start.py"]

# 多阶段构建 - 前端服务
FROM node:18-alpine as frontend

# 设置工作目录
WORKDIR /app

# 配置npm镜像源
RUN npm config set registry https://registry.npmmirror.com

# 复制package.json
COPY frontend/package.json .

# 安装依赖
RUN npm install

# 复制前端代码
COPY frontend/ .

# 构建前端
RUN npm run build

# 使用nginx服务前端
FROM nginx:alpine as frontend-server

# 复制构建好的前端文件
COPY --from=frontend /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
