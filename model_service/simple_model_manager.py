"""
简化的模型管理器 - 用于测试和演示
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from pathlib import Path

logger = logging.getLogger(__name__)

class SimpleModelManager:
    """简化的模型管理器"""
    
    def __init__(self):
        self.models = {}
        self.current_model = None
        self.is_loaded = False
        
    async def initialize(self):
        """初始化模型管理器"""
        logger.info("初始化简化模型管理器...")
        
        # 扫描模型目录
        await self.scan_models()
        
        # 自动加载第一个模型
        if self.models:
            first_model = list(self.models.keys())[0]
            await self.load_model(first_model)
        
        logger.info("简化模型管理器初始化完成")
    
    async def scan_models(self):
        """扫描模型目录"""
        models_dir = Path("./models")
        if not models_dir.exists():
            logger.warning(f"模型目录不存在: {models_dir}")
            return
        
        logger.info(f"扫描模型目录: {models_dir}")
        
        for model_path in models_dir.iterdir():
            if model_path.is_dir() and (model_path / "config.json").exists():
                model_name = model_path.name
                self.models[model_name] = {
                    "name": model_name,
                    "path": str(model_path),
                    "is_loaded": False,
                    "is_current": False
                }
                logger.info(f"发现模型: {model_name}")
    
    async def load_model(self, model_name: str) -> bool:
        """加载指定模型"""
        if model_name not in self.models:
            logger.error(f"模型不存在: {model_name}")
            return False
        
        logger.info(f"加载简化模型: {model_name}")
        self.models[model_name]["is_loaded"] = True
        self.models[model_name]["is_current"] = True
        
        # 重置其他模型状态
        for name, info in self.models.items():
            if name != model_name:
                info["is_loaded"] = False
                info["is_current"] = False
        
        self.current_model = model_name
        self.is_loaded = True
        
        logger.info(f"已切换到模型: {model_name}")
        return True
    
    async def unload_model(self, model_name: str) -> bool:
        """卸载指定模型"""
        if model_name not in self.models:
            return False
        
        self.models[model_name]["is_loaded"] = False
        self.models[model_name]["is_current"] = False
        
        if self.current_model == model_name:
            self.current_model = None
            self.is_loaded = False
        
        logger.info(f"模型 {model_name} 已卸载")
        return True
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        if not self.is_loaded:
            raise RuntimeError("没有加载的模型")
        
        # 模拟生成文本
        max_tokens = kwargs.get("max_tokens", 100)
        temperature = kwargs.get("temperature", 0.7)
        
        # 简单的模拟回复
        responses = [
            "这是一个模拟的DeepSeek模型回复。",
            "你好！我是DeepSeek-7B模型，很高兴为您服务。",
            "我理解您的问题，让我来为您解答。",
            "这是一个基于您输入的回复示例。",
            "感谢您使用DeepSeek模型！"
        ]
        
        # 根据输入选择回复
        if "你好" in prompt or "hello" in prompt.lower():
            response = "你好！我是DeepSeek-7B模型，很高兴为您服务。"
        elif "问题" in prompt or "?" in prompt:
            response = "我理解您的问题，让我来为您解答。"
        else:
            import random
            response = random.choice(responses)
        
        # 模拟生成时间
        await asyncio.sleep(0.5)
        
        return response
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        if not self.is_loaded:
            raise RuntimeError("没有加载的模型")
        
        # 获取完整回复
        response = await self.generate_text(prompt, **kwargs)
        
        # 逐字符输出
        for char in response:
            yield char
            await asyncio.sleep(0.02)  # 模拟流式输出
    
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return list(self.models.keys())
    
    def get_current_model(self) -> Optional[str]:
        """获取当前模型"""
        return self.current_model
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """获取模型信息"""
        if model_name not in self.models:
            return {}
        
        return self.models[model_name]
    
    async def cleanup(self):
        """清理资源"""
        logger.info("清理简化模型管理器...")
        self.models.clear()
        self.current_model = None
        self.is_loaded = False
        logger.info("简化模型管理器清理完成")