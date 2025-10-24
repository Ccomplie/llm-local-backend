"""
模型服务管理API
管理多个模型服务，支持启动、停止、配置等
"""

import asyncio
import time
import json
import subprocess
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from loguru import logger

router = APIRouter(prefix="/api/v1/model-service", tags=["model-service"])

# 数据模型
class ModelService(BaseModel):
    id: str
    name: str
    type: str        # llm, vision, health, trajectory
    model: str
    version: str
    status: str      # running, stopped, error, starting
    port: int
    gpu: str
    memory: int      # GB
    start_time: str
    requests: int
    avg_response_time: float
    health: str      # healthy, warning, error

class ModelTemplate(BaseModel):
    name: str
    type: str
    description: str
    requirements: str
    default_port: int
    default_memory: int

class ServiceRequest(BaseModel):
    name: str
    model_name: str
    model_type: str
    port: int
    memory: int
    gpu: str
    description: Optional[str] = None

class ServiceConfig(BaseModel):
    port: int
    memory: int
    gpu: str

class ServiceMetrics(BaseModel):
    timestamp: str
    request_count: int
    response_time: float
    memory_usage: float
    cpu_usage: float

# 全局状态
model_services: Dict[str, ModelService] = {}
service_metrics: Dict[str, List[ServiceMetrics]] = {}
service_logs: Dict[str, List[str]] = {}
service_counter = 0

# 模型模板
MODEL_TEMPLATES = [
    ModelTemplate(
        name="Qwen-7B",
        type="llm",
        description="阿里云开源大语言模型，支持中英文对话和代码生成",
        requirements="GPU: 16GB+, Memory: 8GB+",
        default_port=8001,
        default_memory=8
    ),
    ModelTemplate(
        name="DeepSeek-7B",
        type="llm",
        description="深度求索开源大语言模型，擅长数学推理和代码生成",
        requirements="GPU: 16GB+, Memory: 8GB+",
        default_port=8002,
        default_memory=8
    ),
    ModelTemplate(
        name="Qwen2.5-7B",
        type="llm",
        description="Qwen2.5系列模型，通过Ollama提供GPU加速",
        requirements="GPU: 16GB+, Memory: 8GB+",
        default_port=8003,
        default_memory=8
    ),
    ModelTemplate(
        name="ResNet-50",
        type="vision",
        description="图像分类模型，支持1000类物体识别",
        requirements="GPU: 4GB+, Memory: 2GB+",
        default_port=8004,
        default_memory=2
    ),
    ModelTemplate(
        name="YOLO-v8",
        type="vision",
        description="目标检测模型，实时检测图像中的物体",
        requirements="GPU: 6GB+, Memory: 3GB+",
        default_port=8005,
        default_memory=3
    ),
    ModelTemplate(
        name="Health-Predictor",
        type="health",
        description="健康状态预测模型，基于生理指标预测健康风险",
        requirements="GPU: 2GB+, Memory: 1GB+",
        default_port=8006,
        default_memory=1
    ),
    ModelTemplate(
        name="Trajectory-Recognition",
        type="trajectory",
        description="轨迹识别模型，分析移动物体的运动轨迹",
        requirements="GPU: 4GB+, Memory: 2GB+",
        default_port=8007,
        default_memory=2
    )
]

def get_available_ports() -> List[int]:
    """获取可用端口列表"""
    used_ports = {service.port for service in model_services.values()}
    available_ports = []
    
    for port in range(8001, 8100):
        if port not in used_ports:
            available_ports.append(port)
    
    return available_ports

