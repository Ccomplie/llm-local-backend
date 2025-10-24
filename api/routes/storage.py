"""
存储资源管理API
监控和管理存储设备，文件管理等
"""

import os
import shutil
import time
import mimetypes
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from loguru import logger

router = APIRouter(prefix="/api/v1/storage", tags=["storage"])

# 数据模型
class StorageInfo(BaseModel):
    id: str
    name: str
    type: str        # ssd, hdd, nvme
    total_space: int # GB
    used_space: int  # GB
    status: str      # normal, warning, error
    mount_point: str

class FileInfo(BaseModel):
    name: str
    size: int        # bytes
    type: str        # file, directory
    path: str
    modified_time: str
    permissions: str

class UploadResponse(BaseModel):
    success: bool
    message: str
    file_path: Optional[str] = None

# 配置
UPLOAD_DIR = Path("uploads")
MODELS_DIR = Path("models")
DATASETS_DIR = Path("uploads/datasets")

# 确保目录存在
UPLOAD_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
DATASETS_DIR.mkdir(exist_ok=True)

def get_storage_info() -> List[StorageInfo]:
    """获取存储设备信息"""
    try:
        storage_devices = []
        
        # 获取根目录磁盘信息
        root_usage = shutil.disk_usage('/')
        root_total = root_usage.total // (1024**3)  # GB
        root_used = root_usage.used // (1024**3)    # GB
        
        # 确定状态
        usage_percent = (root_used / root_total) * 100
        status = "normal"
        if usage_percent > 90:
            status = "error"
        elif usage_percent > 80:
            status = "warning"
        
        # 主存储
        storage_devices.append(StorageInfo(
            id="STORAGE-001",
            name="主存储",
            type="ssd",
            total_space=root_total,
            used_space=root_used,
            status=status,
            mount_point="/"
        ))
        
        # 检查其他挂载点
        try:
            with open('/proc/mounts', 'r') as f:
                mounts = f.readlines()
            
            for mount in mounts:
                parts = mount.split()
                if len(parts) >= 3:
                    device, mount_point, fs_type = parts[0], parts[1], parts[2]
                    
                    # 跳过系统挂载点
                    if mount_point in ['/', '/proc', '/sys', '/dev', '/run']:
                        continue
                    
                    # 检查是否为数据存储
                    if mount_point.startswith('/data') or mount_point.startswith('/media'):
                        try:
                            usage = shutil.disk_usage(mount_point)
                            total = usage.total // (1024**3)
                            used = usage.used // (1024**3)
                            
                            usage_percent = (used / total) * 100 if total > 0 else 0
                            status = "normal"
                            if usage_percent > 90:
                                status = "error"
                            elif usage_percent > 80:
                                status = "warning"
                            
                            storage_type = "ssd" if "ssd" in device.lower() else "hdd"
                            
                            storage_devices.append(StorageInfo(
                                id=f"STORAGE-{len(storage_devices)+1:03d}",
                                name=f"存储设备 {len(storage_devices)+1}",
                                type=storage_type,
                                total_space=total,
                                used_space=used,
                                status=status,
                                mount_point=mount_point
                            ))
                        except Exception:
                            continue
        
        except Exception:
            pass
        
        # 如果没有找到其他存储设备，添加模拟数据
        if len(storage_devices) == 1:
            storage_devices.append(StorageInfo(
                id="STORAGE-002",
                name="备份存储",
                type="hdd",
                total_space=1000,
                used_space=600,
                status="normal",
                mount_point="/backup"
            ))
        
        return storage_devices
        
    except Exception as e:
        logger.error(f"获取存储信息失败: {e}")
        # 返回模拟数据
        return [
            StorageInfo(
                id="STORAGE-001",
                name="主存储",
                type="ssd",
                total_space=500,
                used_space=300,
                status="normal",
                mount_point="/"
            ),
            StorageInfo(
                id="STORAGE-002",
                name="备份存储",
                type="hdd",
                total_space=1000,
                used_space=600,
                status="warning",
                mount_point="/backup"
            )
        ]

def get_file_info(path: str) -> List[FileInfo]:
    """获取目录下的文件信息"""
    try:
        files = []
        path_obj = Path(path)
        
        if not path_obj.exists():
            return files
        
        for item in path_obj.iterdir():
            try:
                stat = item.stat()
                size = stat.st_size if item.is_file() else 0
                file_type = "directory" if item.is_dir() else "file"
                modified_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
                permissions = oct(stat.st_mode)[-3:]
                
                files.append(FileInfo(
                    name=item.name,
                    size=size,
                    type=file_type,
                    path=str(item),
                    modified_time=modified_time,
                    permissions=permissions
                ))
            except Exception:
                continue
        
        # 按类型和名称排序
        files.sort(key=lambda x: (x.type == "file", x.name.lower()))
        return files
        
    except Exception as e:
        logger.error(f"获取文件信息失败: {e}")
        return []

def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

@router.get("/devices", response_model=List[StorageInfo])
async def get_storage_devices():
    """获取存储设备列表"""
    try:
        devices = get_storage_info()
        return devices
    except Exception as e:
        logger.error(f"获取存储设备失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files")
