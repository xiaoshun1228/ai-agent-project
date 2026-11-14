"""评测中台 · 总览页。

启动：streamlit run app.py
"""

import pandas as pd
import streamlit as st

from core.db import get_stats, init_db, list_runs

# 初始化数据库
init_db()

st.set_page_config(
    page_title="LLM 评测中台",
    page_icon="📊",
    layout="wide",
)

st.title("📊 轻量化大模型评测中台")
st.caption("RAG 问答 / Agent 工具调用 / 客服合规 · LLM-as-Judge 自动打分")

# ---- 统计卡片 ----
stats = get_stats()

col1, col2, col3 = st.columns(3)
col1.metric("评测用例", stats["cases"])
col2.metric("评测次数", stats["runs"])
col3.metric("人工复核", stats["reviews"])

st.divider()

# ---- 最近评测 ----
st.subheader("🕒 最近评测结果")

runs = list_runs(limit=20)

if runs:
    rows = []
    for run in runs:
        scores = run.get("scores") or {}
        rows.append({
            "ID": run["id"],
            "类型": run["task_type"],
            "模型": run["model"],
            "召回率": scores.get("recall", ""),
            "准确率": scores.get("accuracy", ""),
            "幻觉率": scores.get("hallucination", ""),
            "合规率": scores.get("compliance", ""),
            "耗时(s)": run["latency"],
            "状态": run["status"],
            "时间": run["created_at"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("还没有评测记录。先到「用例管理」添加用例，再去「执行评测」跑一批。")

st.divider()

# ---- 使用指引 ----
st.subheader("🧭 快速开始")
st.markdown(
    """
    1. **用例管理**：新增评测用例，支持 RAG / Agent / 合规三类
    2. **执行评测**：勾选用例，批量运行，自动打分
    3. **结果分析**：查看指标、对比报表，导出 CSV
    4. **人工复核**：对自动评分不满意时人工打分回流
    """
)
