"""
健康检查API
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import psutil
try:
    import torch
except ImportError:
    torch = None

try:
    from model_service.model_manager import ModelManager
except ImportError:
    from model_service.simple_model_manager import SimpleModelManager as ModelManager

router = APIRouter()

def get_model_manager() -> ModelManager:
    """获取模型管理器依赖"""
    from main import app
    return app.state.model_manager

@router.get("/health", summary="健康检查")
async def health_check():
    """基础健康检查"""
    return {
        "status": "healthy",
        "message": "服务运行正常"
    }

@router.get("/health/detailed", summary="详细健康检查")
async def detailed_health_check(model_manager: ModelManager = Depends(get_model_manager)):
    """详细健康检查"""
    
    # 系统信息
    system_info = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }
    
    # GPU信息
    gpu_info = {}
    if torch and torch.cuda.is_available():
        gpu_info = {
            "available": True,
            "device_count": torch.cuda.device_count(),
            "current_device": torch.cuda.current_device(),
            "device_name": torch.cuda.get_device_name(),
            "memory_allocated": torch.cuda.memory_allocated() / 1024**3,  # GB
            "memory_reserved": torch.cuda.memory_reserved() / 1024**3,   # GB
        }
    else:
        gpu_info = {"available": False}
    
    # 模型信息
    model_info = {
        "available_models": await model_manager.get_available_models(),
        "current_model": await model_manager.get_current_model(),
        "loaded_models": len([m for m in model_manager.models.values() if m.is_loaded])
    }
    
    return {
        "status": "healthy",
        "system": system_info,
        "gpu": gpu_info,
        "models": model_info,
        "timestamp": "2024-01-01T00:00:00Z"  # 实际应该用datetime.now()
    }
