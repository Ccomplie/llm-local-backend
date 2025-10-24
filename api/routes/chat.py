"""
聊天对话API
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import asyncio
import logging

try:
    from model_service.model_manager import ModelManager
except ImportError:
    from model_service.simple_model_manager import SimpleModelManager as ModelManager

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str  # user, assistant, system
    content: str

class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[ChatMessage]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stream: bool = False

class ChatResponse(BaseModel):
    """聊天响应模型"""
    message: str
    usage: Dict[str, int]
    model: str

def get_model_manager() -> ModelManager:
    """获取模型管理器依赖"""
    from main import app
    return app.state.model_manager

@router.post("/chat", response_model=ChatResponse, summary="发送聊天消息")
async def chat_completion(
    request: ChatRequest,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """发送聊天消息并获取回复"""
    
    current_model = await model_manager.get_current_model()
    if not current_model:
        raise HTTPException(status_code=400, detail="没有加载的模型")
    
    try:
        # 构建提示词
        prompt = build_prompt(request.messages)
        
        # 生成参数
        generation_kwargs = {}
        if request.max_tokens:
            generation_kwargs["max_tokens"] = request.max_tokens
        if request.temperature:
            generation_kwargs["temperature"] = request.temperature
        if request.top_p:
            generation_kwargs["top_p"] = request.top_p
        
        # 生成回复
        response = await model_manager.generate_text(prompt, **generation_kwargs)
        
        return ChatResponse(
            message=response,
            usage={"prompt_tokens": len(prompt.split()), "completion_tokens": len(response.split())},
            model=await model_manager.get_current_model()
        )
        
    except Exception as e:
        logger.error(f"聊天生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")

@router.post("/chat/stream", summary="流式聊天")
async def chat_stream(
    request: ChatRequest,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """流式聊天接口"""
    
    current_model = await model_manager.get_current_model()
    if not current_model:
        raise HTTPException(status_code=400, detail="没有加载的模型")
    
    async def generate():
        try:
            # 构建提示词
            prompt = build_prompt(request.messages)
            
            # 生成参数
            generation_kwargs = {}
            if request.max_tokens:
                generation_kwargs["max_tokens"] = request.max_tokens
            if request.temperature:
                generation_kwargs["temperature"] = request.temperature
            if request.top_p:
                generation_kwargs["top_p"] = request.top_p
            
            # 流式生成
            async for token in model_manager.generate_stream(prompt, **generation_kwargs):
                data = {
                    "token": token,
                    "model": current_model
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            
            # 结束标记
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"流式生成失败: {e}")
            error_data = {"error": str(e)}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.websocket("/chat/ws")
async def chat_websocket(websocket: WebSocket):
    """WebSocket聊天接口"""
    await websocket.accept()
    
    try:
        # 获取模型管理器
        from main import app
        model_manager = app.state.model_manager
        
        current_model = await model_manager.get_current_model()
        if not current_model:
            await websocket.send_json({"error": "没有加载的模型"})
            await websocket.close()
            return
        
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "chat":
                messages = message_data.get("messages", [])
                
                try:
                    # 构建提示词
                    prompt = build_prompt(messages)
                    
                    # 流式生成并发送
                    async for token in model_manager.generate_stream(prompt):
                        await websocket.send_json({
                            "type": "token",
                            "token": token
                        })
                    
                    # 发送完成标记
                    await websocket.send_json({
                        "type": "complete"
                    })
                    
                except Exception as e:
                    logger.error(f"WebSocket生成失败: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e)
                    })
            
    except WebSocketDisconnect:
        logger.info("WebSocket连接断开")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        try:
            await websocket.close()
        except:
            pass

def build_prompt(messages: List[ChatMessage]) -> str:
    """构建提示词"""
    prompt_parts = []
    
    for message in messages:
        if message.role == "system":
            prompt_parts.append(f"System: {message.content}")
        elif message.role == "user":
            prompt_parts.append(f"Human: {message.content}")
        elif message.role == "assistant":
            prompt_parts.append(f"Assistant: {message.content}")
    
    prompt_parts.append("Assistant:")
    
    return "\n\n".join(prompt_parts)
