#!/bin/bash

echo "🚀 快速启动大模型本地化服务..."

# 检查服务状态
echo "📊 检查服务状态..."
if curl -s http://localhost:8000/api/v1/health >/dev/null 2>&1; then
    echo "✅ 后端服务已运行"
else
    echo "🔧 启动后端服务..."
    cd /media/cring/mydrive/llm-local-backend
    source .env.optimized 2>/dev/null || true
    nohup python3 start.py > logs/backend.log 2>&1 &
    sleep 5
fi

if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo "✅ 前端服务已运行"
else
    echo "🎨 启动前端服务..."
    cd /media/cring/mydrive/llm-local-backend/frontend
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    sleep 5
fi

echo ""
echo "🎉 服务启动完成！"
echo ""
echo "📱 访问地址："
echo "   前端页面: http://localhost:3000"
echo "   后端API: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo ""
echo "💡 功能说明："
echo "   - 智能Agent: 与本地大模型对话"
echo "   - 算力管理: 监控GPU和任务"
echo "   - 存储管理: 管理文件和存储"
echo "   - 系统监控: 查看系统状态"
echo "   - 模型服务: 管理多个模型"
echo ""
