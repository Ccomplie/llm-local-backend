#!/bin/bash

echo "🔄 重启后端服务..."

# 停止现有服务
echo "停止现有服务..."
pkill -f "python3 start.py" 2>/dev/null || true
sleep 2

# 启动新服务
echo "启动后端服务..."
cd /media/cring/mydrive/llm-local-backend
python3 start.py &

# 等待服务启动
echo "等待服务启动..."
sleep 5

# 测试服务
echo "测试服务状态..."
python3 test_backend.py

echo "✅ 后端服务重启完成！"
