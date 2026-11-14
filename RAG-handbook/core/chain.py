"""检索问答链：检索 -> 拼装 Prompt -> 调用大模型 -> 流式输出。

链路数据流：
    question
      -> 向量检索 top-k 文本块
      -> 拼装成 context
      -> ChatPromptTemplate（system 里放 context）
      -> Qwen 生成
      -> StrOutputParser 转纯文本
"""

import os

from dotenv import load_dotenv
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from core.store import search

# 读取 .env 配置
load_dotenv()

# 生成模型（可被环境变量 CHAT_MODEL 覆盖）
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen-plus")

# 系统提示词：限定模型只能依据参考资料回答
SYSTEM_TEMPLATE = """你是企业员工手册智能助手，请严格依据下面的参考资料回答用户问题。

规则：
1. 只使用参考资料中的信息，不要编造。
2. 如果参考资料中没有答案，直接回答「手册中未找到相关内容」。
3. 回答简洁准确，尽量注明条款编号。
4. 内容较多时用分点列出。

参考资料：
{context}"""

# 消息模板：
# system 里放参考资料，history 放历史对话，human 放本次问题
PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_TEMPLATE),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)


def get_llm(streaming: bool = True) -> ChatTongyi:
    """创建 Qwen 模型对象。

    temperature 调低（0.1），减少模型自由发挥，降低胡编概率。
    """
    return ChatTongyi(
        model=CHAT_MODEL,
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
        streaming=streaming,
        temperature=0.1,
    )


def build_context(docs) -> str:
    """把检索到的文本块拼成带来源标记的上下文。

    每块前面加上【文档名#序号】，方便模型引用、也方便界面展示出处。
    """
    parts = []
    for doc in docs:
        name = doc.metadata.get("doc_name", "未知文档")
        index = doc.metadata.get("chunk_index", "?")
        parts.append(f"【{name}#{index}】\n{doc.page_content}")

    # 块与块之间空一行，便于模型区分
    return "\n\n".join(parts)


def to_messages(history):
    """把界面的消息列表转换成 LangChain 消息对象。

    只保留最近 6 条，避免上下文过长导致 token 超限。
    """
    messages = []
    for item in (history or [])[-6:]:
        content = item.get("content", "")
        if item.get("role") == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))
    return messages


def answer_stream(question: str, k: int = 4, history=None):
    """流式回答。

    参数:
        question: 用户问题
        k: 检索条数
        history: 历史对话列表（可选）
    返回:
        (文本片段生成器, 引用来源列表)
    """
    # 1. 检索相关文本块
    results = search(question, k=k)
    docs = [doc for doc, _score in results]

    # 2. 拼装上下文
    context = build_context(docs)

    # 3. 组装链：Prompt -> 模型 -> 纯文本解析
    chain = PROMPT | get_llm(streaming=True) | StrOutputParser()

    # 4. 流式调用，逐段产出文字
    stream = chain.stream(
        {
            "context": context,
            "question": question,
            "history": to_messages(history),
        }
    )
    return stream, docs


def answer(question: str, k: int = 4, history=None) -> tuple[str, list]:
    """非流式回答，一次性拿到完整文本。

    参数/返回同 answer_stream，但文本是拼接好的完整字符串。
    """
    stream, docs = answer_stream(question, k=k, history=history)
    return "".join(stream), docs
