"""
混合模型管理器
同时支持Ollama模型和Transformers格式的模型
"""
import re
import requests
import json
import asyncio
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncGenerator
from loguru import logger
from config.settings import Settings
from transformers import activations
activations.PytorchGELUTanh = activations.GELUTanh
# 尝试导入Transformers相关模块
try:
    from transformers import TextStreamer
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TextStreamer,  AwqConfig
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers库不可用，将只支持Ollama模型")


class HybridModelManager:
    """混合模型管理器"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.ollama_url = "http://127.0.0.1:11434"
        self.current_model = None
        self.current_model_type = None  # 'ollama' 或 'transformers'
        self.available_models = []
        self.transformers_model = None
        self.transformers_tokenizer = None
        
    async def initialize(self):
        """初始化混合模型管理器"""
        logger.info("初始化混合模型管理器...")
        
        try:
            # 获取Ollama模型列表
            await self._load_ollama_models()
            
            # 获取Transformers模型列表
            await self._load_transformers_models()
            
            # 设置默认模型
            if self.available_models:
                self.current_model = self.available_models[0]['name']
                self.current_model_type = self.available_models[0]['type']
                logger.info(f"默认模型设置为: {self.current_model} ({self.current_model_type})")
            else:
                raise Exception("未找到可用模型")
            
            if self.current_model_type == "transformers":
                model_info = next((m for m in self.available_models if m['name'] == self.current_model), None)
                logger.info(model_info)
                if model_info == None:
                    raise Exception("未找到模型文件")
                await self._load_transformers_model(model_info['path'])
        


            logger.info("混合模型管理器初始化完成")
            
        except Exception as e:
            logger.error(f"混合模型管理器初始化失败: {e}")
            raise
    
    async def _load_ollama_models(self):
        """加载Ollama模型列表"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            ollama_models = [model["name"] for model in data.get("models", [])]
            
            for model_name in ollama_models:
                self.available_models.append({
                    "name": model_name,
                    "type": "ollama",
                    "path": f"ollama://{model_name}",
                    "is_loaded": False,
                    "is_current": False,
                    "size": None
                })
            
            logger.info(f"发现Ollama模型: {ollama_models}")
            
        except Exception as e:
            logger.error(f"获取Ollama模型列表失败: {e}")
    
    async def _load_transformers_models(self):
        """加载Transformers模型列表"""
        if not TRANSFORMERS_AVAILABLE:
            return
            
        try:
            models_dir = Path(self.settings.models_dir)
            if not models_dir.exists():
                return
                
            for model_path in models_dir.iterdir():
                if model_path.is_dir():
                    config_file = model_path / "config.json"
                    if config_file.exists():
                        model_name = f"transformers://{model_path.name}"
                        self.available_models.append({
                            "name": model_name,
                            "type": "transformers",
                            "path": str(model_path),
                            "is_loaded": False,
                            "is_current": False,
                            "size": None
                        })
            
            logger.info(f"发现Transformers模型: {[m['name'] for m in self.available_models if m['type'] == 'transformers']}")
            
        except Exception as e:
            logger.error(f"获取Transformers模型列表失败: {e}")
    
    async def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return [model['name'] for model in self.available_models]
    
    async def get_current_model(self) -> Optional[str]:
        """获取当前模型"""
        return self.current_model
    
    async def switch_model(self, model_name: str) -> bool:
        """切换模型"""
        model_info = next((m for m in self.available_models if m['name'] == model_name), None)
        if not model_info:
            logger.error(f"模型不存在: {model_name}")
            return False
        
        try:
            # 卸载当前模型
            if self.current_model_type == 'transformers' and self.transformers_model:
                del self.transformers_model
                del self.transformers_tokenizer
                self.transformers_model = None
                self.transformers_tokenizer = None
                torch.cuda.empty_cache()
            
            # 加载新模型
            if model_info['type'] == 'ollama':
                self.current_model = model_name
                self.current_model_type = 'ollama'
            elif model_info['type'] == 'transformers':
                await self._load_transformers_model(model_info['path'])
                self.current_model = model_name
                self.current_model_type = 'transformers'
            
            # 更新模型状态
            for model in self.available_models:
                model['is_current'] = (model['name'] == model_name)
            
            logger.info(f"已切换到模型: {model_name} ({model_info['type']})")
            return True
            
        except Exception as e:
            logger.error(f"切换模型失败: {e}")
            return False
    
    # async def _load_transformers_model(self, model_path: str):
    #     """加载Transformers模型"""
    #     if not TRANSFORMERS_AVAILABLE:
    #         raise RuntimeError("Transformers库不可用")
        
    #     logger.info(f"正在加载Transformers模型: {model_path}")
        
    #     # 加载tokenizer
    #     self.transformers_tokenizer = AutoTokenizer.from_pretrained(model_path)
        
    #     # 加载模型
    #     device = "cuda" if torch.cuda.is_available() else "cpu"

        
    #     bnb_config = BitsAndBytesConfig(
    #         load_in_8bit=True,                    # 启用8bit量化
    #         bnb_8bit_compute_dtype=torch.bfloat16, # 计算时使用float8
    #         bnb_8bit_use_double_quant=True,       # 使用双重量化，进一步节省内存
    #         bnb_8bit_quant_type="fp8",            # 量化类型，可选"fp8"或"nf4"
    #     )

    #     self.transformers_model = AutoModelForCausalLM.from_pretrained(
    #         model_path,
    #         dtype=torch.bfloat16 if device == "cuda" else torch.float32,
    #         #device_map="auto" if device == "cuda" else None,
    #         device_map="cuda",
    #         trust_remote_code=True,
    #         quantization_config=bnb_config
    #     )
        
    #     if device == "cpu":
    #         self.transformers_model = self.transformers_model.to(device)
        
    #     logger.info(f"Transformers模型加载完成，使用设备: {device}")
    

    async def _load_transformers_model(self, model_path:str, quant_method: str = "auto", device_map: str = "auto", **kwargs):
        """加载Transformers模型，支持多种量化方法"""
        try:
            model_format = detect_model_format(model_path)
            print(f"检测到模型格式: {model_format}")
            
            # 创建量化配置
            quantization_config, model_kwargs, used_quant_method = create_quantization_config(
                model_format, quant_method
            )
            
            # 合并参数
            model_kwargs.update({
                "quantization_config": quantization_config,
                "device_map": device_map,
                "trust_remote_code": True,
                **kwargs
            })
            
        
            if "torch_dtype" not in model_kwargs and quantization_config is None:
                model_kwargs["torch_dtype"] = torch.bfloat16
            
            # 移除None值参数
            model_kwargs = {k: v for k, v in model_kwargs.items() if v is not None}
        
            self.transformers_model = AutoModelForCausalLM.from_pretrained(model_path, **model_kwargs)
            self.transformers_tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        
            # 创建量化信息字典
            quant_info = {
                "model_format": model_format,
                "quant_method": used_quant_method,
                "quantization_config": quantization_config,
                "model_kwargs": model_kwargs
            }
            
            print(f"成功加载模型 - 格式: {model_format}, 量化方法: {used_quant_method}")
            
        except Exception as e:
            print(f"加载模型失败: {e}")
            # 回退到非量化加载
            print("尝试非量化加载...")
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                device_map=device_map,
                torch_dtype=torch.bfloat16,
                trust_remote_code=True
            )
            tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            
            quant_info = {
                "model_format": model_format,
                "quant_method": "none",
                "quantization_config": None,
                "model_kwargs": {"fallback": True}
            }
            
            return model, tokenizer, quant_info
    

    async def generate_response(self, messages: List[Dict[str, str]], stream: bool = False) -> Any:
        """生成响应"""
        if not self.current_model:
            logger.error("没有设置当前模型")
            raise ValueError("没有设置当前模型")
        
        if self.current_model_type == 'ollama':
            return await self._generate_ollama_response(messages, stream)
        elif self.current_model_type == 'transformers':
            return await self._generate_transformers_response(messages, stream)
        else:
            logger.error(f"未知的模型类型: {self.current_model_type}")
            raise ValueError(f"未知的模型类型: {self.current_model_type}")
    
    async def _generate_ollama_response(self, messages: List[Dict[str, str]], stream: bool = False) -> Any:
        """使用Ollama生成响应"""
        request_data = {
            "model": self.current_model.replace("ollama://", ""),
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
                return self._stream_ollama_generate(request_data)
            else:
                return await self._generate_ollama_sync(request_data)
                
        except Exception as e:
            logger.error(f"Ollama生成响应失败: {e}")
            raise
    
    async def _generate_ollama_sync(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """同步Ollama生成响应"""
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
    
    async def _stream_ollama_generate(self, request_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """流式Ollama生成响应"""
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
    
    async def _generate_transformers_response(self, messages: List[Dict[str, str]], tools) -> Any:
        """使用Transformers生成响应"""
        if not self.transformers_model or not self.transformers_tokenizer:
            raise RuntimeError("Transformers模型未加载")
        
        input_text = self.transformers_tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False # Switches between thinking and non-thinking modes. Default is True.
        )

        # 编码输入
        logger.info(f"\nTransformers输入文本: {input_text}")
        inputs = self.transformers_tokenizer.encode(input_text, return_tensors="pt")
        
        if torch.cuda.is_available():
            inputs = inputs.cuda()
            logger.info("使用GPU进行推理")
        
        if stream:
            # 流式生成
            return self._stream_transformers_generate(inputs)
        else:
            # 同步生成
            with torch.no_grad():
                outputs = self.transformers_model.generate(
                    inputs,
                    max_new_tokens=2048,
                    temperature=0.6,
                    top_p=0.9,
                    top_k=40,
                    do_sample=True,
                    pad_token_id=self.transformers_tokenizer.eos_token_id
                )
            
            # 解码响应
            response_text = self.transformers_tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
            
            return {
                "message": response_text,
                "usage": {
                    "prompt_tokens": inputs.shape[1],
                    "completion_tokens": outputs.shape[1] - inputs.shape[1],
                },
                "model": self.current_model
            }
    
    async def _stream_transformers_generate(self, inputs) -> AsyncGenerator[Dict[str, Any], None]:
        """流式Transformers生成响应"""
        # 创建队列用于流式输出
        from queue import Queue
        output_queue = Queue()
        
        # 创建自定义流式处理器
        class CustomStreamer(TextStreamer):
            def __init__(self, tokenizer, queue, skip_prompt=True, **decode_kwargs):
                super().__init__(tokenizer, skip_prompt=skip_prompt, **decode_kwargs)
                self.queue = queue
            
            def on_finalized_text(self, text: str, stream_end: bool = False):
                """当文本最终确定时调用"""
                if text.strip():
                    self.queue.put({
                        "content": text,
                        "done": stream_end
                    })
        
        # 创建流式处理器
        streamer = CustomStreamer(
            self.transformers_tokenizer,
            output_queue,
            skip_prompt=True
        )
        
        # 在后台线程中运行生成
        import threading
        
        def generate_in_thread():
            try:
                with torch.no_grad():
                    self.transformers_model.generate(
                        inputs,
                        max_new_tokens=2048,
                        temperature=0.6,
                        top_p=0.9,
                        top_k=40,
                        do_sample=True,
                        pad_token_id=self.transformers_tokenizer.eos_token_id,
                        streamer=streamer
                    )
                # 生成完成后发送结束标记
                output_queue.put({"content": "", "done": True})
            except Exception as e:
                logger.error(f"Transformers流式生成失败: {e}")
                output_queue.put({"content": f"生成失败: {str(e)}", "done": True})
        
        # 启动生成线程
        thread = threading.Thread(target=generate_in_thread)
        thread.daemon = True
        thread.start()
        
        # 从队列中获取流式结果
        while True:
            try:
                result = output_queue.get(timeout=30)  # 30秒超时
                yield result
                if result.get("done", False):
                    break
            except:
                logger.warning("Transformers流式生成超时")
                yield {"content": "", "done": True}
                break
    
    async def generate_text(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """生成文本（兼容接口）"""
        try:
            
            result = await self.generate_response(messages, stream=False)
            return result.get("message", "")
        except Exception as e:
            logger.error(f"生成文本失败: {e}")
            raise

    async def generate_func_call(self, prompt: str, tools, **kwargs) -> str:
        """生成文本（兼容接口）"""
        try:
            messages = [{"role": "user", "content": prompt}]

            if self.current_model_type == 'transformers':
                result = await self._generate_transformers_response(messages, stream=False)
                return result.get("message", "")
        except Exception as e:
            logger.error(f"生成文本失败: {e}")
            raise

    

    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            if self.current_model_type == 'ollama':
                # 使用Ollama流式生成
                request_data = {
                    "model": self.current_model.replace("ollama://", ""),
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": kwargs.get("temperature", 0.7),
                        "top_p": kwargs.get("top_p", 0.9),
                        "max_tokens": kwargs.get("max_tokens", 2048),
                    }
                }
                
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
                                yield content
                                
                        except json.JSONDecodeError:
                            continue
                            
            elif self.current_model_type == 'transformers':
                # 使用真正的Transformers流式生成
                async for chunk in self._generate_transformers_response(messages, stream=True):
                    content = chunk.get("content", "")
                    if content:
                        yield content
            else:
                raise ValueError(f"未知的模型类型: {self.current_model_type}")
                
        except Exception as e:
            logger.error(f"流式生成失败: {e}")
            yield f"生成失败: {str(e)}"

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """获取模型信息"""
        model_info = next((m for m in self.available_models if m['name'] == model_name), None)
        if not model_info:
            return {
                "name": model_name,
                "path": "unknown",
                "is_loaded": False,
                "is_current": False,
                "size": "Unknown",
                "type": "unknown"
            }
        
        return {
            "name": model_name,
            "path": model_info['path'],
            "is_loaded": model_info['is_loaded'],
            "is_current": model_name == self.current_model,
            "size": model_info['size'],
            "type": model_info['type']
        }
    
    async def load_model(self, model_name: str) -> bool:
        """加载模型（切换当前模型）"""
        return await self.switch_model(model_name)
    
    async def unload_model(self, model_name: str):
        """卸载模型"""
        if model_name == self.current_model and self.current_model_type == 'transformers':
            if self.transformers_model:
                del self.transformers_model
                del self.transformers_tokenizer
                self.transformers_model = None
                self.transformers_tokenizer = None
                torch.cuda.empty_cache()
                logger.info(f"已卸载Transformers模型: {model_name}")
        else:
            logger.info(f"模型 {model_name} 无需显式卸载")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            health_info = {
                "status": "healthy",
                "current_model": self.current_model,
                "current_model_type": self.current_model_type,
                "available_models": len(self.available_models),
                "gpu_acceleration": torch.cuda.is_available() if TRANSFORMERS_AVAILABLE else False
            }
            
            # 检查Ollama状态
            try:
                response = requests.get(f"{self.ollama_url}/api/version", timeout=5)
                response.raise_for_status()
                version_info = response.json()
                health_info["ollama_version"] = version_info.get("version", "unknown")
                health_info["ollama_status"] = "healthy"
            except Exception as e:
                health_info["ollama_status"] = f"unhealthy: {e}"
            
            # 检查Transformers状态
            if TRANSFORMERS_AVAILABLE:
                health_info["transformers_available"] = True
                health_info["cuda_available"] = torch.cuda.is_available()
                if torch.cuda.is_available():
                    health_info["cuda_device_count"] = torch.cuda.device_count()
            else:
                health_info["transformers_available"] = False
            
            return health_info
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def cleanup(self):
        """清理资源"""
        logger.info("清理混合模型管理器资源...")
        if self.current_model_type == 'transformers' and self.transformers_model:
            del self.transformers_model
            del self.transformers_tokenizer
            self.transformers_model = None
            self.transformers_tokenizer = None
            torch.cuda.empty_cache()
        logger.info("混合模型管理器资源清理完成")



    async def _generate_transformers_func_call(self, messages: List[Dict[str, str]], tools) -> Any:
        """使用Transformers生成函数调用响应"""
        if not self.transformers_model or not self.transformers_tokenizer:
            raise RuntimeError("Transformers模型未加载")
        
        # 应用聊天模板，启用思考模式
        input_text = self.transformers_tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=True,  # 启用思考模式以支持函数调用
            tools=tools
        )

        # 添加工具描述到提示词
        # if tools:
        #     tools_desc = "\n可用工具:\n" + "\n".join([
        #         f"- {tool['function']['name']}: {tool['function']['description']}"
        #         for tool in tools
        #     ])
        #     input_text += tools_desc + "\n\n请根据用户需求选择合适的工具进行调用。"
        

        logger.info(f"\nTransformers函数调用输入文本: \n\n{input_text}")
        inputs = self.transformers_tokenizer.encode(input_text, return_tensors="pt")
        
        if torch.cuda.is_available():
            inputs = inputs.cuda()
            
        
        # 生成响应
        with torch.no_grad():
            outputs = self.transformers_model.generate(
                inputs,
                max_new_tokens=2048,
                temperature=0.6,  # 降低温度以获得更确定的函数调用
                top_p=0.8,
                top_k=30,
                do_sample=True,
                pad_token_id=self.transformers_tokenizer.eos_token_id,
            )
        
        # 解码响应
        response_text = self.transformers_tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
        
        # 尝试解析函数调用
        function_call = parse_function_call(response_text)
        
        return {
            "message": {
                "content": response_text,
                "tool_calls": [function_call] if function_call else []
            },
            "usage": {
                "prompt_tokens": inputs.shape[1],
                "completion_tokens": outputs.shape[1] - inputs.shape[1],
            },
            "model": self.current_model
        }

    async def generate_func_call(self, messages: List[Dict[str, str]], tools, **kwargs) -> Any:
        """生成函数调用"""
        try:
            if self.current_model_type == 'transformers':
                result = await self._generate_transformers_func_call(messages, tools)
                return result
            else:
                # 其他模型的函数调用实现
                raise NotImplementedError(f"模型类型 {self.current_model_type} 的函数调用未实现")
        except Exception as e:
            logger.error(f"函数调用生成失败: {e}")
            raise

def parse_function_call(response_text: str) -> Optional[Dict]:
    """解析函数调用响应"""
    logger.info(f"待解析函数调用文本: {response_text}")
    response_text = response_text.lower().split("tool_call")[-2].strip()
    
    try:

        # 简单的函数调用解析逻辑
        # 在实际应用中，您可能需要更复杂的解析
      
            # 提取参数
        import re
        db_match = re.search(r'database[\s:"]*([\w]+)', response_text, re.IGNORECASE)
        if db_match:
            logger.info("添加SQL函数调用")
            return {
                "function": {
                    "name": "sql_query",
                    "arguments": json.dumps({
                        "database": db_match.group(1),
                    })
                }
            }
                
        return None
    except Exception as e:
        logger.error(f"解析函数调用失败: {e}")
        return None
    

def create_quantization_config(model_format: str, quant_method: str = "auto") -> tuple[Optional[Any], Dict[str, Any]]:
    """
    创建量化配置
    
    Args:
        model_format: 模型格式
        quant_method: 量化方法 ["auto", "4bit", "8bit", "gptq", "awq"]
        
    Returns:
        Tuple: (quantization_config, model_kwargs)
    """
    model_kwargs = {}
    
    if quant_method == "auto":
        # 根据模型格式自动选择量化方法
        if model_format == "bf16":
            quant_method = "8bit"
        elif model_format == "gguf":
            quant_method = "gguf"
        elif model_format == "awq":
            quant_method = "awq"
        elif model_format == "fp8":
            quant_method = "fp8"
        else:
            quant_method = "4bit"  # 默认使用4位量化
    
    # 创建量化配置
    if quant_method == "4bit":
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_storage_dtype=torch.uint8
        )
        
    elif quant_method == "8bit":
        quantization_config = BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_skip_modules=["lm_head", "embed_tokens"],
            llm_int8_has_fp16_weight=False,
            llm_int8_threshold=6.0
        )
        
    elif quant_method == "awq":
        quantization_config = AwqConfig(
            bits=4,
            group_size=128,
            zero_point=True,
            version="gemm"
        )
        
    elif quant_method == "fp8":
        # FP8 量化配置
        model_kwargs.update({
            "torch_dtype": "auto"
        })
        quantization_config = None
        
    elif quant_method == "gptq":
        # GPTQ 配置
        model_kwargs.update({
            "revision": "gptq-4bit-32g-actorder_True"  # 或其他GPTQ版本
        })
        quantization_config = None
        
    elif quant_method == "gguf":
        # GGUF 格式需要特殊处理
        model_kwargs.update({
            "model_file": "*.gguf"  # 需要指定具体的GGUF文件
        })
        quantization_config = None
        
    else:
        quantization_config = None
    
    return quantization_config, model_kwargs, quant_method

