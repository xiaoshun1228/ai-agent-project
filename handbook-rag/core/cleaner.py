"""数据清洗：把脏文档清洗成干净文本。

清洗流水线（顺序不能乱）：
1. 统一换行符
2. 逐行过滤噪声：页码、目录点线、纯符号行
3. 合并多余空格与空行
4. 敏感信息脱敏：手机号 / 身份证 / 邮箱
5. 按行去重：基于内容 MD5 哈希
"""

import hashlib
import re
from dataclasses import dataclass


@dataclass
class CleanStats:
    """清洗统计，用于在界面上展示效果。"""

    total_lines: int = 0        # 原始总行数
    noise_lines: int = 0        # 被过滤掉的噪声行数
    blank_lines: int = 0        # 被压缩掉的空行数
    duplicate_lines: int = 0    # 被去重删掉的行数
    masked_items: int = 0       # 脱敏替换的敏感信息数量

    def summary(self) -> str:
        """返回一行便于展示的中文统计。"""
        return (
            f"共 {self.total_lines} 行，"
            f"过滤噪声 {self.noise_lines} 行，"
            f"压缩空行 {self.blank_lines} 行，"
            f"去重 {self.duplicate_lines} 行，"
            f"脱敏 {self.masked_items} 处"
        )


# ---------- 正则规则 ----------
# 页码行：如 "3"、"- 12 -"、"第 5 页"
PAGE_NUMBER = re.compile(r"^\s*[-—–]?\s*第?\s*\d+\s*页?\s*[-—–]?\s*$")

# 目录点线行：如 "第一章 总则 ........ 3"
TOC_LINE = re.compile(r"^\s*.{0,60}[.·…]{3,}\s*\d+\s*$")

# 纯符号行：如 "-----"、"***"
SYMBOL_ONLY = re.compile(r"^[\W_]+$")

# 连续空格 / 连续空行
MULTI_SPACE = re.compile(r"[ \t]+")
MULTI_BLANK = re.compile(r"\n{3,}")

# 敏感信息（用分组保留部分内容，便于核对）
# 手机号：保留前 3 位和后 4 位
PHONE = re.compile(r"(?<!\d)(1[3-9]\d)\d{4}(\d{4})(?!\d)")
# 身份证：保留前 6 位和后 4 位
ID_CARD = re.compile(r"(?<!\d)(\d{6})\d{8}(\d{3}[\dXx])(?!\d)")
# 邮箱：保留首字母和域名
EMAIL = re.compile(r"([\w.+-])[\w.+-]*(@[\w-]+\.[\w.]+)")


def mask_sensitive(text: str, stats: CleanStats) -> str:
    """敏感信息脱敏。

    手机号替换为 138****0000，身份证保留前 6 后 4，邮箱保留首字母。
    用 subn 拿到替换次数，累加到统计里。
    """
    # 逐个正则替换，subn 返回 (新文本, 替换次数)
    text, phone_count = PHONE.subn(r"\1****\2", text)
    text, id_count = ID_CARD.subn(r"\1********\2", text)
    text, email_count = EMAIL.subn(r"\1***\2", text)

    # 累计脱敏次数
    stats.masked_items += phone_count + id_count + email_count
    return text


def dedupe_lines(text: str, stats: CleanStats) -> str:
    """按行去重：内容完全相同的条款只保留第一次出现。

    用集合保存每行的 MD5 值，查询是 O(1)；
    这样不用反复比较整行文本，文档大时也不会慢。
    """
    seen_hashes: set[str] = set()  # 已出现过的行哈希
    kept: list[str] = []           # 保留的行

    for line in text.split("\n"):
        stripped = line.strip()

        # 空行原样保留，作为段落分隔
        if not stripped:
            kept.append("")
            continue

        # 计算这一行内容的 MD5 指纹
        digest = hashlib.md5(stripped.encode("utf-8")).hexdigest()

        # 指纹已存在说明是重复行，跳过并计数
        if digest in seen_hashes:
            stats.duplicate_lines += 1
            continue

        # 新出现的行，记下指纹并保留
        seen_hashes.add(digest)
        kept.append(line)

    return "\n".join(kept)


def clean_text(text: str) -> tuple[str, CleanStats]:
    """执行完整清洗流水线。

    参数:
        text: 原始文本
    返回:
        (清洗后文本, 统计信息)
    """
    stats = CleanStats()

    # 1. 统一换行符：Windows 的 \r\n 和 Mac 的 \r 都转成 \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. 逐行过滤噪声，同时把连续空行压缩成一个段落分隔
    lines = text.split("\n")
    stats.total_lines = len(lines)

    kept: list[str] = []          # 过滤后保留的行
    previous_blank = False        # 上一行是否为空行

    for line in lines:
        stripped = line.strip()

        # 空行：只保留一个，用于分隔段落
        if not stripped:
            stats.blank_lines += 1
            if not previous_blank:
                kept.append("")
            previous_blank = True
            continue

        previous_blank = False

        # 噪声行判断：页码、目录点线、纯符号
        if (
            PAGE_NUMBER.match(stripped)
            or TOC_LINE.match(stripped)
            or SYMBOL_ONLY.match(stripped)
        ):
            stats.noise_lines += 1
            continue

        # 正常行：把多个连续空格合并成一个
        kept.append(MULTI_SPACE.sub(" ", stripped))

    text = "\n".join(kept)

    # 3. 敏感信息脱敏
    text = mask_sensitive(text, stats)

    # 4. 空行压缩：3 个以上连续空行压成 1 个
    text = MULTI_BLANK.sub("\n\n", text).strip()

    # 5. 按行去重
    text = dedupe_lines(text, stats)

    return text, stats
