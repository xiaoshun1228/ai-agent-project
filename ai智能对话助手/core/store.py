"""Chroma 向量库：负责向量入库、检索、清空。"""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from core.embedder import get_embeddings

# 向量库持久化目录（项目根目录下的 chroma_db）
PERSIST_DIR = Path(__file__).resolve().parents[1] / "chroma_db"

# 集合名，相当于数据库里的"表"
COLLECTION_NAME = "faq"


def get_vector_store() -> Chroma:
    """打开（或创建）本地向量库。

    每次调用都会连接到同一个磁盘目录，数据不会丢。
    """
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),  # 告诉 Chroma 用哪个模型做向量化
        persist_directory=str(PERSIST_DIR),
    )


def add_chunks(chunks) -> int:
    """把文本块写入向量库。

    参数:
        chunks: Chunk 列表
    返回:
        实际写入的条数
    """
    # 把自定义的 Chunk 转成 LangChain 的 Document（正文 + 元数据）
    documents = [
        Document(
            page_content=chunk.text,
            metadata={
                "doc_name": chunk.doc_name,   # 来源文档名，用于展示引用
                "chunk_index": chunk.index,   # 块序号
            },
        )
        for chunk in chunks
    ]

    store = get_vector_store()
    store.add_documents(documents)  # 自动调用 embedding 并写入
    return len(documents)


def search(query: str, k: int = 4) -> list[tuple[Document, float]]:
    """语义检索最相关的 k 个文本块。

    参数:
        query: 用户问题
        k: 返回条数
    返回:
        [(文档块, 距离分数)]，分数越小表示越相关
    """
    store = get_vector_store()
    return store.similarity_search_with_score(query, k=k)


def count() -> int:
    """当前库中文本块数量。"""
    return len(get_vector_store().get()["ids"])


def clear() -> None:
    """清空向量库（删除全部文本块）。"""
    store = get_vector_store()
    ids = store.get()["ids"]
    if ids:
        store.delete(ids)
