"""私人厨师 Agent：定义模型、工具、记忆和流式对话逻辑。"""

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_tavily import TavilySearch
from langgraph.checkpoint.sqlite import SqliteSaver

from app.common.logger import logger

# 加载 .env 中的环境变量（模型 Key、Tavily Key 等）
load_dotenv()

# ---------- 1. 工具：联网搜索 ----------
# Tavily 用于检索真实菜谱，API Key 自动从 TAVILY_API_KEY 环境变量读取
tavily = TavilySearch(
    max_results=5,      # 每次最多返回 5 条结果
    topic="general",    # 通用搜索
)

# ---------- 2. 模型：多模态 Qwen ----------
# qwen3-omni-flash 支持图片输入，能识别食材照片
model = init_chat_model(
    model="qwen3-omni-flash",
    model_provider="openai",
    # 接口地址优先从环境变量读取，没设置就用官方默认地址
    base_url=os.getenv(
        "DASHSCOPE_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ),
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    # 本机 httpx2 解压 brotli 响应有 bug，禁用压缩绕开
    default_headers={"Accept-Encoding": "identity"},
)

# ---------- 3. 记忆：SQLite 持久化 ----------
# 数据库放在项目根目录的 db 文件夹，不存在会自动创建
db_dir = Path(__file__).resolve().parents[2] / "db"
db_dir.mkdir(exist_ok=True)

# check_same_thread=False 允许多线程访问同一个连接
checkpointer = SqliteSaver(
    sqlite3.connect(db_dir / "personal_chief.db", check_same_thread=False)
)
# 自动建表
checkpointer.setup()

# ---------- 4. 系统提示词 ----------
# 规定 Agent 的四步工作流：识别食材 → 检索菜谱 → 打分排序 → 结构化输出
system_prompt = """
你是一名私人厨师。收到用户提供的食材照片或清单后，请按以下流程操作:
1.识别和评估食材:若用户提供照片，首先辨识所有可见食材。基于食材的外观状态，评估其新鲜度与可用量，整理出一份“当前可用食材清单”。
2.智能食谱检索:优先调用 web_search 工具，以“可用食材清单”为核心关键词，查找可行菜谱。
3.多维度评估与排序:从营养价值和制作难度两个维度对检索到的候选食谱进行量化打分，并根据得分排序，制作简单且营养丰富的排名靠前。
4.结构化方案输出:把排序后的食谱整理为一份结构清晰的建议报告，要包含食谱信息、得分、推荐理由、食谱的参考图片，帮助用户快速做出决策。

请严格按照流程，优先调用 web_search 工具搜索食谱，搜索不到的情况下才能自己发挥。
"""

# ---------- 5. 创建 Agent ----------
# create_agent 会把「模型 + 工具 + 记忆 + 提示词」组装成一个可循环调用的智能体
agent = create_agent(
    model=model,
    tools=[tavily],
    checkpointer=checkpointer,
    system_prompt=system_prompt,
)


# ---------- 6. 流式对话 ----------
async def search_recipes(prompt: str, image: str, thread_id: str):
    """调用 Agent 搜索食谱，逐段产出文字。

    参数:
        prompt: 用户文字输入
        image: 可选的图片 URL（空字符串表示没有图片）
        thread_id: 会话编号，用于隔离不同用户的对话
    返回:
        异步生成器，逐段产出模型回答
    """
    logger.info(f"[用户]: {prompt}, image: {image}, thread_id: {thread_id}")

    try:
        # 没有图片时用纯文本消息
        if not image or image.strip() == "":
            message = HumanMessage(content=prompt)
        else:
            # 有图片时按 OpenAI 兼容格式组装多模态消息
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image}},
                ]
            )

        # 流式调用 Agent：每生成一段文字就立即产出
        for chunk, metadata in agent.stream(
            {"messages": [message]},
            {"configurable": {"thread_id": thread_id}},
            stream_mode="messages",
        ):
            # 只输出 AI 回复的文本片段，忽略工具调用等中间消息
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                yield chunk.content

    except Exception as e:
        logger.error(f"\n[错误]: {str(e)}")
        yield "信息检索失败，试试看手动输入食物列表？"


# ---------- 7. 会话管理 ----------
def clear_messages(thread_id: str):
    """清空指定会话的全部历史。"""
    logger.info(f"清空历史消息，thread_id: {thread_id}")
    checkpointer.delete_thread(thread_id)


def get_messages(thread_id: str) -> list[dict[str, str]]:
    """查询指定会话的历史消息。

    返回:
        [{"role": "user"/"assistant", "content": "..."}]
    """
    logger.info(f"获取历史消息，thread_id: {thread_id}")

    # 按 thread_id 取出该会话的 checkpoint
    checkpoint = checkpointer.get({"configurable": {"thread_id": thread_id}})
    if not checkpoint:
        return []

    # 取出消息列表
    channel_values = checkpoint.get("channel_values")
    if not channel_values:
        return []

    messages = channel_values.get("messages", [])
    if not messages:
        return []

    # 转换成前端需要的格式，过滤空消息
    result = []
    for msg in messages:
        if not msg.content:
            continue

        if isinstance(msg, HumanMessage):
            result.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            result.append({"role": "assistant", "content": msg.content})

    return result
