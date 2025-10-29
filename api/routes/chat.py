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
import time
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

# 新增：从不同类型的 chunk 中提取文本
def _extract_text_from_chunk(chunk: Any) -> str:
    """从 model_manager.generate_stream 的返回值中提取文本（兼容 str/dict/list）"""
    try:
        if chunk is None:
            return ""
        # 如果已经是字符串
        if isinstance(chunk, str):
            return chunk
        # 如果是字典，优先取常见字段
        if isinstance(chunk, dict):
            # 直接 token 字段
            if "token" in chunk and isinstance(chunk["token"], str):
                return chunk["token"]
            # message.content 结构
            if "message" in chunk and isinstance(chunk["message"], dict):
                return chunk["message"].get("content", "") or ""
            # content 字段
            if "content" in chunk and isinstance(chunk["content"], str):
                return chunk["content"]
            # choices -> delta/text
            if "choices" in chunk and isinstance(chunk["choices"], list):
                content = ""
                for c in chunk["choices"]:
                    if isinstance(c, dict):
                        delta = c.get("delta")
                        if isinstance(delta, dict) and isinstance(delta.get("content"), str):
                            content += delta.get("content", "")
                        else:
                            content += c.get("text", "") or (c.get("message") or {}).get("content", "") or ""
                return content
        # 如果是列表，尝试组合内部的 message.content
        if isinstance(chunk, list):
            pieces = []
            for item in chunk:
                pieces.append(_extract_text_from_chunk(item))
            return "".join(pieces)
    except Exception as e:
        logger.debug("提取 chunk 文本失败: %s", e)
    return ""

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


# @router.post("/chat/teststream", summary="流式聊天")
# async def stream_lines(
#     request: ChatRequest,
#     model_manager: ModelManager = Depends(get_model_manager)
# ):
#     """测试流式聊天接口，无需调用模型，只是模拟流式输出"""
#     lines = [
#         "第一行：流式传输开始...",
#         "第二行：数据正在实时传输",
#         "第三行：这是中间过程",
#         "第四行：传输进度 50%",
#         "第五行：即将完成传输",
#         "第六行：流式传输结束！"
#     ]
    
#     async def line_generator():
#         for i, line in enumerate(lines, 1):
#             # 每行之间有不同的延迟
#             await asyncio.sleep(1)
#             # 添加行号和时间戳
#             timestamp = time.strftime("%H:%M:%S")
#             yield f"[{timestamp}] 第{i}行: {line}\n"
    
#     return StreamingResponse(
#         line_generator(),
#         media_type="text/plain; charset=utf-8"
#     )


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
            async for chunk in model_manager.generate_stream(prompt, **generation_kwargs):
                text = _extract_text_from_chunk(chunk)
                if not text:
                    continue
                data = {
                    "token": text,
                    "model": current_model
                }
                # 以 SSE 格式发送统一 JSON
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            
            # 结束标记
            yield "data: {\"done\": true}\n\n"
            
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
            "X-Accel-Buffering": "no",  # <- 禁用代理缓冲，帮助流式数据实时到达客户端
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
                    async for chunk in model_manager.generate_stream(prompt):
                        text = _extract_text_from_chunk(chunk)
                        if not text:
                            continue
                        await websocket.send_json({
                            "type": "token",
                            "token": text,
                            "model": current_model
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


def build_prompt_sql(messages: List[ChatMessage]) -> str:
    """构建SQL提示词"""

    System_prompt = """
        角色设定
            你是一个专业的SQL专家，专门生成MySQL查询语句。现在需要针对MySQL官方employees数据库进行查询。
        数据库结构信息
        表清单和字段结构：
        1. employees（员工表）
            emp_no INT(11) PRIMARY KEY - 员工编号
            birth_date DATE - 出生日期
            first_name VARCHAR(14) - 名字
            last_name VARCHAR(16) - 姓氏
            hire_date DATE - 入职日期
        2. departments（部门表）
            dept_no CHAR(4) PRIMARY KEY - 部门编号
            dept_name VARCHAR(40) UNIQUE - 部门名称
        3. dept_emp（员工部门关联表）
            emp_no INT(11) - 员工编号
            dept_no CHAR(4) - 部门编号
            from_date DATE - 开始日期
            to_date DATE - 结束日期
                复合主键: (emp_no, dept_no)
        4. dept_manager（部门经理表）
            emp_no INT(11) - 员工编号
            dept_no CHAR(4) - 部门编号
            from_date DATE - 开始日期
            to_date DATE - 结束日期
                复合主键: (emp_no, dept_no)
        5. titles（职位历史表）
            emp_no INT(11) - 员工编号
            title VARCHAR(50) - 职位名称
            from_date DATE - 开始日期
            to_date DATE - 结束日期
                复合主键: (emp_no, title, from_date)
        6. salaries（薪资历史表）
            emp_no INT(11) - 员工编号
            salary INT(11) - 薪资数额
            from_date DATE - 开始日期
            to_date DATE - 结束日期
                复合主键: (emp_no, from_date)
        表关系说明
            employees ↔ dept_emp: 一对多关系
            employees ↔ dept_manager: 一对多关系
            employees ↔ titles: 一对多关系
            employees ↔ salaries: 一对多关系
            departments ↔ dept_emp: 一对多关系
            departments ↔ dept_manager: 一对多关系
        输出要求
            请根据我的查询需求，生成准确、优化的MySQL查询语句。只需要提供SQL代码，不需要解释。
        现在开始"""
    prompt_parts = []
    prompt_parts.append(f"System: {System_prompt}")
    for message in messages:
        if message.role == "system":
            prompt_parts.append(f"System: {message.content}")
        elif message.role == "user":
            prompt_parts.append(f"Human: {message.content}")
        elif message.role == "assistant":
            prompt_parts.append(f"Assistant: {message.content}")
    
    prompt_parts.append("Assistant:")
    
    return "\n\n".join(prompt_parts)