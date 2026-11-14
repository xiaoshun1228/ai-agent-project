"""D2 验证脚本：清洗 -> 分块 -> 写入 Chroma -> 检索。

运行前请确认 .env 中已配置 DASHSCOPE_API_KEY。
    python -X utf8 demo_index.py
"""

from core.cleaner import clean_text
from core.loader import load_file
from core.splitter import split_document
from core.store import add_chunks, clear, count, search


def main() -> None:
    document = load_file("data/员工手册_示例.txt")
    cleaned_text, stats = clean_text(document.text)
    print("清洗完成：", stats.summary())

    chunks = split_document(cleaned_text, document.name)
    print(f"分块完成：共 {len(chunks)} 块")
    for chunk in chunks:
        preview = chunk.text[:40].replace("\n", " ")
        print(f"  [{chunk.index}] {preview}...")

    clear()
    added = add_chunks(chunks)
    print(f"入库完成：{added} 条，当前库中共 {count()} 条")

    question = "出差报销需要多久内提交？"
    print(f"\n检索问题：{question}")
    for doc, score in search(question, k=3):
        print(f"  score={score:.4f}  [{doc.metadata['doc_name']}#{doc.metadata['chunk_index']}]")
        print(f"    {doc.page_content[:80]}")


if __name__ == "__main__":
    main()
