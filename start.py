#!/usr/bin/env python3
"""
启动脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        sys.exit(1)

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import fastapi
        import uvicorn
        print("✓ 核心依赖已安装")
        
        # 可选依赖检查
        try:
            import torch
            print("✓ PyTorch已安装")
        except ImportError:
            print("⚠️  PyTorch未安装，将使用简化模式")
            
        try:
            import transformers
            print("✓ Transformers已安装")
        except ImportError:
            print("⚠️  Transformers未安装，将使用简化模式")
            
    except ImportError as e:
        print(f"✗ 缺少核心依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)

def create_directories():
    """创建必要的目录"""
    directories = [
        "models",
        "uploads",
        "uploads/datasets",
        "uploads/temp",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ 创建目录: {directory}")

def main():
    """主函数"""
    print("🚀 启动大模型本地化后端服务...")
    
    # 检查Python版本
    check_python_version()
    print("✓ Python版本检查通过")
    
    # 检查依赖
    check_dependencies()
    
    # 创建目录
    create_directories()
    
    # 检查环境文件
    if not Path(".env").exists():
        print("⚠️  未找到.env文件，使用默认配置")
        print("💡 提示: 复制.env.example到.env并修改配置")
    
    # 启动服务
    print("🎯 启动FastAPI服务...")
    try:
        import uvicorn
        from config.settings import settings
        
        uvicorn.run(
            "main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
