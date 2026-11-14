"""D1 验证脚本：读取示例文档 -> 清洗 -> 打印前后对比与统计。

运行：
    python -X utf8 demo_clean.py
"""

from core.cleaner import clean_text
from core.loader import load_file


def main() -> None:
    document = load_file("data/员工手册_示例.txt")

    print("=" * 60)
    print("原始文本")
    print("=" * 60)
    print(document.text)

    cleaned_text, stats = clean_text(document.text)

    print("=" * 60)
    print("清洗后文本")
    print("=" * 60)
    print(cleaned_text)

    print("=" * 60)
    print("清洗统计：", stats.summary())
    print("=" * 60)


if __name__ == "__main__":
    main()
