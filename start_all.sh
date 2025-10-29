#!/bin/bash

echo "🚀 启动大模型本地化前后端服务..."

# 检查当前目录
if [ ! -f "main.py" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi

# 检查npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装"
    exit 1
fi

echo "✅ 环境检查通过"

# 停止可能正在运行的服务
echo "🛑 停止可能正在运行的服务..."
pkill -f "python3 start.py" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
sleep 2

# 启动后端服务
echo "🔧 启动后端服务..."
# cd /media/cring/mydrive/llm-local-backend
source .env.optimized 2>/dev/null || true
# nohup python3 start.py > logs/backend.log 2>&1 &
nohup python3 start.py >logs/nohup.log 2>&1 &
BACKEND_PID=$!
echo "   后端服务PID: $BACKEND_PID"

# 等待后端启动
echo "⏳ 等待后端服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/v1/health >/dev/null 2>&1; then
        echo "✅ 后端服务启动成功"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ 后端服务启动超时"
        exit 1
    fi
    sleep 1
done

# 启动前端服务的
echo "🎨 启动前端服务..."
cd frontend

# 检查是否需要安装依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   前端服务PID: $FRONTEND_PID"

# 等待前端启动
echo "⏳ 等待前端服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        echo "✅ 前端服务启动成功"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ 前端服务启动超时"
        exit 1
    fi
    sleep 1
done

# 保存PID到文件
echo $BACKEND_PID > /tmp/llm_backend.pid
echo $FRONTEND_PID > /tmp/llm_frontend.pid

echo ""
echo "🎉 前后端服务启动完成！"
echo ""
echo "📱 访问地址："
echo "   前端页面: http://localhost:3000"
echo "   后端API: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo ""
echo "📊 服务状态："
echo "   后端服务: http://localhost:8000/api/v1/health"
echo "   前端服务: http://localhost:3000"
echo ""
echo "📝 日志文件："
echo "   后端日志: logs/backend.log"
echo "   前端日志: logs/frontend.log"
echo ""
echo "🛑 停止服务："
echo "   ./stop_all.sh"
echo "   或手动: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "💡 提示："
echo "   - 前端页面支持智能Agent对话"
echo "   - 算力资源管理页面可监控GPU状态"
echo "   - 存储资源管理页面可管理文件"
echo "   - 系统资源管理页面可监控系统状态"
echo "   - 模型服务管理页面可管理多个模型"
echo ""
