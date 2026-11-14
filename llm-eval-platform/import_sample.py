"""把示例用例导入数据库。

运行：
    python import_sample.py
"""

import json

from core.config import DATA_DIR
from core.db import add_case, init_db, list_cases


def main() -> None:
    init_db()

    # 已有用例时跳过，避免重复导入
    if list_cases():
        print("数据库中已有用例，跳过导入")
        return

    sample_file = DATA_DIR / "sample_cases.json"
    data = json.loads(sample_file.read_text(encoding="utf-8"))

    for case in data["cases"]:
        add_case(
            task_type=case["task_type"],
            question=case["question"],
            expected_answer=case.get("expected_answer", ""),
            contexts=case.get("contexts", []),
            expected_tools=case.get("expected_tools", []),
        )

    print(f"已导入 {len(data['cases'])} 条示例用例")


if __name__ == "__main__":
    main()
