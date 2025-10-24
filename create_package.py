#!/usr/bin/env python3
"""
创建大模型本地化部署包
"""

import os
import shutil
import tarfile
import datetime
from pathlib import Path

def create_deployment_package():
    print("📦 创建新的大模型本地化部署包...")
    
    # 检查当前目录
    if not os.path.exists("main.py"):
        print("❌ 请在项目根目录运行此脚本")
        return False
    
    # 删除旧的部署包
    print("🗑️ 删除旧的部署包...")
    old_packages = list(Path("/media/cring/mydrive").glob("llm-local-backend-*.tar.gz"))
    for package in old_packages:
        try:
            package.unlink()
            print(f"   删除: {package.name}")
        except Exception as e:
            print(f"   删除失败: {e}")
    
    # 创建部署包目录
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    package_name = f"llm-local-backend-{timestamp}"
    package_dir = Path("/media/cring/mydrive") / package_name
    
    print(f"📁 创建部署包目录: {package_dir}")
    package_dir.mkdir(exist_ok=True)
    
    # 需要复制的文件和目录
    items_to_copy = [
        # 核心目录
        "api",
        "config", 
        "model_service",
        "utils",
        "frontend",
        
        # 核心文件
        "main.py",
        "start.py",
        "requirements.txt",
        "README.md",
        
        # Docker文件
        "Dockerfile",
        "docker-compose.yml",
        "docker.env",
        "nginx.conf",
        ".dockerignore",
        
        # 启动脚本
        "start_all.sh",
        "stop_all.sh",
        "quick_start.sh",
        "build_docker.sh",
        "restart_backend.sh",
        "test_backend.py",
        
        # 文档
        "DOCKER_DEPLOYMENT.md",
        "PROJECT_STRUCTURE.md",
        "USAGE_GUIDE.md",
        "DEPLOYMENT_SUMMARY.md",
    ]
    
    # 复制文件
    print("📋 复制文件...")
    for item in items_to_copy:
        src = Path(item)
        if src.exists():
            dst = package_dir / item
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
                print(f"   复制目录: {item}")
            else:
                shutil.copy2(src, dst)
                print(f"   复制文件: {item}")
        else:
            print(f"   ⚠️ 文件不存在: {item}")
    
    # 创建必要的目录
    print("📁 创建必要目录...")
    (package_dir / "models").mkdir(exist_ok=True)
    (package_dir / "uploads").mkdir(exist_ok=True)
    (package_dir / "logs").mkdir(exist_ok=True)
    
    # 创建部署说明文件
    deployment_guide = package_dir / "DEPLOYMENT_GUIDE.md"
    with open(deployment_guide, 'w', encoding='utf-8') as f:
        f.write("""# 🚀 大模型本地化部署指南

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
ollama pull llama2:latest
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
- **主页面**: http://localhost:8080 (Docker) 或 http://localhost:3001 (本地)
- **API文档**: http://localhost:8000/docs

## 🎯 功能特性

- 🤖 智能Agent对话（支持多模型切换）
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
./restart_backend.sh                # 重启后端
python3 test_backend.py             # 测试后端
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
""")
    
    # 创建快速安装脚本
    install_script = package_dir / "install.sh"
    with open(install_script, 'w', encoding='utf-8') as f:
        f.write("""#!/bin/bash

echo "🚀 大模型本地化系统安装脚本"

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
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
ollama pull llama2:latest

# 部署应用
echo "🐳 部署应用..."
chmod +x build_docker.sh
./build_docker.sh

echo "✅ 安装完成！"
echo "📱 访问地址: http://localhost:8080"
""")
    
    # 设置安装脚本权限
    os.chmod(install_script, 0o755)
    
    # 创建压缩包
    print("📦 创建压缩包...")
    tar_path = Path("/media/cring/mydrive") / f"{package_name}.tar.gz"
    
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(package_dir, arcname=package_name)
    
    # 清理临时目录
    shutil.rmtree(package_dir)
    
    # 显示结果
    file_size = tar_path.stat().st_size / (1024 * 1024)  # MB
    
    print("")
    print("🎉 新部署包创建完成！")
    print("")
    print(f"📁 部署包位置: {tar_path}")
    print(f"📏 包大小: {file_size:.1f} MB")
    print("")
    print("🚀 使用方法:")
    print(f"   1. 将 {package_name}.tar.gz 复制到目标机器")
    print(f"   2. 解压: tar -xzf {package_name}.tar.gz")
    print(f"   3. 进入目录: cd {package_name}")
    print("   4. 运行安装: ./install.sh")
    print("")
    print("📋 包含内容:")
    print("   ✅ 完整的源代码（包含最新修复）")
    print("   ✅ Docker配置文件")
    print("   ✅ 启动脚本")
    print("   ✅ 部署文档")
    print("   ✅ 安装脚本")
    print("   ✅ 测试脚本")
    print("")
    print("🆕 新功能:")
    print("   ✅ 混合模型管理器（支持Ollama和Transformers模型）")
    print("   ✅ 前端滚动优化")
    print("   ✅ 流式聊天API修复")
    print("   ✅ 多模型切换功能")
    print("")
    print("💡 提示: 部署包已包含所有必要文件，可在任何支持Docker的机器上运行！")
    
    return True

if __name__ == "__main__":
    create_deployment_package()
