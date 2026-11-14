"""对话接口：流式回答、查询历史、清空会话。"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agents.personal_chief_agent import (
    clear_messages,
    get_messages,
    search_recipes,
)
from app.models.schemas import ChatRequest

router = APIRouter()


@router.post("/chat/stream")
async def chat_endpoint(request: ChatRequest):
    """流式对话接口。

    接收用户消息（可带图片 URL），返回 SSE 流；
    前端可以边接收边显示，不用等完整回答生成完。
    """
    return StreamingResponse(
        search_recipes(request.message, request.image_url, request.thread_id),
        media_type="text/event-stream",
    )


@router.get("/chat/messages")
async def get_chat_messages(thread_id: str):
    """获取指定会话的历史消息。"""
    messages = get_messages(thread_id)
    return {"messages": messages}


@router.delete("/chat/messages")
async def clear_chat_messages(thread_id: str):
    """清空指定会话的历史消息。"""
    clear_messages(thread_id)
    return {"success": True}
