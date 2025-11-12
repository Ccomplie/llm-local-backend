"""
应用配置管理
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    app_name: str = "大模型本地化后端"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 模型配置
    models_dir: str = "./models/test_model"
    default_model: Optional[str] = None
    max_model_memory_gb: float = 8.0
    model_cache_size: int = 3
    
    # 对话配置
    max_conversation_length: int = 4096
    max_response_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    
    # 数据库配置
    database_url: str = "sqlite:///./llm_backend.db"
    redis_url: str = "redis://localhost:6379"
    
    # 安全配置
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    # 文件上传配置
    upload_dir: str = "./uploads"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: List[str] = [
        ".txt",
        ".md",
        ".json",
        ".csv",
        ".pdf",
        ".docx",
        ".xlsx",
        ".pptx"
    ]
    file_context_max_chars: int = 20000
    file_preview_chars: int = 800
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "./logs/backend.log"
    
    # 模型服务配置
    enable_gpu: bool = True
    gpu_memory_fraction: float = 0.8
    quantization: str = "int4"  # none, int8, int4 - 使用int4量化进一步加速
    
    @field_validator("models_dir", "upload_dir")
    def create_directories(cls, v):
        """确保目录存在"""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator("log_file")
    def create_log_dir(cls, v):
        """确保日志目录存在"""
        Path(v).parent.mkdir(parents=True, exist_ok=True)
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 全局设置实例
settings = Settings()