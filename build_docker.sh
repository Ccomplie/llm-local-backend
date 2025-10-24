#!/bin/bash

echo "🐳 开始构建大模型本地化Docker镜像..."

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker服务"
    exit 1
fi

# 检查当前目录
if [ ! -f "main.py" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

echo "✅ 环境检查通过"

# 停止并移除旧容器
echo "🛑 停止并移除旧的Docker容器..."
docker-compose down --remove-orphans 2>/dev/null || docker compose down --remove-orphans 2>/dev/null || true

# 构建镜像
echo "🏗️ 正在构建Docker镜像..."
if ! docker-compose build --no-cache 2>/dev/null && ! docker compose build --no-cache; then
    echo "❌ Docker镜像构建失败！"
    exit 1
fi

echo "✅ Docker镜像构建成功！"

# 启动服务
echo "🚀 正在启动Docker服务..."
if ! docker-compose up -d 2>/dev/null && ! docker compose up -d; then
    echo "❌ Docker服务启动失败！"
    exit 1
fi

echo "✅ Docker服务启动成功！"

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
if curl -s http://localhost:8080/health >/dev/null 2>&1; then
    echo "✅ 服务健康检查通过"
else
    echo "⚠️ 服务可能还在启动中，请稍等..."
fi

echo ""
echo "🎉 大模型本地化Docker部署完成！"
echo ""
echo "📱 访问地址："
echo "   主页面: http://localhost:8080"
echo "   前端页面: http://localhost:80"
echo "   后端API: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo ""
echo "🔧 管理命令："
echo "   查看服务状态: docker-compose ps 或 docker compose ps"
echo "   查看服务日志: docker-compose logs -f 或 docker compose logs -f"
echo "   停止所有服务: docker-compose down 或 docker compose down"
echo "   重启所有服务: docker-compose restart 或 docker compose restart"
echo ""
echo "💡 注意事项："
echo "   - 确保Ollama服务在宿主机上运行"
echo "   - 模型文件将保存在 ./models 目录"
echo "   - 上传文件将保存在 ./uploads 目录"
echo "   - 日志文件将保存在 ./logs 目录"
echo ""
