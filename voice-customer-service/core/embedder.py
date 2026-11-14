"""向量化：把文本块转换成向量。

使用阿里云 DashScope 的 text-embedding-v4 模型，
它把一段文字编码成一串数字（向量），语义相近的文字向量也相近。
"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_community.embeddings import DashScopeEmbeddings

# 读取 .env 中的配置（DASHSCOPE_API_KEY 等）
load_dotenv()

# 使用的向量模型名
EMBEDDING_MODEL = "text-embedding-v4"


@lru_cache(maxsize=1)
def get_embeddings() -> DashScopeEmbeddings:
    """返回全局唯一的向量化对象。

    用 lru_cache 缓存，避免每次调用都重新创建客户端。
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")

    # 没有 Key 时尽早报错，避免后面调用时才失败
    if not api_key:
        raise RuntimeError("缺少 DASHSCOPE_API_KEY，请在 .env 文件中配置")

    return DashScopeEmbeddings(
        model=EMBEDDING_MODEL,
        dashscope_api_key=api_key,
    )