async def get_files(
    path: str = Query(default="/", description="目录路径"),
    file_type: Optional[str] = Query(default=None, description="文件类型筛选"),
    search: Optional[str] = Query(default=None, description="搜索关键词")
):
    """获取文件列表"""
    try:
        # 安全检查，防止路径遍历攻击
        safe_path = Path(path).resolve()
        if not str(safe_path).startswith(str(Path.cwd())):
            raise HTTPException(status_code=403, detail="访问被拒绝")
        
        files = get_file_info(str(safe_path))
        
        # 应用筛选
        if file_type:
            files = [f for f in files if f.type == file_type]
        
        if search:
            search_lower = search.lower()
            files = [f for f in files if search_lower in f.name.lower()]
        
        # 添加格式化的大小信息
        for file in files:
            file.size_formatted = format_file_size(file.size)
        
        return {
            "path": str(safe_path),
            "files": files,
            "total_count": len(files)
        }
        
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    target_path: str = Form(...)
):
    """上传文件"""
    try:
        # 验证目标路径
        if target_path not in ["models", "datasets", "uploads"]:
            raise HTTPException(status_code=400, detail="无效的目标路径")
        
        # 确定上传目录
        if target_path == "models":
            upload_dir = MODELS_DIR
        elif target_path == "datasets":
            upload_dir = DATASETS_DIR
        else:
            upload_dir = UPLOAD_DIR
        
        # 检查文件大小（限制500MB）
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > 500 * 1024 * 1024:  # 500MB
            raise HTTPException(status_code=413, detail="文件大小超过500MB限制")
        
        # 保存文件
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"文件上传成功: {file_path}")
        
        return UploadResponse(
            success=True,
            message=f"文件 {file.filename} 上传成功",
            file_path=str(file_path)
        )
        
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download")
async def download_file(file_path: str = Query(...)):
    """下载文件"""
    try:
        # 安全检查
        safe_path = Path(file_path).resolve()
        if not str(safe_path).startswith(str(Path.cwd())):
            raise HTTPException(status_code=403, detail="访问被拒绝")
        
        if not safe_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if safe_path.is_dir():
            raise HTTPException(status_code=400, detail="不能下载目录")
        
        return FileResponse(
            path=str(safe_path),
            filename=safe_path.name,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"文件下载失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/files")
async def delete_file(file_path: str = Query(...)):
    """删除文件"""
    try:
        # 安全检查
        safe_path = Path(file_path).resolve()
        if not str(safe_path).startswith(str(Path.cwd())):
            raise HTTPException(status_code=403, detail="访问被拒绝")
        
        if not safe_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if safe_path.is_dir():
            shutil.rmtree(safe_path)
        else:
            safe_path.unlink()
        
        logger.info(f"文件删除成功: {safe_path}")
        
        return {"success": True, "message": f"文件 {safe_path.name} 删除成功"}
        
    except Exception as e:
        logger.error(f"文件删除失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preview")
async def preview_file(file_path: str = Query(...)):
    """预览文件"""
    try:
        # 安全检查
        safe_path = Path(file_path).resolve()
        if not str(safe_path).startswith(str(Path.cwd())):
            raise HTTPException(status_code=403, detail="访问被拒绝")
        
        if not safe_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if safe_path.is_dir():
            raise HTTPException(status_code=400, detail="不能预览目录")
        
        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(str(safe_path))
        
        # 对于文本文件，返回内容
        if mime_type and mime_type.startswith('text/'):
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read(10000)  # 限制预览内容长度
            
            return {
                "type": "text",
                "content": content,
                "mime_type": mime_type
            }
        
        # 对于其他文件，返回基本信息
        stat = safe_path.stat()
        return {
            "type": "binary",
            "size": stat.st_size,
            "mime_type": mime_type or "application/octet-stream",
            "message": "二进制文件，无法预览"
        }
        
    except Exception as e:
        logger.error(f"文件预览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_storage_stats():
    """获取存储统计信息"""
    try:
        devices = get_storage_info()
        
        total_space = sum(device.total_space for device in devices)
        used_space = sum(device.used_space for device in devices)
        available_space = total_space - used_space
        usage_rate = (used_space / total_space * 100) if total_space > 0 else 0
        
        # 获取文件统计
        models_count = len(list(MODELS_DIR.rglob("*"))) if MODELS_DIR.exists() else 0
        datasets_count = len(list(DATASETS_DIR.rglob("*"))) if DATASETS_DIR.exists() else 0
        uploads_count = len(list(UPLOAD_DIR.rglob("*"))) if UPLOAD_DIR.exists() else 0
        
        return {
            "storage_stats": {
                "total_space_gb": total_space,
                "used_space_gb": used_space,
                "available_space_gb": available_space,
                "usage_rate_percent": usage_rate,
                "device_count": len(devices)
            },
            "file_stats": {
                "models_count": models_count,
                "datasets_count": datasets_count,
                "uploads_count": uploads_count,
                "total_files": models_count + datasets_count + uploads_count
            },
            "devices": devices
        }
        
    except Exception as e:
        logger.error(f"获取存储统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/usage-trend")
async def get_usage_trend():
    """获取存储使用趋势"""
    try:
        # 生成模拟趋势数据
        current_time = time.time()
        trend_data = []
        
        for i in range(30):  # 30天数据
            timestamp = current_time - (29 - i) * 24 * 3600
            date_str = time.strftime("%Y-%m-%d", time.localtime(timestamp))
            
            # 模拟使用率增长
            base_usage = 60
            daily_growth = i * 0.5
            random_variation = (i % 7) * 2  # 周期性变化
            
            usage = min(95, base_usage + daily_growth + random_variation)
            
            trend_data.append({
                "date": date_str,
                "usage": round(usage, 1)
            })
        
        return trend_data
        
    except Exception as e:
        logger.error(f"获取使用趋势失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
