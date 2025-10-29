"""
Ollama 模型管理器（重写）
- 使用 httpx.AsyncClient 实现真正的异步/流式请求
- 提供 generate_text(prompt, ...) 和 generate_stream(prompt, ...) 两个对外接口，兼容项目中调用
- 更稳健地解析 Ollama 返回的流（SSE 或逐行 JSON）
"""

from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio
import json
from loguru import logger
import httpx

try:
    from config.settings import Settings
except Exception:
    # 保证在没有 Settings 时也能导入（根据项目实际情况可删除）
    class Settings:
        OLLAMA_URL = "http://127.0.0.1:11434"


class OllamaManager:
    """Ollama 模型管理器（异步实现）"""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        # 支持通过 Settings 指定地址，否则使用默认
        self.ollama_url = getattr(self.settings, "OLLAMA_URL", "http://127.0.0.1:11434")
        self.current_model: Optional[str] = None
        self.available_models: List[str] = []
        self._client: Optional[httpx.AsyncClient] = None
        self._init_lock = asyncio.Lock()

    async def _ensure_client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=None)  # 流式时需要 None 超时

    async def initialize(self):
        """初始化管理器并加载模型列表"""
        async with self._init_lock:
            await self._ensure_client()
            logger.info("初始化 OllamaManager，地址: {}", self.ollama_url)
            try:
                await self._load_available_models()
                if self.available_models:
                    self.current_model = self.available_models[0]
                    logger.info("默认模型设置为: {}", self.current_model)
                logger.info("OllamaManager 初始化完成")
            except Exception as e:
                logger.error("初始化 OllamaManager 失败: {}", e)
                raise

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _load_available_models(self):
        """尝试加载 Ollama 中可用的模型列表，兼容不同接口返回格式"""
        await self._ensure_client()
        endpoints = ["/api/models", "/api/tags", "/models"]
        models: List[str] = []
        for ep in endpoints:
            try:
                url = f"{self.ollama_url}{ep}"
                resp = await self._client.get(url, timeout=10.0)
                if resp.status_code != 200:
                    continue
                try:
                    data = resp.json()
                except Exception:
                    # 有些接口返回纯文本列表
                    text = resp.text.strip()
                    if text:
                        # 尝试按行拆分
                        models = [line.strip() for line in text.splitlines() if line.strip()]
                        break
                    continue

                # 尝试解析常见结构
                if isinstance(data, dict):
                    # Ollama /api/models 可能返回 {"models": [{"name": "...", ...}, ...]}
                    if "models" in data and isinstance(data["models"], list):
                        for m in data["models"]:
                            if isinstance(m, dict) and "name" in m:
                                models.append(m["name"])
                            elif isinstance(m, str):
                                models.append(m)
                        if models:
                            break
                    # 有时直接是 {"name": "..."} 或 {"tags": [...]}
                    if "name" in data and isinstance(data["name"], str):
                        models.append(data["name"])
                        break
                    if "tags" in data and isinstance(data["tags"], list):
                        for t in data["tags"]:
                            if isinstance(t, str):
                                models.append(t)
                        if models:
                            break
                elif isinstance(data, list):
                    # 直接列表
                    for item in data:
                        if isinstance(item, dict) and "name" in item:
                            models.append(item["name"])
                        elif isinstance(item, str):
                            models.append(item)
                    if models:
                        break
            except Exception as e:
                logger.debug("尝试从 {} 获取模型列表失败: {}", ep, e)
                continue

        self.available_models = models
        logger.info("发现 Ollama 模型: {}", self.available_models)

    async def get_available_models(self) -> List[str]:
        return self.available_models.copy()

    async def get_current_model(self) -> Optional[str]:
        return self.current_model

    async def switch_model(self, model_name: str) -> bool:
        if model_name in self.available_models:
            self.current_model = model_name
            logger.info("已切换到模型: {}", model_name)
            return True
        logger.error("模型不存在: {}", model_name)
        return False

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        非流式生成文本（返回完整字符串）
        返回 string（response message）
        """
        if not self.current_model:
            raise ValueError("没有设置当前模型")
        await self._ensure_client()

        messages = [{"role": "user", "content": prompt}]
        payload = {
            "model": self.current_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
                "max_tokens": kwargs.get("max_tokens", 2048),
            }
        }
        # 合并外部 options
        if "options" in kwargs and isinstance(kwargs["options"], dict):
            payload["options"].update(kwargs["options"])

        url = f"{self.ollama_url}/api/chat"
        resp = await self._client.post(url, json=payload, timeout=60.0)
        resp.raise_for_status()
        try:
            data = resp.json()
        except Exception:
            # 如果不是 JSON，返回文本
            return resp.text

        # 兼容不同返回结构
        if isinstance(data, dict):
            # 常见：{"message": {"content": "..."}, ...}
            if "message" in data and isinstance(data["message"], dict):
                return data["message"].get("content", "")
            # 或者直接 content 字段
            if "content" in data:
                return data.get("content", "")
            # 或者 choices -> first -> text
            if "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0:
                first = data["choices"][0]
                if isinstance(first, dict):
                    return first.get("text") or first.get("message", {}).get("content", "") or ""
        return ""

    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        流式生成接口
        返回一个异步生成器，逐步 yield 字符串 chunk（文本增量）
        """
        if not self.current_model:
            raise ValueError("没有设置当前模型")
        await self._ensure_client()

        messages = [{"role": "user", "content": prompt}]
        payload = {
            "model": self.current_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
                "max_tokens": kwargs.get("max_tokens", 2048),
            }
        }
        if "options" in kwargs and isinstance(kwargs["options"], dict):
            payload["options"].update(kwargs["options"])

        url = f"{self.ollama_url}/api/chat"

        # 使用 httpx 的 stream 接口逐行读取
        try:
            async with self._client.stream("POST", url, json=payload, timeout=None) as resp:
                resp.raise_for_status()
                # aiter_lines 支持按行异步迭代，兼容 SSE 或逐行 JSON
                async for raw_line in resp.aiter_lines():
                    if not raw_line:
                        continue
                    line = raw_line.strip()
                    # 支持 SSE 前缀 "data: "
                    if line.startswith("data: "):
                        line = line[6:]
                    # 跳过 DONE 标记（有些实现）
                    if line in ("[DONE]", "[done]"):
                        break
                    # 尝试解析 JSON
                    parsed = None
                    try:
                        parsed = json.loads(line)
                    except Exception:
                        # 如果不是 JSON，则直接作为文本 chunk 返回
                        # 例如有些实现直接返回纯文本 token
                        yield {"token": line, "model": self.current_model}
                        continue

                    # parsed 为 dict 或列表，尝试提取内容
                    content = ""
                    if isinstance(parsed, dict):
                        # 完成标记
                        if parsed.get("done", False):
                            break
                        # 常见 message.content
                        msg = parsed.get("message")
                        if isinstance(msg, dict):
                            content = msg.get("content", "") or content
                        # 直接 content 字段
                        if not content and parsed.get("content"):
                            content = parsed.get("content")
                        # choices 结构（delta/text）
                        if not content and "choices" in parsed and isinstance(parsed["choices"], list):
                            for c in parsed["choices"]:
                                if isinstance(c, dict):
                                    content_part = None
                                    delta = c.get("delta")
                                    if isinstance(delta, dict):
                                        content_part = delta.get("content")
                                    if content_part is None:
                                        content_part = c.get("text") or (c.get("message") or {}).get("content") or ""
                                    if content_part:
                                        content += content_part
                        # results 结构
                        if not content and "results" in parsed and isinstance(parsed["results"], list):
                            for r in parsed["results"]:
                                if isinstance(r, dict) and isinstance(r.get("message"), dict):
                                    content += r["message"].get("content", "")
                    elif isinstance(parsed, list):
                        # 列表中可能包含 message 部分
                        for item in parsed:
                            if isinstance(item, dict):
                                if item.get("done", False):
                                    return
                                if isinstance(item.get("message"), dict):
                                    content += item["message"].get("content", "") or ""
                    # 如果提取到内容则 yield（统一为 dict）
                    if content:
                        yield {"token": content, "model": self.current_model}

        except Exception as e:
            logger.error("Ollama 流式请求出错: {}", e)
            # 将错误以异常抛出，调用方可捕获并回退到非流式逻辑
            raise
