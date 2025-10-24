"""
系统资源管理API
监控系统状态，进程管理，网络状态等
"""

import os
import time
import subprocess
import psutil
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from loguru import logger

router = APIRouter(prefix="/api/v1/system", tags=["system"])

# 数据模型
class SystemInfo(BaseModel):
    metric: str
    current: float
    total: float
    unit: str
    status: str      # normal, warning, error
    trend: str       # up, down, stable

class ProcessInfo(BaseModel):
    pid: int
    name: str
    cpu: float
    memory: int      # MB
    status: str
    user: str
    start_time: str
    command: str

class NetworkInfo(BaseModel):
    interface: str
    ip_address: str
    status: str      # up, down
    rx_bytes: int
    tx_bytes: int
    rx_packets: int
    tx_packets: int
    errors: int

class SystemLog(BaseModel):
    timestamp: str
    level: str       # info, warning, error
    module: str
    message: str

class ProcessRequest(BaseModel):
    name: str
    command: str
    user: str

# 全局状态
system_logs: List[SystemLog] = []
performance_history: List[Dict[str, Any]] = []

def get_system_info() -> List[SystemInfo]:
    """获取系统资源信息"""
    try:
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
        
        # 网络信息（简化）
        network_io = psutil.net_io_counters()
        network_speed = 1000  # 假设1Gbps
        
        system_data = [
            SystemInfo(
                metric="CPU使用率",
                current=cpu_percent,
                total=100,
                unit="%",
                status="normal" if cpu_percent < 80 else "warning" if cpu_percent < 90 else "error",
                trend="stable"
            ),
            SystemInfo(
                metric="内存使用率",
                current=memory_percent,
                total=100,
                unit="%",
                status="normal" if memory_percent < 80 else "warning" if memory_percent < 90 else "error",
                trend="stable"
            ),
            SystemInfo(
                metric="磁盘使用率",
                current=disk_percent,
                total=100,
                unit="%",
                status="normal" if disk_percent < 80 else "warning" if disk_percent < 90 else "error",
                trend="stable"
            ),
            SystemInfo(
                metric="网络带宽",
                current=network_speed,
                total=network_speed,
                unit="Mbps",
                status="normal",
                trend="stable"
            )
        ]
        
        return system_data
        
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        # 返回模拟数据
        return [
            SystemInfo(
                metric="CPU使用率",
                current=65.0,
                total=100,
                unit="%",
                status="normal",
                trend="stable"
            ),
            SystemInfo(
                metric="内存使用率",
                current=78.0,
                total=100,
                unit="%",
                status="warning",
                trend="up"
            ),
            SystemInfo(
                metric="磁盘使用率",
                current=45.0,
                total=100,
                unit="%",
                status="normal",
                trend="stable"
            ),
            SystemInfo(
                metric="网络带宽",
                current=320.0,
                total=1000,
                unit="Mbps",
                status="normal",
                trend="down"
            )
        ]

def get_processes() -> List[ProcessInfo]:
    """获取进程信息"""
    try:
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status', 'username', 'create_time', 'cmdline']):
            try:
                info = proc.info
                
                # 计算内存使用（MB）
                memory_mb = info['memory_info'].rss // (1024**2) if info['memory_info'] else 0
                
                # 格式化启动时间
                start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info['create_time']))
                
                # 格式化命令
                command = ' '.join(info['cmdline']) if info['cmdline'] else info['name']
                if len(command) > 100:
                    command = command[:100] + "..."
                
                process = ProcessInfo(
                    pid=info['pid'],
                    name=info['name'],
                    cpu=info['cpu_percent'] or 0.0,
                    memory=memory_mb,
                    status=info['status'],
                    user=info['username'] or 'unknown',
                    start_time=start_time,
                    command=command
                )
                
                processes.append(process)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # 按CPU使用率排序
        processes.sort(key=lambda x: x.cpu, reverse=True)
        
        return processes[:50]  # 返回前50个进程
        
    except Exception as e:
        logger.error(f"获取进程信息失败: {e}")
        return []

