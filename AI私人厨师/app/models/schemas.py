"""请求数据模型：定义接口接收的 JSON 结构。"""

from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """对话接口的请求体。

    字段:
        message: 用户输入的文字内容
        image_url: 可选的图片直链（供多模态模型识别食材）
        thread_id: 会话编号，同一编号共享上下文
    """

    message: str
    image_url: Optional[str] = None
    thread_id: str
