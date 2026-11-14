"""FastAPI 接口：把 RAG 问答能力封装为标准 REST API。

启动：
    uvicorn api:app --reload

接口文档：
    http://127.0.0.1:8000/docs

说明：
    这个文件和 app.py（Streamlit 界面）共用 core/ 下的同一套检索与生成逻辑，
    两种形态可以分别启动，互不影响。
"""

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.chain import answer_stream
from core.store import count

app = FastAPI(
    title="RAG Handbook API",
    description="企业员工手册知识库问答接口",
    version="1.0.0",
)


class AskRequest(BaseModel):
    """问答请求体。"""

    question: str          # 用户问题
    top_k: int = 4         # 检索条数，默认 4


@app.get("/health")
def health():
    """健康检查：返回服务状态和知识库条数。"""
    return {"status": "ok", "blocks": count()}


@app.post("/ask")
def ask(request: AskRequest):
    """非流式问答：一次性返回完整回答和引用出处。"""
    stream, docs = answer_stream(request.question, k=request.top_k)

    # 把生成器拼成完整文本
    answer_text = "".join(stream)

    # 只返回需要的元数据字段
    sources = [
        {
            "doc_name": doc.metadata.get("doc_name", "未知文档"),
            "chunk_index": doc.metadata.get("chunk_index", "?"),
        }
        for doc in docs
    ]

    return {"answer": answer_text, "sources": sources}


@app.post("/ask/stream")
def ask_stream(request: AskRequest):
    """流式问答：边生成边返回，适合前端实时显示。"""
    stream, _docs = answer_stream(request.question, k=request.top_k)
    return StreamingResponse(stream, media_type="text/plain; charset=utf-8")