def detect_model_format(model_path: str) -> str:
    """
    检测模型格式
    
    Args:
        model_path: 模型路径
        
    Returns:
        str: 模型格式 ["bf16", "gguf", "awq", "fp8", "unknown"]
    """
    if not os.path.exists(model_path):
        return "unknown"
    
    # 检查GGUF文件
    if any(file.endswith('.gguf') for file in os.listdir(model_path)):
        return "gguf"
    
    # 检查配置文件
    config_path = os.path.join(model_path, "config.json")
    if os.path.exists(config_path):
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # 检查量化配置
        if "quantization_config" in config:
            quant_config = config["quantization_config"]
            if quant_config.get("quant_method") == "awq":
                return "awq"
            elif quant_config.get("quant_method") == "gptq":
                return "gptq"
            elif quant_config.get("quant_method") == "fp8":
                return "fp8"
            elif quant_config.get("bits", 0) == 8:
                return "fp8"
        
        # 检查模型数据类型
        if config.get("torch_dtype") == "bfloat16":
            return "bf16"
    
    return "unknown"


# def parse_function_call(response_text: str) -> Optional[Dict]:
#     """解析函数调用响应"""
#     response_text = response_text.split("tool_call")[-1].strip()
#     try:

#         # 简单的函数调用解析逻辑
#         # 在实际应用中，您可能需要更复杂的解析


#         if "sql_query" in response_text.lower():
#             return extract_function_from_response(response_text)
                
#         return None
#     except Exception as e:
#         logger.error(f"解析函数调用失败: {e}")
#         return None