"""文档读取：把 txt / md / pdf 文件读成纯文本。"""

from dataclasses import dataclass
from pathlib import Path

# 支持的文件类型（小写后缀）
SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf"}


@dataclass
class Document:
    """一份原始文档。"""

    name: str      # 文件名（不含扩展名），用作展示名
    text: str      # 原始文本内容
    source: str    # 完整路径，便于追溯来源


def load_file(path: str | Path) -> Document:
    """读取单个文档文件。

    参数:
        path: 文件路径
    返回:
        Document 对象（文件名、正文、路径）
    异常:
        ValueError: 文件类型不支持时抛出
    """
    file_path = Path(path)
    suffix = file_path.suffix.lower()  # 取扩展名并统一小写

    # 类型检查：不支持的格式直接拒绝
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"不支持的文件类型：{suffix}，仅支持 {SUPPORTED_SUFFIXES}")

    # PDF 需要专门的解析库，其他格式按 UTF-8 直接读
    if suffix == ".pdf":
        text = _read_pdf(file_path)
    else:
        # errors="ignore" 防止个别乱码字符导致整个文件读取失败
        text = file_path.read_text(encoding="utf-8", errors="ignore")

    return Document(name=file_path.stem, text=text, source=str(file_path))


def load_folder(folder: str | Path) -> list[Document]:
    """读取文件夹下所有支持的文档。

    参数:
        folder: 文件夹路径
    返回:
        Document 列表，按文件名排序，保证每次顺序一致
    """
    documents = []
    # sorted 保证读取顺序稳定，便于复现
    for path in sorted(Path(folder).iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            documents.append(load_file(path))
    return documents


def read_uploaded(name: str, data: bytes) -> str:
    """读取 Streamlit 上传的文件内容（bytes）为纯文本。

    参数:
        name: 上传文件的原始文件名（用来判断类型）
        data: 文件二进制内容
    返回:
        纯文本字符串
    """
    suffix = Path(name).suffix.lower()

    if suffix == ".pdf":
        from io import BytesIO

        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ImportError("读取 PDF 请先安装：pip install pypdf") from exc

        # 从内存字节流解析 PDF，不需要先落盘
        reader = PdfReader(BytesIO(data))
        # 逐页提取文字，用换行拼接
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    # txt / md 直接按 UTF-8 解码
    return data.decode("utf-8", errors="ignore")


def _read_pdf(path: Path) -> str:
    """读取本地 PDF 文件的文字内容。

    参数:
        path: PDF 文件路径
    返回:
        PDF 全部页面的文字，按换行拼接
    """
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ImportError("读取 PDF 请先安装：pip install pypdf") from exc

    # 打开 PDF，逐页提取文字；提取不到时返回空字符串
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
