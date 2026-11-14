"""批量评测调度：按用例逐个执行并保存结果。"""

from core.db import add_run, get_case
from core.evaluators import evaluate_case


def run_batch(case_ids: list[int], model: str = "qwen-plus",
              progress_callback=None) -> list[dict]:
    """批量执行评测。

    参数:
        case_ids: 用例 ID 列表
        model: 被测模型名
        progress_callback: 可选回调，签名 (done, total, result)
    返回:
        本次所有评测结果列表
    """
    results = []
    total = len(case_ids)

    for index, case_id in enumerate(case_ids, start=1):
        case = get_case(case_id)

        # 用例不存在或已删除时跳过
        if not case or case["status"] != "active":
            continue

        result = evaluate_case(case, model)

        # 写入数据库
        run_id = add_run(
            case_id=case_id,
            task_type=case["task_type"],
            model=model,
            pred_answer=result["pred_answer"],
            tool_calls=result["tool_calls"],
            scores=result["scores"],
            latency=result["latency"],
            status=result["status"],
            error=result["error"],
        )

        record = {
            "run_id": run_id,
            "case_id": case_id,
            "task_type": case["task_type"],
            "question": case["question"],
            **result,
        }
        results.append(record)

        # 通知界面更新进度
        if progress_callback:
            progress_callback(index, total, record)

    return results
