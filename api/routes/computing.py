"""
算力资源管理API
监控和管理GPU资源，任务分配等
"""

import asyncio
import subprocess
import json
import time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from loguru import logger

router = APIRouter(prefix="/api/v1/computing", tags=["computing"])

# 数据模型
class GPUInfo(BaseModel):
    id: str
    name: str
    memory_total: int  # GB
    memory_used: int   # GB
    utilization: int   # 百分比
    temperature: int   # 摄氏度
    status: str        # idle, running, error
    current_task: Optional[str] = None

class TaskInfo(BaseModel):
    id: str
    name: str
    gpu_id: str
    status: str        # pending, running, completed, failed
    progress: int      # 百分比
    start_time: str
    estimated_time: str

class TaskRequest(BaseModel):
    name: str
    gpu_id: str
    task_type: str     # training, inference, finetune
    priority: str      # high, medium, low

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

# 全局状态存储
gpu_status: Dict[str, GPUInfo] = {}
task_queue: List[TaskInfo] = []
task_counter = 0

def get_gpu_info() -> List[GPUInfo]:
    """获取GPU信息"""
    try:
        # 使用nvidia-smi获取GPU信息
        result = subprocess.run([
            'nvidia-smi', 
            '--query-gpu=index,name,memory.total,memory.used,utilization.gpu,temperature.gpu',
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            # 如果nvidia-smi不可用，返回模拟数据
            return get_mock_gpu_info()
        
        gpus = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 6:
                    gpu_id = f"GPU-{parts[0]}"
                    name = parts[1]
                    memory_total = int(parts[2]) // 1024  # 转换为GB
                    memory_used = int(parts[3]) // 1024   # 转换为GB
                    utilization = int(parts[4])
                    temperature = int(parts[5])
                    
                    # 确定状态
                    status = "idle"
                    current_task = None
                    if utilization > 10:
                        status = "running"
                        current_task = "模型推理"
                    
                    gpu_info = GPUInfo(
                        id=gpu_id,
                        name=name,
                        memory_total=memory_total,
                        memory_used=memory_used,
                        utilization=utilization,
                        temperature=temperature,
                        status=status,
                        current_task=current_task
                    )
                    gpus.append(gpu_info)
        
        return gpus
        
    except Exception as e:
        logger.error(f"获取GPU信息失败: {e}")
        return get_mock_gpu_info()

def get_mock_gpu_info() -> List[GPUInfo]:
    """返回模拟GPU信息（当nvidia-smi不可用时）"""
    return [
        GPUInfo(
            id="GPU-0",
            name="NVIDIA Jetson AGX Orin",
            memory_total=32,
            memory_used=8,
            utilization=25,
            temperature=45,
            status="running",
            current_task="Ollama模型推理"
        ),
        GPUInfo(
            id="GPU-1", 
            name="NVIDIA Jetson AGX Orin (Secondary)",
            memory_total=32,
            memory_used=0,
            utilization=0,
            temperature=40,
            status="idle"
        )
    ]

def get_system_info() -> Dict[str, Any]:
    """获取系统信息"""
    try:
        import psutil
        
        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 内存信息
        memory = psutil.virtual_memory()
        memory_total = memory.total // (1024**3)  # GB
        memory_used = memory.used // (1024**3)    # GB
        memory_percent = memory.percent
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        disk_total = disk.total // (1024**3)      # GB
        disk_used = disk.used // (1024**3)        # GB
        disk_percent = (disk.used / disk.total) * 100
        
        return {
            "cpu": {
                "usage_percent": cpu_percent,
                "core_count": cpu_count
            },
            "memory": {
                "total_gb": memory_total,
                "used_gb": memory_used,
                "usage_percent": memory_percent
            },
            "disk": {
                "total_gb": disk_total,
                "used_gb": disk_used,
                "usage_percent": disk_percent
            }
        }
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return {
            "cpu": {"usage_percent": 0, "core_count": 8},
            "memory": {"total_gb": 32, "used_gb": 16, "usage_percent": 50},
            "disk": {"total_gb": 500, "used_gb": 250, "usage_percent": 50}
        }

@router.get("/gpus", response_model=List[GPUInfo])
async def get_gpus():
    """获取GPU列表"""
    try:
        gpus = get_gpu_info()
        return gpus
    except Exception as e:
        logger.error(f"获取GPU列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gpus/{gpu_id}", response_model=GPUInfo)
async def get_gpu_detail(gpu_id: str):
    """获取特定GPU详情"""
    try:
        gpus = get_gpu_info()
        for gpu in gpus:
            if gpu.id == gpu_id:
                return gpu
        
        raise HTTPException(status_code=404, detail="GPU not found")
    except Exception as e:
        logger.error(f"获取GPU详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks", response_model=List[TaskInfo])
async def get_tasks():
    """获取任务列表"""
    try:
        return task_queue
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks", response_model=TaskResponse)
async def create_task(task_request: TaskRequest, background_tasks: BackgroundTasks):
    """创建新任务"""
    try:
        global task_counter
        task_counter += 1
        
        task_id = f"TASK-{task_counter:03d}"
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 估算完成时间（简单估算）
        estimated_hours = 2 if task_request.task_type == "training" else 0.5
        estimated_time = time.strftime("%Y-%m-%d %H:%M:%S", 
                                     time.localtime(time.time() + estimated_hours * 3600))
        
        task = TaskInfo(
            id=task_id,
            name=task_request.name,
            gpu_id=task_request.gpu_id,
            status="pending",
            progress=0,
            start_time=current_time,
            estimated_time=estimated_time
        )
        
        task_queue.append(task)
        
        # 在后台启动任务
        background_tasks.add_task(execute_task, task)
        
        return TaskResponse(
            task_id=task_id,
            status="created",
            message=f"任务 {task_id} 已创建并加入队列"
        )
        
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def execute_task(task: TaskInfo):
    """执行任务（模拟）"""
    try:
        # 更新任务状态为运行中
        task.status = "running"
        logger.info(f"开始执行任务: {task.id}")
        
        # 模拟任务执行过程
        for progress in range(0, 101, 10):
            await asyncio.sleep(2)  # 模拟执行时间
            task.progress = progress
            
            if progress == 100:
                task.status = "completed"
                logger.info(f"任务完成: {task.id}")
            else:
                logger.info(f"任务进度: {task.id} - {progress}%")
                
    except Exception as e:
        task.status = "failed"
        logger.error(f"任务执行失败: {task.id} - {e}")

@router.post("/tasks/{task_id}/pause")
async def pause_task(task_id: str):
    """暂停任务"""
    try:
        for task in task_queue:
            if task.id == task_id:
                if task.status == "running":
                    task.status = "paused"
                    return {"message": f"任务 {task_id} 已暂停"}
                else:
                    raise HTTPException(status_code=400, detail="任务不在运行状态")
        
        raise HTTPException(status_code=404, detail="任务不存在")
    except Exception as e:
        logger.error(f"暂停任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks/{task_id}/stop")
async def stop_task(task_id: str):
    """停止任务"""
    try:
        for task in task_queue:
            if task.id == task_id:
                task.status = "stopped"
                return {"message": f"任务 {task_id} 已停止"}
        
        raise HTTPException(status_code=404, detail="任务不存在")
    except Exception as e:
        logger.error(f"停止任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
async def get_performance_data():
    """获取性能数据"""
    try:
        # 生成模拟性能数据
        current_time = time.time()
        performance_data = []
        
        for i in range(24):  # 24小时数据
            timestamp = current_time - (23 - i) * 3600
            time_str = time.strftime("%H:%M", time.localtime(timestamp))
            
            # 模拟GPU利用率数据
            gpu1_util = max(0, min(100, 50 + (i % 12) * 5 + (i % 3) * 10))
            gpu2_util = max(0, min(100, 30 + (i % 8) * 8 + (i % 2) * 15))
            gpu3_util = max(0, min(100, 40 + (i % 10) * 6 + (i % 4) * 12))
            
            performance_data.append({
                "time": time_str,
                "gpu1": gpu1_util,
                "gpu2": gpu2_util,
                "gpu3": gpu3_util
            })
        
        return performance_data
        
    except Exception as e:
        logger.error(f"获取性能数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_computing_stats():
    """获取算力统计信息"""
    try:
        gpus = get_gpu_info()
        system_info = get_system_info()
        
        total_gpus = len(gpus)
        running_gpus = len([gpu for gpu in gpus if gpu.status == "running"])
        total_memory = sum(gpu.memory_total for gpu in gpus)
        used_memory = sum(gpu.memory_used for gpu in gpus)
        avg_utilization = sum(gpu.utilization for gpu in gpus) // total_gpus if total_gpus > 0 else 0
        
        return {
            "gpu_stats": {
                "total_gpus": total_gpus,
                "running_gpus": running_gpus,
                "total_memory_gb": total_memory,
                "used_memory_gb": used_memory,
                "memory_usage_percent": (used_memory / total_memory * 100) if total_memory > 0 else 0,
                "avg_utilization_percent": avg_utilization
            },
            "system_stats": system_info,
            "task_stats": {
                "total_tasks": len(task_queue),
                "running_tasks": len([t for t in task_queue if t.status == "running"]),
                "pending_tasks": len([t for t in task_queue if t.status == "pending"]),
                "completed_tasks": len([t for t in task_queue if t.status == "completed"])
            }
        }
        
    except Exception as e:
        logger.error(f"获取算力统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
