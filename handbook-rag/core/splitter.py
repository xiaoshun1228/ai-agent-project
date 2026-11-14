"""文本分块：把清洗后的长文本切成适合检索的小块。

为什么要重叠（overlap）：
分块点可能落在一句话中间，相邻块共享一段边界文本，
避免关键信息被切断后检索不到。
"""

from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

# 默认每块 300 字，相邻块重叠 50 字
DEFAULT_CHUNK_SIZE = 300
DEFAULT_CHUNK_OVERLAP = 50

# 中文优先的切分顺序：
# 先按空行（段落），再按换行，然后按句号/问号/分号/逗号，最后退化到单个字符
SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]


@dataclass
class Chunk:
    """一个文本块。"""

    text: str        # 块内容
    doc_name: str    # 来自哪份文档
    index: int       # 在该文档中的序号（从 0 开始）


def split_document(
    text: str,
    doc_name: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    """把一份文档切成若干文本块。

    参数:
        text: 清洗后的文档文本
        doc_name: 文档名，会写进每个块的元数据
        chunk_size: 每块最大字符数
        chunk_overlap: 相邻块重叠字符数
    返回:
        Chunk 列表
    """
    # RecursiveCharacterTextSplitter 会按 separators 的顺序
    # 优先在语义边界（段落、句子）处切分
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=SEPARATORS,
        length_function=len,  # 按字符数计算长度（中文友好）
    )

    # 执行切分，得到若干字符串
    pieces = splitter.split_text(text)

    # 去掉首尾空白，并过滤掉空块
    return [
        Chunk(text=piece.strip(), doc_name=doc_name, index=i)
        for i, piece in enumerate(pieces)
        if piece.strip()
    ]
