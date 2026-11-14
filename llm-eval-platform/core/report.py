"""报表：汇总统计、对比数据、CSV 导出。"""

import csv
import io

from core.metrics import (
    SCORE_KEYS,
    average_scores,
    group_by_model,
    group_by_task_type,
    human_vs_auto,
    trend_by_run,
)


def build_report(runs: list[dict], reviews: list[dict]) -> dict:
    """生成完整报表数据。"""
    return {
        "overall": average_scores(runs),               # 总体平均分
        "by_task_type": group_by_task_type(runs),      # 按评测类型
        "by_model": group_by_model(runs),              # 按模型
        "human_vs_auto": human_vs_auto(runs, reviews), # 人工 vs 自动
        "trend": trend_by_run(runs),                   # 趋势
    }


def export_csv(runs: list[dict]) -> str:
    """把评测结果导出为 CSV 字符串。"""
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow([
        "run_id", "case_id", "task_type", "model",
        "recall", "accuracy", "hallucination", "compliance",
        "latency", "status", "created_at",
    ])

    for run in runs:
        scores = run.get("scores") or {}
        writer.writerow([
            run["id"],
            run["case_id"],
            run["task_type"],
            run["model"],
            scores.get("recall", ""),
            scores.get("accuracy", ""),
            scores.get("hallucination", ""),
            scores.get("compliance", ""),
            run["latency"],
            run["status"],
            run["created_at"],
        ])

    return buffer.getvalue()


def compare_models(runs: list[dict]) -> dict[str, dict]:
    """模型对比：返回每个模型的四项平均分。"""
    result = group_by_model(runs)
    # 保证每项都有值，方便前端直接画图
    for model, scores in result.items():
        for key in SCORE_KEYS:
            scores.setdefault(key, 0.0)
    return result
