#!/bin/bash

echo "🛑 停止大模型本地化前后端服务..."

# 停止后端服务
if [ -f "/tmp/llm_backend.pid" ]; then
    BACKEND_PID=$(cat /tmp/llm_backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "🛑 停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        sleep 2
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo "🔨 强制停止后端服务..."
            kill -9 $BACKEND_PID
        fi
        echo "✅ 后端服务已停止"
    else
        echo "ℹ️  后端服务未运行"
    fi
    rm -f /tmp/llm_backend.pid
else
    echo "ℹ️  未找到后端服务PID文件"
fi

# 停止前端服务
if [ -f "/tmp/llm_frontend.pid" ]; then
    FRONTEND_PID=$(cat /tmp/llm_frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "🛑 停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        sleep 2
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo "🔨 强制停止前端服务..."
            kill -9 $FRONTEND_PID
        fi
        echo "✅ 前端服务已停止"
    else
        echo "ℹ️  前端服务未运行"
    fi
    rm -f /tmp/llm_frontend.pid
else
    echo "ℹ️  未找到前端服务PID文件"
fi

# 清理可能残留的进程
echo "🧹 清理残留进程..."
pkill -f "python3 start.py" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

echo "✅ 所有服务已停止"
echo ""
echo "💡 如需重新启动，请运行: ./start_all.sh"
