"""结果分析与对比报表。"""

import pandas as pd
import streamlit as st

from core.db import init_db, list_reviews, list_runs
from core.metrics import SCORE_LABELS
from core.report import build_report, export_csv

init_db()

st.set_page_config(page_title="结果分析", page_icon="📈", layout="wide")
st.title("📈 评测结果分析")

runs = list_runs(limit=1000)
reviews = list_reviews(limit=1000)

if not runs:
    st.info("暂无评测数据，请先执行评测。")
    st.stop()

report = build_report(runs, reviews)
overall = report["overall"]

# ---- 总体指标 ----
st.subheader("总体指标")
c1, c2, c3, c4 = st.columns(4)
c1.metric("召回率", f"{overall.get('recall', 0):.2%}")
c2.metric("准确率", f"{overall.get('accuracy', 0):.2%}")
c3.metric("幻觉率", f"{overall.get('hallucination', 0):.2%}", help="越低越好")
c4.metric("合规率", f"{overall.get('compliance', 0):.2%}")

st.caption(f"统计样本：{overall.get('count', 0)} 条成功评测")

st.divider()

# ---- 按类型对比 ----
st.subheader("按评测类型对比")
by_type = report["by_task_type"]

if by_type:
    df_type = pd.DataFrame(by_type).T
    df_type.index.name = "类型"
    st.bar_chart(df_type[[k for k in SCORE_LABELS]])
    st.dataframe(df_type, use_container_width=True)

st.divider()

# ---- 按模型对比 ----
st.subheader("按模型对比")
by_model = report["by_model"]

if by_model:
    df_model = pd.DataFrame(by_model).T
    df_model.index.name = "模型"
    st.bar_chart(df_model[[k for k in SCORE_LABELS]])
    st.dataframe(df_model, use_container_width=True)
else:
    st.info("暂无多模型数据")

st.divider()

# ---- 人工 vs 自动 ----
st.subheader("人工复核 vs 自动评分")
hva = report["human_vs_auto"]

if hva["count"] > 0:
    df_hva = pd.DataFrame({
        "自动评分": hva["auto"],
        "人工评分": hva["human"],
    })
    st.bar_chart(df_hva)
    st.caption(f"已复核 {hva['count']} 条")
else:
    st.info("还没有人工复核记录，可到「人工复核」页面打分。")

st.divider()

# ---- 导出 ----
st.subheader("导出报表")
csv_data = export_csv(runs)
st.download_button(
    "⬇️ 下载 CSV",
    data=csv_data,
    file_name="eval_results.csv",
    mime="text/csv",
)
