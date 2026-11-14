"""客服对话：检索 FAQ + 调用 Qwen 生成回答。"""

from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from core.config import CHAT_MODEL, DASHSCOPE_API_KEY
from core.store import search

# 客服人设：语气亲切，回答简短，适合语音播报
SYSTEM_TEMPLATE = """你是「智选商城」的智能客服小助手，语气亲切、专业、简洁。

回答规则（必须严格遵守）：
1. 回答内容必须完全来自下面的「常见问题资料」，不得添加资料以外的任何信息。
2. 如果资料中找不到答案，只能回答：「抱歉，这个问题我暂时查不到，建议您转接人工客服。」
3. 严禁推测或编造公司地址、电话、价格、政策等资料中没有的内容。
4. 回答控制在三句话以内，适合语音播报。
5. 不要使用表情符号、星号、井号等特殊符号。

常见问题资料：
{context}"""

PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_TEMPLATE),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)


def get_llm(streaming: bool = True) -> ChatTongyi:
    """创建 Qwen 模型对象。"""
    return ChatTongyi(
        model=CHAT_MODEL,
        dashscope_api_key=DASHSCOPE_API_KEY,
        streaming=streaming,
        temperature=0.1,
    )


def build_context(docs) -> str:
    """把检索到的 FAQ 拼成一段参考资料。"""
    return "\n\n".join(doc.page_content for doc in docs)


def to_messages(history):
    """把界面历史消息转换成 LangChain 消息，保留最近 6 条。"""
    messages = []
    for item in (history or [])[-6:]:
        if item.get("role") == "user":
            messages.append(HumanMessage(content=item.get("content", "")))
        else:
            messages.append(AIMessage(content=item.get("content", "")))
    return messages


def answer_stream(question: str, k: int = 3, history=None):
    """流式生成客服回答。

    返回:
        (文本片段生成器, 检索到的 FAQ 列表)
    """
    # 1. 检索相关 FAQ
    results = search(question, k=k)
    docs = [doc for doc, _score in results]

    # 2. 拼装参考资料
    context = build_context(docs)

    # 3. 组装链并流式调用
    chain = PROMPT | get_llm(streaming=True) | StrOutputParser()
    stream = chain.stream(
        {
            "context": context,
            "question": question,
            "history": to_messages(history),
        }
    )
    return stream, docs
