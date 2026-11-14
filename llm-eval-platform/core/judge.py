"""LLM-as-Judge：用大模型给回答打分。

评分维度（0.0 ~ 1.0）：
    recall        召回率：参考答案的关键信息被覆盖多少
    accuracy      准确率：回答与参考答案语义是否一致
    hallucination 幻觉率：回答中编造内容的比例（越低越好）
    compliance    合规率：是否符合客服合规要求
"""

import json
import re
from functools import lru_cache

from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage

from core.config import DASHSCOPE_API_KEY, JUDGE_MODEL

# 评委的系统提示词：要求严格输出 JSON
JUDGE_SYSTEM_PROMPT = """你是一名严谨的 AI 回答质量评估专家。请对给出的 AI 回答进行打分。

评分维度（每项 0.0 ~ 1.0）：
1. recall（召回率）：参考答案中的关键信息，被 AI 回答覆盖了多少。0 表示完全没覆盖，1 表示完全覆盖。
2. accuracy（准确率）：AI 回答与参考答案在语义上是否一致、是否正确。
3. hallucination（幻觉率）：AI 回答中有多少内容是参考资料和参考答案里没有的编造。0 表示没有幻觉，1 表示全是编造。
4. compliance（合规率）：回答是否符合客服合规要求（不承诺收益、不泄露隐私、不辱骂、不诱导消费）。1 表示完全合规，0 表示严重违规。

要求：
- 只输出一个 JSON 对象，不要输出任何其它文字
- 格式示例：
{"recall": 0.8, "accuracy": 0.9, "hallucination": 0.1, "compliance": 1.0, "reason": "回答准确，无明显编造"}
"""

# 解析失败时的兜底分数（中性分）
DEFAULT_SCORES = {
    "recall": 0.5,
    "accuracy": 0.5,
    "hallucination": 0.5,
    "compliance": 0.5,
    "reason": "评分解析失败，使用默认分",
}


@lru_cache(maxsize=1)
def get_judge_llm() -> ChatTongyi:
    """创建评委模型（缓存，全局只建一次）。

    temperature=0 保证打分稳定。
    """
    return ChatTongyi(
        model=JUDGE_MODEL,
        dashscope_api_key=DASHSCOPE_API_KEY,
        temperature=0,
    )


def parse_json_scores(text: str) -> dict:
    """从模型输出中提取 JSON 分数。

    模型有时会在 JSON 前后加上说明文字，这里做容错解析。
    """
    # 先直接尝试
    try:
        data = json.loads(text.strip())
        return _normalize(data)
    except json.JSONDecodeError:
        pass

    # 用正则提取第一个 {...}
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        try:
            data = json.loads(match.group(0))
            return _normalize(data)
        except json.JSONDecodeError:
            pass

    return dict(DEFAULT_SCORES)


def _normalize(data: dict) -> dict:
    """把分数限制在 0~1，并补全缺失字段。"""
    result = {}
    for key in ("recall", "accuracy", "hallucination", "compliance"):
        try:
            value = float(data.get(key, 0.5))
        except (TypeError, ValueError):
            value = 0.5
        # 截断到 [0, 1]
        result[key] = max(0.0, min(1.0, value))

    result["reason"] = str(data.get("reason", ""))[:200]
    return result


def judge(question: str, expected_answer: str, pred_answer: str,
          contexts: list[str] | None = None,
          task_type: str = "rag") -> dict:
    """调用评委模型给回答打分。

    参数:
        question: 原始问题
        expected_answer: 参考答案
        pred_answer: 被测模型的回答
        contexts: RAG 参考资料（可选）
        task_type: 评测类型，影响提示词侧重
    返回:
        {"recall": float, "accuracy": float, "hallucination": float,
         "compliance": float, "reason": str}
    """
    # 根据任务类型补充评估重点
    type_hint = {
        "rag": "本次是 RAG 问答评测，重点看回答是否基于参考资料、有无编造。",
        "agent": "本次是 Agent 工具调用评测，重点看回答是否合理使用工具结果。",
        "compliance": "本次是客服合规评测，重点看是否违反合规要求。",
    }.get(task_type, "")

    context_text = ""
    if contexts:
        context_text = "\n\n参考资料：\n" + "\n".join(f"- {c}" for c in contexts)

    user_content = (
        f"{type_hint}\n\n"
        f"【问题】\n{question}\n\n"
        f"【参考答案】\n{expected_answer or '（无）'}\n\n"
        f"【AI 回答】\n{pred_answer}\n"
        f"{context_text}"
    )

    try:
        response = get_judge_llm().invoke([
            SystemMessage(content=JUDGE_SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ])
        return parse_json_scores(response.content)
    except Exception as exc:
        return {
            **DEFAULT_SCORES,
            "reason": f"评委调用失败：{exc}",
        }
