"""
数据库配置和初始化
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from datetime import datetime

from config.settings import settings

# 创建异步引擎
engine = create_async_engine(
    settings.database_url.replace("sqlite://", "sqlite+aiosqlite://"),
    echo=False
)

# 创建异步会话
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 创建基础模型类
Base = declarative_base()

class Conversation(Base):
    """对话记录表"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    session_id = Column(String, index=True)
    model_name = Column(String)
    user_message = Column(Text)
    assistant_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class TrainingJob(Base):
    """训练任务表"""
    __tablename__ = "training_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True)
    model_name = Column(String)
    status = Column(String)  # pending, running, completed, failed, cancelled
    config = Column(Text)  # JSON配置
    progress = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ModelInfo(Base):
    """模型信息表"""
    __tablename__ = "model_info"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    path = Column(String)
    size = Column(Integer)
    format = Column(String)  # transformers, llama-cpp, etc.
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

async def init_database():
    """初始化数据库"""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
