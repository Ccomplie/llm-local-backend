#!/bin/bash

echo "📦 创建大模型本地化部署包..."

# 检查当前目录
if [ ! -f "main.py" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

# 创建部署包目录
PACKAGE_NAME="llm-local-backend-$(date +%Y%m%d-%H%M%S)"
PACKAGE_DIR="/media/cring/mydrive/$PACKAGE_NAME"

echo "📁 创建部署包目录: $PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

# 复制核心文件
echo "📋 复制核心文件..."
cp -r api "$PACKAGE_DIR/"
cp -r config "$PACKAGE_DIR/"
cp -r model_service "$PACKAGE_DIR/"
cp -r utils "$PACKAGE_DIR/"
cp -r frontend "$PACKAGE_DIR/"

# 复制配置文件
cp main.py "$PACKAGE_DIR/"
cp start.py "$PACKAGE_DIR/"
cp requirements.txt "$PACKAGE_DIR/"
cp README.md "$PACKAGE_DIR/"

# 复制Docker文件
cp Dockerfile "$PACKAGE_DIR/"
cp docker-compose.yml "$PACKAGE_DIR/"
cp docker.env "$PACKAGE_DIR/"
cp nginx.conf "$PACKAGE_DIR/"
cp .dockerignore "$PACKAGE_DIR/"

# 复制启动脚本
cp start_all.sh "$PACKAGE_DIR/"
cp stop_all.sh "$PACKAGE_DIR/"
cp quick_start.sh "$PACKAGE_DIR/"
cp build_docker.sh "$PACKAGE_DIR/"
cp restart_backend.sh "$PACKAGE_DIR/"
cp test_backend.py "$PACKAGE_DIR/"

# 复制文档
cp DOCKER_DEPLOYMENT.md "$PACKAGE_DIR/"
cp PROJECT_STRUCTURE.md "$PACKAGE_DIR/"
cp CLEANUP_SUMMARY.md "$PACKAGE_DIR/"

# 创建必要的目录
mkdir -p "$PACKAGE_DIR/models"
mkdir -p "$PACKAGE_DIR/uploads"
mkdir -p "$PACKAGE_DIR/logs"

# 创建部署说明文件
cat > "$PACKAGE_DIR/DEPLOYMENT_GUIDE.md" << 'EOF'
# 🚀 大模型本地化部署指南

## 📋 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 8GB 可用内存
- 至少 20GB 可用磁盘空间

## 🚀 快速部署

### 1. 安装Ollama（必需）
```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# 下载并安装 https://ollama.ai/download
```

### 2. 下载模型
```bash
ollama pull qwen2.5:7b
ollama pull deepseek-coder:6.7b
```

### 3. 启动Ollama服务
```bash
ollama serve
```

### 4. 部署应用
```bash
# 方式1: Docker部署（推荐）
chmod +x build_docker.sh
./build_docker.sh

# 方式2: 本地部署
chmod +x start_all.sh
./start_all.sh
```

### 5. 访问服务
- **主页面**: http://localhost:8080 (Docker) 或 http://localhost:3000 (本地)
- **API文档**: http://localhost:8000/docs

## 🎯 功能特性

- 🤖 智能Agent对话
- 📊 算力资源管理
- 💾 存储资源管理
- 🖥️ 系统资源管理
- 🔧 模型服务管理

## 🛠️ 管理命令

```bash
# Docker部署
docker compose ps                    # 查看服务状态
docker compose logs -f              # 查看日志
docker compose down                 # 停止服务

# 本地部署
./stop_all.sh                       # 停止服务
```

## 🔧 配置说明

编辑 `docker.env` 文件修改配置：
- `OLLAMA_HOST`: Ollama服务地址
- `DEFAULT_MODEL`: 默认模型
- `SECRET_KEY`: 安全密钥

## 📞 技术支持

如遇问题，请查看：
1. 日志文件: `logs/backend.log`
2. 服务状态: `docker compose ps`
3. 项目文档: `README.md`

---
**注意**: 首次部署可能需要下载模型文件，请确保网络连接正常。
EOF

# 创建快速安装脚本
cat > "$PACKAGE_DIR/install.sh" << 'EOF'
#!/bin/bash

echo "🚀 大模型本地化系统安装脚本"

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 检查Ollama
if ! command -v ollama &> /dev/null; then
    echo "⚠️ Ollama未安装，正在安装..."
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# 启动Ollama
echo "🔧 启动Ollama服务..."
ollama serve &
sleep 5

# 下载模型
echo "📥 下载模型..."
ollama pull qwen2.5:7b

# 部署应用
echo "🐳 部署应用..."
chmod +x build_docker.sh
./build_docker.sh

echo "✅ 安装完成！"
echo "📱 访问地址: http://localhost:8080"
EOF

chmod +x "$PACKAGE_DIR/install.sh"

# 创建压缩包
echo "📦 创建压缩包..."
cd "/media/cring/mydrive"
tar -czf "$PACKAGE_NAME.tar.gz" "$PACKAGE_NAME"

# 显示结果
echo ""
echo "🎉 部署包创建完成！"
echo ""
echo "📁 部署包位置: /media/cring/mydrive/$PACKAGE_NAME.tar.gz"
echo "📏 包大小: $(du -h /media/cring/mydrive/$PACKAGE_NAME.tar.gz | cut -f1)"
echo ""
echo "🚀 使用方法:"
echo "   1. 将 $PACKAGE_NAME.tar.gz 复制到目标机器"
echo "   2. 解压: tar -xzf $PACKAGE_NAME.tar.gz"
echo "   3. 进入目录: cd $PACKAGE_NAME"
echo "   4. 运行安装: ./install.sh"
echo ""
echo "📋 包含内容:"
echo "   ✅ 完整的源代码"
echo "   ✅ Docker配置文件"
echo "   ✅ 启动脚本"
echo "   ✅ 部署文档"
echo "   ✅ 安装脚本"
echo ""
echo "💡 提示: 部署包已包含所有必要文件，可在任何支持Docker的机器上运行！"
