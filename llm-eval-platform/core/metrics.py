"""指标聚合与对比：把多条评测结果汇总成报表数据。"""

SCORE_KEYS = ("recall", "accuracy", "hallucination", "compliance")

# 指标中文名
SCORE_LABELS = {
    "recall": "召回率",
    "accuracy": "准确率",
    "hallucination": "幻觉率",
    "compliance": "合规率",
}


def average_scores(runs: list[dict]) -> dict:
    """计算一批评测结果的平均分。

    只统计成功执行的记录。
    """
    valid = [r for r in runs if r.get("status") == "success" and r.get("scores")]
    if not valid:
        return {key: 0.0 for key in SCORE_KEYS} | {"count": 0}

    result = {}
    for key in SCORE_KEYS:
        values = [float(r["scores"].get(key, 0)) for r in valid]
        result[key] = round(sum(values) / len(values), 4)

    result["count"] = len(valid)
    return result


def group_by_task_type(runs: list[dict]) -> dict[str, dict]:
    """按评测类型分组统计平均分。

    返回:
        {"rag": {...}, "agent": {...}, "compliance": {...}}
    """
    groups: dict[str, list[dict]] = {}
    for run in runs:
        groups.setdefault(run["task_type"], []).append(run)

    return {task_type: average_scores(items) for task_type, items in groups.items()}


def group_by_model(runs: list[dict]) -> dict[str, dict]:
    """按模型分组统计平均分，用于多模型对比。"""
    groups: dict[str, list[dict]] = {}
    for run in runs:
        groups.setdefault(run["model"], []).append(run)

    return {model: average_scores(items) for model, items in groups.items()}


def human_vs_auto(runs: list[dict], reviews: list[dict]) -> dict:
    """自动评分与人工评分的对比。

    只统计有复核记录的评测。
    """
    # 建 run_id -> 人工分数 的映射（多条取最新一条）
    review_map = {}
    for review in reviews:
        review_map[review["run_id"]] = review["human_scores"]

    auto_values = {key: [] for key in SCORE_KEYS}
    human_values = {key: [] for key in SCORE_KEYS}

    for run in runs:
        human = review_map.get(run["id"])
        if not human or not run.get("scores"):
            continue

        for key in SCORE_KEYS:
            if key in human:
                auto_values[key].append(float(run["scores"].get(key, 0)))
                human_values[key].append(float(human[key]))

    def mean(values: list[float]) -> float:
        return round(sum(values) / len(values), 4) if values else 0.0

    return {
        "count": len([v for v in auto_values["accuracy"]]),
        "auto": {key: mean(auto_values[key]) for key in SCORE_KEYS},
        "human": {key: mean(human_values[key]) for key in SCORE_KEYS},
    }


def trend_by_run(runs: list[dict]) -> list[dict]:
    """按时间顺序输出每次评测的综合分，用于趋势图。"""
    ordered = sorted(runs, key=lambda r: r["id"])
    trend = []
    for run in ordered:
        scores = run.get("scores") or {}
        if not scores:
            continue
        # 综合分 = 四项平均（幻觉率取反，越低越好）
        composite = (
            scores.get("recall", 0)
            + scores.get("accuracy", 0)
            + (1 - scores.get("hallucination", 0))
            + scores.get("compliance", 0)
        ) / 4
        trend.append({
            "run_id": run["id"],
            "task_type": run["task_type"],
            "composite": round(composite, 4),
        })
    return trend