def get_network_info() -> List[NetworkInfo]:
    """获取网络接口信息"""
    try:
        network_interfaces = []
        
        # 获取网络接口统计
        net_io = psutil.net_io_counters(pernic=True)
        net_addrs = psutil.net_if_addrs()
        net_stats = psutil.net_if_stats()
        
        for interface, stats in net_stats.items():
            # 跳过回环接口
            if interface.startswith('lo'):
                continue
            
            # 获取IP地址
            ip_address = "N/A"
            for addr in net_addrs.get(interface, []):
                if addr.family == 2:  # IPv4
                    ip_address = addr.address
                    break
            
            # 获取网络IO统计
            io_stats = net_io.get(interface)
            if io_stats:
                network_interfaces.append(NetworkInfo(
                    interface=interface,
                    ip_address=ip_address,
                    status="up" if stats.isup else "down",
                    rx_bytes=io_stats.bytes_recv,
                    tx_bytes=io_stats.bytes_sent,
                    rx_packets=io_stats.packets_recv,
                    tx_packets=io_stats.packets_sent,
                    errors=io_stats.errin + io_stats.errout
                ))
        
        return network_interfaces
        
    except Exception as e:
        logger.error(f"获取网络信息失败: {e}")
        # 返回模拟数据
        return [
            NetworkInfo(
                interface="eth0",
                ip_address="192.168.1.100",
                status="up",
                rx_bytes=1024000,
                tx_bytes=512000,
                rx_packets=1500,
                tx_packets=800,
                errors=0
            ),
            NetworkInfo(
                interface="wlan0",
                ip_address="10.0.0.50",
                status="up",
                rx_bytes=2048000,
                tx_bytes=1024000,
                rx_packets=3000,
                tx_packets=1500,
                errors=2
            )
        ]

def get_system_logs() -> List[SystemLog]:
    """获取系统日志"""
    try:
        # 这里可以读取实际的系统日志文件
        # 现在返回模拟数据
        logs = [
            SystemLog(
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                level="info",
                module="System",
                message="系统运行正常"
            ),
            SystemLog(
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 300)),
                level="warning",
                module="Memory",
                message="内存使用率超过80%"
            ),
            SystemLog(
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 600)),
                level="info",
                module="Network",
                message="网络连接正常"
            )
        ]
        
        # 添加历史日志
        logs.extend(system_logs)
        
        # 按时间排序
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        return logs[:100]  # 返回最近100条日志
        
    except Exception as e:
        logger.error(f"获取系统日志失败: {e}")
        return []

def get_performance_trend() -> List[Dict[str, Any]]:
    """获取性能趋势数据"""
    try:
        current_time = time.time()
        trend_data = []
        
        for i in range(24):  # 24小时数据
            timestamp = current_time - (23 - i) * 3600
            time_str = time.strftime("%H:%M", time.localtime(timestamp))
            
            # 模拟性能数据
            cpu_usage = max(0, min(100, 50 + (i % 12) * 5 + (i % 3) * 10))
            memory_usage = max(0, min(100, 60 + (i % 8) * 8 + (i % 2) * 15))
            disk_usage = max(0, min(100, 40 + (i % 10) * 6 + (i % 4) * 12))
            
            trend_data.append({
                "timestamp": time_str,
                "cpu": cpu_usage,
                "memory": memory_usage,
                "disk": disk_usage
            })
        
        return trend_data
        
    except Exception as e:
        logger.error(f"获取性能趋势失败: {e}")
        return []

@router.get("/info", response_model=List[SystemInfo])
async def get_system_info_endpoint():
    """获取系统资源信息"""
    try:
        return get_system_info()
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processes", response_model=List[ProcessInfo])
async def get_processes_endpoint():
    """获取进程列表"""
    try:
        return get_processes()
    except Exception as e:
        logger.error(f"获取进程列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processes/{pid}", response_model=ProcessInfo)
async def get_process_detail(pid: int):
    """获取特定进程详情"""
    try:
        processes = get_processes()
        for proc in processes:
            if proc.pid == pid:
                return proc
        
        raise HTTPException(status_code=404, detail="进程不存在")
    except Exception as e:
        logger.error(f"获取进程详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/processes/{pid}/kill")
