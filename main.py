"""
大模型本地化后端服务主入口
支持多种模型格式和实时对话
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from config.settings import Settings
from api.routes import chat, model_management, training, health, computing, storage, system, model_service, auth
# 使用混合模型管理器（支持Ollama和Transformers模型）
try:
    from model_service.hybrid_model_manager import HybridModelManager as ModelManager
    print("使用混合模型管理器（支持Ollama和Transformers模型）")
except ImportError:
    # 如果混合管理器不可用，回退到Ollama管理器
    try:
        from model_service.ollama_manager import OllamaManager as ModelManager
        print("使用Ollama模型管理器（GPU加速）")
    except ImportError:
        # 如果Ollama不可用，回退到原始模型管理器
        try:
            from model_service.model_manager import ModelManager
            print("使用原始模型管理器")
        except ImportError:
            # 如果导入失败，回退到简化版本
            from model_service.simple_model_manager import SimpleModelManager as ModelManager
            print("使用简化模型管理器")
from utils.logger import setup_logger
from utils.database import init_database

# 配置日志
setup_logger()
logger = logging.getLogger(__name__)

# 全局模型管理器
model_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global model_manager
    
    # 启动时初始化
    logger.info("正在启动大模型后端服务...")
    
    # 初始化数据库
    await init_database()
    
    # 初始化模型管理器
    settings = Settings()
    model_manager = ModelManager(settings)
    await model_manager.initialize()
    app.state.model_manager = model_manager
    
    logger.info("后端服务启动完成")
    
    yield
    
    # 关闭时清理
    logger.info("正在关闭后端服务...")
    if model_manager:
        await model_manager.cleanup()
    logger.info("后端服务已关闭")

# 创建FastAPI应用
app = FastAPI(
    title="大模型本地化后端",
    description="支持多种模型格式的本地化大模型服务",
    version="1.0.0",
    lifespan=lifespan
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 注册路由
app.include_router(health.router, prefix="/api/v1", tags=["健康检查"])
app.include_router(chat.router, prefix="/api/v1", tags=["聊天对话"])
app.include_router(model_management.router, prefix="/api/v1", tags=["模型管理"])
app.include_router(training.router, prefix="/api/v1", tags=["模型训练"])
app.include_router(computing.router, tags=["算力资源管理"])
app.include_router(storage.router, tags=["存储资源管理"])
app.include_router(system.router, tags=["系统资源管理"])
app.include_router(model_service.router, tags=["模型服务管理"])
app.include_router(auth.router, prefix="/api/v1", tags=["用户认证"])

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误", "error": str(exc)}
    )

# 根路径
@app.get("/")
async def root():
    """根路径信息"""
    return {
        "message": "大模型本地化后端服务",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    
    settings = Settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
