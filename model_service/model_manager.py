"""
模型管理器 - 统一管理不同格式的大模型
"""

import asyncio
import logging
import gc
from typing import Dict, List, Optional, Any, AsyncGenerator
from pathlib import Path
from abc import ABC, abstractmethod

# 可选导入torch
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch未安装，将使用基础功能")

from config.settings import settings

logger = logging.getLogger(__name__)

class BaseModel(ABC):
    """模型基类"""
    
    def __init__(self, model_path: str, model_name: str):
        self.model_path = model_path
        self.model_name = model_name
        self.is_loaded = False
        
    @abstractmethod
    async def load(self) -> bool:
        """加载模型"""
        pass
    
    @abstractmethod
    async def unload(self) -> bool:
        """卸载模型"""
        pass
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        pass

class TransformersModel(BaseModel):
    """Transformers模型实现"""
    
    def __init__(self, model_path: str, model_name: str):
        super().__init__(model_path, model_name)
        self.model = None
        self.tokenizer = None
        if TORCH_AVAILABLE:
            self.device = "cuda" if torch.cuda.is_available() and settings.enable_gpu else "cpu"
            print("device:", self.device)
        else:
            self.device = "cpu"
    
    async def load(self) -> bool:
        """加载Transformers模型"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            logger.info(f"正在加载模型: {self.model_name}")
            
            # 加载分词器
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # 配置模型加载参数
            model_kwargs = {
                "trust_remote_code": True,
            }
            
            if TORCH_AVAILABLE:
                model_kwargs["torch_dtype"] = torch.float16 if self.device == "cuda" else torch.float32
                
                # 量化配置
                if settings.quantization == "int8":
                    model_kwargs["load_in_8bit"] = True
                elif settings.quantization == "int4":
                    model_kwargs["load_in_4bit"] = True
            
            # 加载模型
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                **model_kwargs
            )
            
            if TORCH_AVAILABLE and self.device == "cuda":
                self.model = self.model.cuda()
            
            self.is_loaded = True
            logger.info(f"模型 {self.model_name} 加载完成")
            return True
            
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return False
    
    async def unload(self) -> bool:
        """卸载模型"""
        try:
            if self.model:
                del self.model
                self.model = None
            if self.tokenizer:
                del self.tokenizer
                self.tokenizer = None
            
            if TORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            
            self.is_loaded = False
            logger.info(f"模型 {self.model_name} 已卸载")
            return True
            
        except Exception as e:
            logger.error(f"卸载模型失败: {e}")
            return False
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        if not self.is_loaded:
            raise RuntimeError("模型未加载")
        
        try:
            # 编码输入
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            if self.device == "cuda":
                inputs = inputs.cuda()
            
            # 生成参数
            generation_kwargs = {
                "max_new_tokens": kwargs.get("max_tokens", settings.max_response_tokens),
                "temperature": kwargs.get("temperature", settings.temperature),
                "top_p": kwargs.get("top_p", settings.top_p),
                "do_sample": True,
                "pad_token_id": self.tokenizer.eos_token_id,
            }
            
            # 生成文本
            with torch.no_grad():
                outputs = self.model.generate(inputs, **generation_kwargs)
            
            # 解码输出
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # 移除输入部分
            response = response[len(prompt):].strip()
            
            return response
            
        except Exception as e:
            logger.error(f"文本生成失败: {e}")
            raise
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        if not self.is_loaded:
            raise RuntimeError("模型未加载")
        
        try:
            # 编码输入
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            if self.device == "cuda":
                inputs = inputs.cuda()
            
            # 生成参数
            generation_kwargs = {
                "max_new_tokens": kwargs.get("max_tokens", settings.max_response_tokens),
                "temperature": kwargs.get("temperature", settings.temperature),
                "top_p": kwargs.get("top_p", settings.top_p),
                "do_sample": True,
                "pad_token_id": self.tokenizer.eos_token_id,
            }
            
            # 流式生成
            generated_tokens = []
            with torch.no_grad():
                for _ in range(generation_kwargs["max_new_tokens"]):
                    # 生成下一个token
                    outputs = self.model.generate(
                        inputs,
                        max_new_tokens=1,
                        **{k: v for k, v in generation_kwargs.items() if k != "max_new_tokens"}
                    )
                    
                    # 获取新生成的token
                    new_token = outputs[0][-1].item()
                    generated_tokens.append(new_token)
                    
                    # 解码并返回
                    token_text = self.tokenizer.decode([new_token], skip_special_tokens=True)
                    yield token_text
                    
                    # 更新输入
                    inputs = outputs
                    
                    # 检查结束条件
                    if new_token == self.tokenizer.eos_token_id:
                        break
                    
                    await asyncio.sleep(0.01)  # 避免阻塞
                    
        except Exception as e:
            logger.error(f"流式生成失败: {e}")
            raise

class ModelManager:
    """模型管理器"""
    
    def __init__(self):
        self.models: Dict[str, BaseModel] = {}
        self.current_model: Optional[str] = None
        self.model_cache_size = settings.model_cache_size
    
    async def initialize(self):
        """初始化模型管理器"""
        logger.info("初始化模型管理器...")
        
        # 扫描模型目录
        await self.scan_models()
        
        # 加载默认模型
        if settings.default_model and settings.default_model in self.models:
            await self.load_model(settings.default_model)
        
        logger.info("模型管理器初始化完成")
    
    async def scan_models(self):
        """扫描模型目录"""
        models_dir = Path(settings.models_dir)
        if not models_dir.exists():
            logger.warning(f"模型目录不存在: {models_dir}")
            return
        
        logger.info(f"扫描模型目录: {models_dir}")
        
        for model_path in models_dir.iterdir():
            if model_path.is_dir():
                model_name = model_path.name
                
                # 检查是否为Transformers模型
                if (model_path / "config.json").exists():
                    self.models[model_name] = TransformersModel(
                        str(model_path), model_name
                    )
                    logger.info(f"发现模型: {model_name}")
    
    async def load_model(self, model_name: str) -> bool:
        """加载指定模型"""
        if model_name not in self.models:
            logger.error(f"模型不存在: {model_name}")
            return False
        
        # 卸载当前模型
        if self.current_model:
            await self.unload_model(self.current_model)
        
        # 加载新模型
        model = self.models[model_name]
        success = await model.load()
        
        if success:
            self.current_model = model_name
            logger.info(f"已切换到模型: {model_name}")
        else:
            logger.error(f"加载模型失败: {model_name}")
        
        return success
    
    async def unload_model(self, model_name: str) -> bool:
        """卸载指定模型"""
        if model_name not in self.models:
            return False
        
        model = self.models[model_name]
        success = await model.unload()
        
        if success and self.current_model == model_name:
            self.current_model = None
        
        return success
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        if not self.current_model:
            raise RuntimeError("没有加载的模型")
        
        model = self.models[self.current_model]
        return await model.generate(prompt, **kwargs)
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        if not self.current_model:
            raise RuntimeError("没有加载的模型")
        
        model = self.models[self.current_model]
        async for token in model.generate_stream(prompt, **kwargs):
            yield token
    
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
        
        model = self.models[model_name]
        return {
            "name": model.model_name,
            "path": model.model_path,
            "is_loaded": model.is_loaded,
            "is_current": model_name == self.current_model
        }
    
    async def cleanup(self):
        """清理资源"""
        logger.info("清理模型管理器...")
        
        for model_name in list(self.models.keys()):
            await self.unload_model(model_name)
        
        self.models.clear()
        self.current_model = None
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        
        logger.info("模型管理器清理完成")