def check_port_available(port: int) -> bool:
    """检查端口是否可用"""
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def get_gpu_list() -> List[str]:
    """获取可用GPU列表"""
    try:
        # 尝试使用nvidia-smi获取GPU信息
        result = subprocess.run(['nvidia-smi', '--list-gpus'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            gpus = []
            for i, line in enumerate(result.stdout.strip().split('\n')):
                if line.strip():
                    gpus.append(f"GPU-{i}")
            return gpus
    except Exception:
        pass
    
    # 返回默认GPU列表
    return ["GPU-0", "GPU-1", "GPU-2"]

@router.get("/templates", response_model=List[ModelTemplate])
async def get_model_templates():
    """获取模型模板列表"""
    try:
        return MODEL_TEMPLATES
    except Exception as e:
        logger.error(f"获取模型模板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/services", response_model=List[ModelService])
async def get_model_services():
    """获取模型服务列表"""
    try:
        return list(model_services.values())
    except Exception as e:
        logger.error(f"获取模型服务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/services/{service_id}", response_model=ModelService)
async def get_service_detail(service_id: str):
    """获取特定服务详情"""
    try:
        if service_id not in model_services:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        return model_services[service_id]
    except Exception as e:
        logger.error(f"获取服务详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/services", response_model=Dict[str, str])
async def create_service(service_request: ServiceRequest, background_tasks: BackgroundTasks):
    """创建新的模型服务"""
    try:
        global service_counter
        service_counter += 1
        
        service_id = f"SERVICE-{service_counter:03d}"
        
        # 检查端口是否可用
        if not check_port_available(service_request.port):
            raise HTTPException(status_code=400, detail=f"端口 {service_request.port} 已被占用")
        
        # 创建服务实例
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        service = ModelService(
            id=service_id,
            name=service_request.name,
            type=service_request.model_type,
            model=service_request.model_name,
            version="v1.0.0",
            status="starting",
            port=service_request.port,
            gpu=service_request.gpu,
            memory=service_request.memory,
            start_time=current_time,
            requests=0,
            avg_response_time=0.0,
            health="healthy"
        )
        
        # 添加到服务列表
        model_services[service_id] = service
        service_metrics[service_id] = []
        service_logs[service_id] = []
        
        # 在后台启动服务
        background_tasks.add_task(start_service_background, service)
        
        logger.info(f"创建模型服务: {service_id}")
        
        return {
            "service_id": service_id,
            "status": "created",
            "message": f"服务 {service_id} 创建成功，正在启动中"
        }
        
    except Exception as e:
        logger.error(f"创建模型服务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def start_service_background(service: ModelService):
    """后台启动服务"""
    try:
        # 模拟服务启动过程
        await asyncio.sleep(2)  # 模拟启动时间
        
        # 更新服务状态
        service.status = "running"
        service_logs[service.id].append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [INFO] 服务启动成功")
        
        logger.info(f"服务 {service.id} 启动成功")
        
        # 开始模拟服务运行
        asyncio.create_task(simulate_service_running(service))
        
    except Exception as e:
        service.status = "error"
        service.health = "error"
        service_logs[service.id].append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [ERROR] 服务启动失败: {e}")
        logger.error(f"服务 {service.id} 启动失败: {e}")

async def simulate_service_running(service: ModelService):
    """模拟服务运行"""
    while service.status == "running":
        try:
            await asyncio.sleep(30)  # 每30秒更新一次
            
            # 模拟请求处理
            if service.status == "running":
                # 随机增加请求数
                service.requests += 1
                
                # 模拟响应时间
                import random
                service.avg_response_time = random.uniform(0.5, 3.0)
                
                # 生成性能指标
                metrics = ServiceMetrics(
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                    request_count=service.requests,
                    response_time=service.avg_response_time,
                    memory_usage=random.uniform(50, 90),
                    cpu_usage=random.uniform(20, 80)
                )
                
                service_metrics[service.id].append(metrics)
                
                # 保持最近100条记录
                if len(service_metrics[service.id]) > 100:
                    service_metrics[service.id] = service_metrics[service.id][-100:]
                
        except Exception as e:
            logger.error(f"模拟服务运行失败: {e}")
            break

@router.post("/services/{service_id}/start")
async def start_service(service_id: str, background_tasks: BackgroundTasks):
    """启动服务"""
    try:
        if service_id not in model_services:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        service = model_services[service_id]
        
        if service.status == "running":
            raise HTTPException(status_code=400, detail="服务已在运行")
        
        service.status = "starting"
        background_tasks.add_task(start_service_background, service)
        
        return {"message": f"服务 {service_id} 启动中"}
        
    except Exception as e:
        logger.error(f"启动服务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/services/{service_id}/stop")
async def stop_service(service_id: str):
    """停止服务"""
    try:
        if service_id not in model_services:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        service = model_services[service_id]
        service.status = "stopped"
        service.health = "error"
        
        service_logs[service.id].append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [INFO] 服务已停止")
        
        logger.info(f"服务 {service_id} 已停止")
        
        return {"message": f"服务 {service_id} 已停止"}
        
    except Exception as e:
        logger.error(f"停止服务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/services/{service_id}/config")
async def update_service_config(service_id: str, config: ServiceConfig):
    """更新服务配置"""
    try:
        if service_id not in model_services:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        service = model_services[service_id]
        
        # 检查端口是否可用（如果端口有变化）
        if config.port != service.port and not check_port_available(config.port):
            raise HTTPException(status_code=400, detail=f"端口 {config.port} 已被占用")
        
        # 更新配置
        service.port = config.port
        service.memory = config.memory
        service.gpu = config.gpu
        
        service_logs[service.id].append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [INFO] 服务配置已更新")
        
        logger.info(f"服务 {service_id} 配置已更新")
        
        return {"message": f"服务 {service_id} 配置已更新"}
        
    except Exception as e:
        logger.error(f"更新服务配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/services/{service_id}")
async def delete_service(service_id: str):
    """删除服务"""
    try:
        if service_id not in model_services:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        service = model_services[service_id]
        
        # 如果服务正在运行，先停止
        if service.status == "running":
            service.status = "stopped"
        
        # 删除服务
        del model_services[service_id]
        if service_id in service_metrics:
            del service_metrics[service_id]
        if service_id in service_logs:
            del service_logs[service_id]
        
        logger.info(f"服务 {service_id} 已删除")
        
        return {"message": f"服务 {service_id} 已删除"}
        
    except Exception as e:
        logger.error(f"删除服务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/services/{service_id}/metrics", response_model=List[ServiceMetrics])
async def get_service_metrics(service_id: str, limit: int = 100):
    """获取服务性能指标"""
    try:
        if service_id not in model_services:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        metrics = service_metrics.get(service_id, [])
        return metrics[-limit:] if limit > 0 else metrics
        
    except Exception as e:
        logger.error(f"获取服务指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/services/{service_id}/logs")
async def get_service_logs(service_id: str, limit: int = 100):
    """获取服务日志"""
    try:
        if service_id not in model_services:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        logs = service_logs.get(service_id, [])
        return logs[-limit:] if limit > 0 else logs
        
    except Exception as e:
        logger.error(f"获取服务日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/services/{service_id}/test")
async def test_service_api(service_id: str, test_data: Dict[str, Any]):
    """测试服务API"""
    try:
        if service_id not in model_services:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        service = model_services[service_id]
        
        if service.status != "running":
            raise HTTPException(status_code=400, detail="服务未运行")
        
        # 模拟API测试
        import random
        response_time = random.uniform(0.5, 2.0)
        
        # 更新服务统计
        service.requests += 1
        service.avg_response_time = (service.avg_response_time + response_time) / 2
        
        service_logs[service.id].append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [INFO] API测试请求")
        
        return {
            "success": True,
            "response_time": response_time,
            "message": f"API测试成功，响应时间: {response_time:.2f}s"
        }
        
    except Exception as e:
        logger.error(f"测试服务API失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_service_stats():
    """获取服务统计信息"""
    try:
        total_services = len(model_services)
        running_services = len([s for s in model_services.values() if s.status == "running"])
        healthy_services = len([s for s in model_services.values() if s.health == "healthy"])
        
        total_requests = sum(s.requests for s in model_services.values())
        avg_response_time = sum(s.avg_response_time for s in model_services.values()) / total_services if total_services > 0 else 0
        
        return {
            "service_stats": {
                "total_services": total_services,
                "running_services": running_services,
                "healthy_services": healthy_services,
                "health_rate": (healthy_services / total_services * 100) if total_services > 0 else 0
            },
            "performance_stats": {
                "total_requests": total_requests,
                "avg_response_time": round(avg_response_time, 2)
            },
            "available_ports": get_available_ports()[:10],  # 返回前10个可用端口
            "available_gpus": get_gpu_list()
        }
        
    except Exception as e:
        logger.error(f"获取服务统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def get_services_health():
    """获取所有服务健康状态"""
    try:
        health_status = {}
        
        for service_id, service in model_services.items():
            health_status[service_id] = {
                "status": service.status,
                "health": service.health,
                "uptime": time.time() - time.mktime(time.strptime(service.start_time, "%Y-%m-%d %H:%M:%S")),
                "requests": service.requests,
                "avg_response_time": service.avg_response_time
            }
        
        return health_status
        
    except Exception as e:
        logger.error(f"获取服务健康状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
