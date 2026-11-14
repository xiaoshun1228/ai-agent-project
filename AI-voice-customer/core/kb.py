"""FAQ 知识库：加载问答对、清洗、写入向量库。"""

import re

from core.cleaner import clean_text
from core.config import DATA_DIR
from core.splitter import Chunk
from core.store import add_chunks, count

# FAQ 文件位置
FAQ_FILE = DATA_DIR / "faq.txt"


def load_pairs(text: str) -> list[str]:
    """把 FAQ 文本按「Q:」切分成一条条问答。

    参数:
        text: 原始 FAQ 文本
    返回:
        每条问答的字符串列表
    """
    # 先复用清洗流水线，去掉多余空行和噪声
    cleaned_text, _ = clean_text(text)

    # 每个以 Q: 开头的行视为一条新问答
    pairs = re.split(r"\n(?=Q\s*[:：])", cleaned_text)
    return [pair.strip() for pair in pairs if pair.strip()]


def init_kb(force: bool = False) -> int:
    """初始化 FAQ 知识库。

    参数:
        force: 为 True 时先清空再导入
    返回:
        当前知识库条目数
    """
    # 已有数据且不强制重建时，直接返回
    if count() > 0 and not force:
        return count()

    text = FAQ_FILE.read_text(encoding="utf-8")
    pairs = load_pairs(text)

    # 每条问答作为一个独立文本块，不需要再切分
    chunks = [
        Chunk(text=pair, doc_name="FAQ", index=i)
        for i, pair in enumerate(pairs)
    ]
    add_chunks(chunks)
    return len(chunks)
