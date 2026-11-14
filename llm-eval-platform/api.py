"""FastAPI 接口：评测中台的后端 API。

启动：
    uvicorn api:app --reload

接口文档：
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse, RedirectResponse

from core.db import (
    add_case,
    add_review,
    delete_case,
    get_case,
    get_stats,
    init_db,
    list_cases,
    list_reviews,
    list_runs,
    update_case,
)
from core.models import CaseIn, ReviewIn, RunIn
from core.report import build_report, export_csv
from core.runner import run_batch

app = FastAPI(
    title="LLM 评测中台 API",
    description="轻量化大模型 RAG / Agent 自动化评测平台",
    version="1.0.0",
)

# 启动时初始化数据库
init_db()


@app.get("/", include_in_schema=False)
def root():
    """根路径跳转到接口文档。"""
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    """健康检查。"""
    return {"status": "ok", **get_stats()}


# ==================== 用例管理 ====================

@app.post("/cases")
def create_case(payload: CaseIn):
    """新增评测用例。"""
    case_id = add_case(
        task_type=payload.task_type,
        question=payload.question,
        expected_answer=payload.expected_answer,
        contexts=payload.contexts,
        expected_tools=payload.expected_tools,
    )
    return {"id": case_id, "message": "创建成功"}


@app.get("/cases")
def get_cases(task_type: str | None = None):
    """查询用例列表。"""
    return {"cases": list_cases(task_type=task_type)}


@app.get("/cases/{case_id}")
def get_case_detail(case_id: int):
    """查询单条用例。"""
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    return case


@app.delete("/cases/{case_id}")
def remove_case(case_id: int):
    """删除用例（软删除）。"""
    if not delete_case(case_id):
        raise HTTPException(status_code=404, detail="用例不存在")
    return {"message": "已删除"}


# ==================== 执行评测 ====================

@app.post("/run")
def execute(payload: RunIn):
    """批量执行评测，同步返回结果。"""
    if not payload.case_ids:
        raise HTTPException(status_code=400, detail="case_ids 不能为空")

    results = run_batch(payload.case_ids, model=payload.model)
    return {"count": len(results), "results": results}


@app.get("/runs")
def get_runs(task_type: str | None = None, limit: int = 200):
    """查询评测结果。"""
    return {"runs": list_runs(task_type=task_type, limit=limit)}


# ==================== 人工复核 ====================

@app.post("/reviews")
def submit_review(payload: ReviewIn):
    """提交人工复核打分。"""
    review_id = add_review(
        run_id=payload.run_id,
        reviewer=payload.reviewer,
        human_scores=payload.human_scores,
        comment=payload.comment,
    )
    return {"id": review_id, "message": "复核已记录"}


@app.get("/reviews")
def get_reviews(run_id: int | None = None):
    """查询复核记录。"""
    return {"reviews": list_reviews(run_id=run_id)}


# ==================== 报表 ====================

@app.get("/report")
def get_report(task_type: str | None = None):
    """获取汇总报表。"""
    runs = list_runs(task_type=task_type, limit=1000)
    reviews = list_reviews(limit=1000)
    return build_report(runs, reviews)


@app.get("/export.csv", response_class=PlainTextResponse)
def export(task_type: str | None = None):
    """导出评测结果 CSV。"""
    runs = list_runs(task_type=task_type, limit=1000)
    return export_csv(runs)
