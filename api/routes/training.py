"""
模型训练API
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import asyncio
import shutil
from pathlib import Path
import logging

try:
    from model_service.model_manager import ModelManager
except ImportError:
    from model_service.simple_model_manager import SimpleModelManager as ModelManager
from config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)

class TrainingConfig(BaseModel):
    """训练配置模型"""
    model_name: str
    dataset_path: str
    learning_rate: float = 5e-5
    batch_size: int = 4
    num_epochs: int = 3
    max_length: int = 512
    warmup_steps: int = 100
    save_steps: int = 500
    eval_steps: int = 500

class TrainingStatus(BaseModel):
    """训练状态模型"""
    task_id: str
    status: str  # pending, running, completed, failed
    progress: float
    current_epoch: int
    total_epochs: int
    loss: Optional[float] = None
    message: str

def get_model_manager() -> ModelManager:
    """获取模型管理器依赖"""
    from main import app
    return app.state.model_manager

# 存储训练任务状态
training_tasks: Dict[str, TrainingStatus] = {}

@router.post("/training/start", summary="开始训练")
async def start_training(
    config: TrainingConfig,
    background_tasks: BackgroundTasks,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """开始模型训练"""
    
    # 生成任务ID
    import uuid
    task_id = str(uuid.uuid4())
    
    # 检查数据集是否存在
    dataset_path = Path(config.dataset_path)
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail="数据集文件不存在")
    
    # 创建训练任务状态
    training_tasks[task_id] = TrainingStatus(
        task_id=task_id,
        status="pending",
        progress=0.0,
        current_epoch=0,
        total_epochs=config.num_epochs,
        message="训练任务已创建"
    )
    
    # 启动后台训练任务
    background_tasks.add_task(
        run_training,
        task_id,
        config,
        model_manager
    )
    
    return {"task_id": task_id, "message": "训练任务已启动"}

@router.get("/training/status/{task_id}", response_model=TrainingStatus, summary="获取训练状态")
async def get_training_status(task_id: str):
    """获取训练任务状态"""
    
    if task_id not in training_tasks:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    return training_tasks[task_id]

@router.get("/training/tasks", response_model=List[TrainingStatus], summary="获取所有训练任务")
async def get_all_training_tasks():
    """获取所有训练任务状态"""
    
    return list(training_tasks.values())

@router.post("/training/upload-dataset", summary="上传训练数据集")
async def upload_dataset(file: UploadFile = File(...)):
    """上传训练数据集"""
    
    # 检查文件类型
    if not file.filename.endswith(('.json', '.jsonl', '.txt', '.csv')):
        raise HTTPException(status_code=400, detail="只支持json、jsonl、txt、csv格式的数据集文件")
    
    try:
        # 保存数据集文件
        dataset_dir = Path(settings.upload_dir) / "datasets"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = dataset_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "message": "数据集上传成功",
            "path": str(file_path),
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"上传数据集失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.post("/training/cancel/{task_id}", summary="取消训练")
async def cancel_training(task_id: str):
    """取消训练任务"""
    
    if task_id not in training_tasks:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    training_tasks[task_id].status = "cancelled"
    training_tasks[task_id].message = "训练任务已取消"
    
    return {"message": f"训练任务 {task_id} 已取消"}

async def run_training(task_id: str, config: TrainingConfig, model_manager: ModelManager):
    """运行训练任务"""
    
    try:
        # 更新状态为运行中
        training_tasks[task_id].status = "running"
        training_tasks[task_id].message = "训练进行中..."
        
        # 这里应该实现实际的训练逻辑
        # 由于训练是一个复杂的过程，这里提供一个框架
        
        for epoch in range(config.num_epochs):
            training_tasks[task_id].current_epoch = epoch + 1
            training_tasks[task_id].progress = (epoch + 1) / config.num_epochs * 100
            
            # 模拟训练步骤
            for step in range(100):  # 假设每个epoch有100步
                # 这里应该执行实际的训练步骤
                await asyncio.sleep(0.1)  # 模拟训练时间
                
                # 模拟损失值
                loss = 2.0 - (epoch * 0.5 + step * 0.01)
                training_tasks[task_id].loss = max(loss, 0.1)
                
                # 检查是否被取消
                if training_tasks[task_id].status == "cancelled":
                    return
        
        # 训练完成
        training_tasks[task_id].status = "completed"
        training_tasks[task_id].progress = 100.0
        training_tasks[task_id].message = "训练完成"
        
        # 重新扫描模型以包含新训练的模型
        await model_manager.scan_models()
        
    except Exception as e:
        logger.error(f"训练失败: {e}")
        training_tasks[task_id].status = "failed"
        training_tasks[task_id].message = f"训练失败: {str(e)}"
