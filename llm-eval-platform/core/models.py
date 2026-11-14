"""数据模型：用例、评测结果、人工复核。"""

from typing import Optional

from pydantic import BaseModel, Field

# 支持的三类评测任务
TASK_TYPES = ("rag", "agent", "compliance")


class CaseIn(BaseModel):
    """新增 / 编辑用例的请求体。"""

    task_type: str = Field(description="评测类型：rag / agent / compliance")
    question: str = Field(description="问题或用户输入")
    expected_answer: str = Field(default="", description="参考答案")
    contexts: list[str] = Field(default_factory=list, description="RAG 参考文档片段")
    expected_tools: list[str] = Field(default_factory=list, description="Agent 期望调用的工具")


class CaseOut(CaseIn):
    """用例完整信息（含数据库字段）。"""

    id: int
    version: int
    status: str
    created_at: str


class RunIn(BaseModel):
    """执行评测的请求体。"""

    case_ids: list[int] = Field(description="要评测的用例 ID 列表")
    model: str = Field(default="qwen-plus", description="被测模型名")


class ReviewIn(BaseModel):
    """人工复核的请求体。"""

    run_id: int
    reviewer: str = Field(default="human", description="复核人")
    human_scores: dict = Field(description="人工打分，如 {'accuracy': 0.9, ...}")
    comment: str = Field(default="", description="复核意见")


class AskResult(BaseModel):
    """单条评测结果。"""

    run_id: int
    case_id: int
    task_type: str
    pred_answer: str
    tool_calls: list[str] = Field(default_factory=list)
    scores: dict
    latency: float
    status: str
    error: Optional[str] = None
