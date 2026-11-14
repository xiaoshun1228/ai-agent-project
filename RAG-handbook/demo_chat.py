"""D3 验证脚本：检索问答链 + 流式输出 + 引用来源。

运行：
    python -X utf8 demo_chat.py
"""

from core.chain import answer_stream
from core.cleaner import clean_text
from core.loader import load_file
from core.splitter import split_document
from core.store import add_chunks, count


def ensure_index() -> None:
    """库为空时自动导入示例文档。"""
    if count() > 0:
        print(f"向量库已有 {count()} 条")
        return

    document = load_file("data/员工手册_示例.txt")
    cleaned_text, _ = clean_text(document.text)
    chunks = split_document(cleaned_text, document.name)
    add_chunks(chunks)
    print(f"向量库为空，已导入 {len(chunks)} 条")


def ask(question: str) -> None:
    print(f"\n问：{question}")
    print("答：", end="")

    stream, docs = answer_stream(question)
    for piece in stream:
        print(piece, end="", flush=True)

    print("\n引用：", end="")
    for doc in docs[:3]:
        print(f"[{doc.metadata['doc_name']}#{doc.metadata['chunk_index']}] ", end="")
    print()


def main() -> None:
    ensure_index()

    # 前两个问题手册里有答案，第三个故意问手册里没有的内容，检验是否编造
    ask("出差报销需要多久内提交？")
    ask("迟到多久算旷工？")
    ask("公司年假有几天？")


if __name__ == "__main__":
    main()
