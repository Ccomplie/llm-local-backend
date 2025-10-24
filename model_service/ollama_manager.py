"""
Ollama模型管理器
使用Ollama API进行GPU加速的模型推理
"""

import requests
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from loguru import logger
from config.settings import Settings


class OllamaManager:
    """Ollama模型管理器"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.ollama_url = "http://127.0.0.1:11434"
        self.current_model = None
        self.available_models = []
        
    async def initialize(self):
        """初始化Ollama管理器"""
        logger.info("初始化Ollama模型管理器...")
        
        try:
            # 获取可用模型列表
            await self._load_available_models()
            
            # 设置默认模型
            if self.available_models:
                self.current_model = self.available_models[0]
                logger.info(f"默认模型设置为: {self.current_model}")
            
            logger.info("Ollama模型管理器初始化完成")
            
        except Exception as e:
            logger.error(f"Ollama模型管理器初始化失败: {e}")
            raise
    
    async def _load_available_models(self):
        """加载可用模型列表"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self.available_models = [model["name"] for model in data.get("models", [])]
            logger.info(f"发现Ollama模型: {self.available_models}")
            
        except Exception as e:
            logger.error(f"获取Ollama模型列表失败: {e}")
            self.available_models = []
    
    async def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return self.available_models.copy()
    
    async def get_current_model(self) -> Optional[str]:
        """获取当前模型"""
        return self.current_model
    
    async def switch_model(self, model_name: str) -> bool:
        """切换模型"""
        if model_name in self.available_models:
            self.current_model = model_name
            logger.info(f"已切换到模型: {model_name}")
            return True
        else:
            logger.error(f"模型不存在: {model_name}")
            return False
    
    async def generate_response(self, messages: List[Dict[str, str]], stream: bool = False) -> Any:
        """生成响应"""
        if not self.current_model:
            raise ValueError("没有设置当前模型")
        
        # 构建请求数据
        request_data = {
            "model": self.current_model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2048,
            }
        }
        
        try:
            if stream:
                return self._stream_generate(request_data)
            else:
                return await self._generate_sync(request_data)
                
        except Exception as e:
            logger.error(f"生成响应失败: {e}")
            raise
    
    async def _generate_sync(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """同步生成响应"""
        response = requests.post(
            f"{self.ollama_url}/api/chat",
            json=request_data,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "message": result.get("message", {}).get("content", ""),
            "usage": {
                "prompt_tokens": result.get("prompt_eval_count", 0),
                "completion_tokens": result.get("eval_count", 0),
            },
            "model": self.current_model
        }
    
    async def _stream_generate(self, request_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """流式生成响应"""
        response = requests.post(
            f"{self.ollama_url}/api/chat",
            json=request_data,
            stream=True,
            timeout=60
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    
                    if data.get("done", False):
                        break
                    
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield {
                            "content": content,
                            "done": False
                        }
                        
                except json.JSONDecodeError:
                    continue
        
        yield {"content": "", "done": True}
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """生成文本（兼容接口）"""
        try:
            messages = [{"role": "user", "content": prompt}]
            result = await self.generate_response(messages, stream=False)
            return result.get("message", "")
        except Exception as e:
            logger.error(f"生成文本失败: {e}")
            raise

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "name": model_name,
            "path": f"ollama://{model_name}",
            "is_loaded": model_name == self.current_model,
            "is_current": model_name == self.current_model,
            "size": "Unknown",  # Ollama不提供模型大小信息
            "type": "ollama"
        }
    
    async def load_model(self, model_name: str) -> bool:
        """加载模型（切换当前模型）"""
        try:
            if model_name in self.available_models:
                self.current_model = model_name
                logger.info(f"已切换到模型: {model_name}")
                return True
            else:
                logger.error(f"模型不存在: {model_name}")
                return False
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return False
    
    async def unload_model(self, model_name: str):
        """卸载模型（Ollama不需要显式卸载）"""
        logger.info(f"Ollama模型 {model_name} 无需显式卸载")
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            response = requests.get(f"{self.ollama_url}/api/version", timeout=5)
            response.raise_for_status()
            
            version_info = response.json()
            
            return {
                "status": "healthy",
                "ollama_version": version_info.get("version", "unknown"),
                "current_model": self.current_model,
                "available_models": len(self.available_models),
                "gpu_acceleration": True  # Ollama默认使用GPU
            }
            
        except Exception as e:
            logger.error(f"Ollama健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
