"""
模型管理API
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import shutil
import zipfile
from pathlib import Path
import logging

try:
    from model_service.model_manager import ModelManager
except ImportError:
    from model_service.simple_model_manager import SimpleModelManager as ModelManager
from config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)

class ModelInfo(BaseModel):
    """模型信息模型"""
    name: str
    path: str
    is_loaded: bool
    is_current: bool
    size: Optional[str] = None

class ModelSwitchRequest(BaseModel):
    """模型切换请求"""
    model_name: str

def get_model_manager() -> ModelManager:
    """获取模型管理器依赖"""
    from main import app
    return app.state.model_manager

@router.get("/models", response_model=List[ModelInfo], summary="获取模型列表")
async def get_models(model_manager: ModelManager = Depends(get_model_manager)):
    """获取所有可用模型列表"""
    
    models = []
    available_models = await model_manager.get_available_models()
    for model_name in available_models:
        info = model_manager.get_model_info(model_name)
        
        # 计算模型大小
        model_path = Path(info["path"])
        size = None
        if model_path.exists():
            total_size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
            size = format_size(total_size)
        
        models.append(ModelInfo(
            name=info["name"],
            path=info["path"],
            is_loaded=info["is_loaded"],
            is_current=info["is_current"],
            size=size
        ))
    
    return models

@router.post("/models/switch", summary="切换模型")
async def switch_model(
    request: ModelSwitchRequest,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """切换当前使用的模型"""
    
    available_models = await model_manager.get_available_models()
    if request.model_name not in available_models:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    try:
        success = await model_manager.load_model(request.model_name)
        
        if success:
            return {"message": f"已切换到模型: {request.model_name}"}
        else:
            raise HTTPException(status_code=500, detail="模型加载失败")
            
    except Exception as e:
        logger.error(f"切换模型失败: {e}")
        raise HTTPException(status_code=500, detail=f"切换模型失败: {str(e)}")

@router.post("/models/upload", summary="上传模型")
async def upload_model(
    file: UploadFile = File(...),
    model_manager: ModelManager = Depends(get_model_manager)
):
    """上传模型文件"""
    
    # 检查文件类型
    if not file.filename.endswith(('.zip', '.tar.gz', '.tar')):
        raise HTTPException(status_code=400, detail="只支持zip、tar.gz、tar格式的模型文件")
    
    try:
        # 创建临时目录
        temp_dir = Path(settings.upload_dir) / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存上传的文件
        temp_file = temp_dir / file.filename
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 解压文件
        extract_dir = Path(settings.models_dir) / Path(file.filename).stem
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        if file.filename.endswith('.zip'):
            with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        else:
            import tarfile
            with tarfile.open(temp_file, 'r:*') as tar_ref:
                tar_ref.extractall(extract_dir)
        
        # 清理临时文件
        temp_file.unlink()
        
        # 重新扫描模型
        await model_manager.scan_models()
        
        return {"message": f"模型 {file.filename} 上传成功"}
        
    except Exception as e:
        logger.error(f"上传模型失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.delete("/models/{model_name}", summary="删除模型")
async def delete_model(
    model_name: str,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """删除指定模型"""
    
    available_models = await model_manager.get_available_models()
    if model_name not in available_models:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 如果模型正在使用，先卸载
    current_model = await model_manager.get_current_model()
    if model_name == current_model:
        await model_manager.unload_model(model_name)
    
    try:
        # 删除模型文件
        model_info = model_manager.get_model_info(model_name)
        model_path = Path(model_info["path"])
        
        if model_path.exists():
            shutil.rmtree(model_path)
        
        # 从管理器中移除
        del model_manager.models[model_name]
        
        return {"message": f"模型 {model_name} 删除成功"}
        
    except Exception as e:
        logger.error(f"删除模型失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.get("/models/current", summary="获取当前模型")
async def get_current_model(model_manager: ModelManager = Depends(get_model_manager)):
    """获取当前使用的模型信息"""
    
    current_model = await model_manager.get_current_model()
    if not current_model:
        return {"message": "没有加载的模型"}
    
    info = model_manager.get_model_info(current_model)
    return ModelInfo(
        name=info["name"],
        path=info["path"],
        is_loaded=info["is_loaded"],
        is_current=info["is_current"]
    )

def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f}{size_names[i]}"