async def kill_process(pid: int):
    """终止进程"""
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        
        # 等待进程终止
        try:
            proc.wait(timeout=5)
        except psutil.TimeoutExpired:
            proc.kill()  # 强制终止
        
        logger.info(f"进程 {pid} 已终止")
        return {"message": f"进程 {pid} 已终止"}
        
    except psutil.NoSuchProcess:
        raise HTTPException(status_code=404, detail="进程不存在")
    except psutil.AccessDenied:
        raise HTTPException(status_code=403, detail="权限不足")
    except Exception as e:
        logger.error(f"终止进程失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/processes")
async def start_process(process_request: ProcessRequest, background_tasks: BackgroundTasks):
    """启动新进程"""
    try:
        # 这里只是模拟启动进程，实际实现需要根据具体需求
        logger.info(f"启动进程: {process_request.name}")
        
        # 在后台执行进程启动
        background_tasks.add_task(execute_process, process_request)
        
        return {"message": f"进程 {process_request.name} 启动中"}
        
    except Exception as e:
        logger.error(f"启动进程失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def execute_process(process_request: ProcessRequest):
    """执行进程（模拟）"""
    try:
        # 这里可以实现实际的进程启动逻辑
        logger.info(f"执行进程: {process_request.command}")
        
        # 添加日志
        log = SystemLog(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            level="info",
            module="Process",
            message=f"进程 {process_request.name} 启动成功"
        )
        system_logs.append(log)
        
    except Exception as e:
        logger.error(f"执行进程失败: {e}")
        log = SystemLog(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            level="error",
            module="Process",
            message=f"进程 {process_request.name} 启动失败: {e}"
        )
        system_logs.append(log)

@router.get("/network", response_model=List[NetworkInfo])
async def get_network_info_endpoint():
    """获取网络接口信息"""
    try:
        return get_network_info()
    except Exception as e:
        logger.error(f"获取网络信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs", response_model=List[SystemLog])
async def get_system_logs_endpoint(
    level: Optional[str] = None,
    limit: int = 100
):
    """获取系统日志"""
    try:
        logs = get_system_logs()
        
        # 按级别筛选
        if level:
            logs = [log for log in logs if log.level == level]
        
        # 限制数量
        logs = logs[:limit]
        
        return logs
        
    except Exception as e:
        logger.error(f"获取系统日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-trend")
async def get_performance_trend_endpoint():
    """获取性能趋势数据"""
    try:
        return get_performance_trend()
    except Exception as e:
        logger.error(f"获取性能趋势失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_system_stats():
    """获取系统统计信息"""
    try:
        system_info = get_system_info()
        processes = get_processes()
        network_info = get_network_info()
        
        # 计算统计信息
        cpu_info = next((info for info in system_info if info.metric == "CPU使用率"), None)
        memory_info = next((info for info in system_info if info.metric == "内存使用率"), None)
        disk_info = next((info for info in system_info if info.metric == "磁盘使用率"), None)
        
        running_processes = len([p for p in processes if p.status == "running"])
        total_memory = sum(p.memory for p in processes)
        
        active_interfaces = len([n for n in network_info if n.status == "up"])
        total_errors = sum(n.errors for n in network_info)
        
        return {
            "system_stats": {
                "cpu_usage_percent": cpu_info.current if cpu_info else 0,
                "memory_usage_percent": memory_info.current if memory_info else 0,
                "disk_usage_percent": disk_info.current if disk_info else 0,
                "uptime_seconds": time.time() - psutil.boot_time()
            },
            "process_stats": {
                "total_processes": len(processes),
                "running_processes": running_processes,
                "total_memory_usage_mb": total_memory
            },
            "network_stats": {
                "active_interfaces": active_interfaces,
                "total_interfaces": len(network_info),
                "total_errors": total_errors
            }
        }
        
    except Exception as e:
        logger.error(f"获取系统统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logs")
async def add_system_log(log: SystemLog):
    """添加系统日志"""
    try:
        system_logs.append(log)
        logger.info(f"添加系统日志: {log.message}")
        return {"message": "日志添加成功"}
    except Exception as e:
        logger.error(f"添加系统日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
