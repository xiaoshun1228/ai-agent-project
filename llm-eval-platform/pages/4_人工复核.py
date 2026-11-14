"""人工复核打分回流。"""

import pandas as pd
import streamlit as st

from core.db import add_review, get_case, init_db, list_reviews, list_runs

init_db()

st.set_page_config(page_title="人工复核", page_icon="🧑‍⚖️", layout="wide")
st.title("🧑‍⚖️ 人工复核打分")

runs = list_runs(limit=200)

if not runs:
    st.info("暂无评测结果，请先执行评测。")
    st.stop()

# ---- 选择评测记录 ----
run_options = {
    f'#{r["id"]} [{r["task_type"]}] {r["pred_answer"][:30] or "（空）"}': r
    for r in runs
}
selected_label = st.selectbox("选择要复核的评测记录", list(run_options.keys()))
run = run_options[selected_label]

# ---- 展示详情 ----
st.subheader("评测详情")

# 通过 case_id 取出原始问题和参考答案
case = get_case(run["case_id"])

col1, col2 = st.columns(2)
with col1:
    st.markdown("**问题**")
    st.write(case["question"] if case else "（用例已删除）")

    st.markdown("**参考答案**")
    st.write(case["expected_answer"] if case and case["expected_answer"] else "（无）")

    st.markdown("**模型预测回答**")
    st.write(run["pred_answer"] or "（空）")

    if run.get("tool_calls"):
        st.markdown("**调用工具**")
        st.write(", ".join(run["tool_calls"]))

with col2:
    st.markdown("**自动评分**")
    st.json(run.get("scores") or {})

st.divider()

# ---- 人工打分 ----
st.subheader("人工打分")

with st.form("review_form"):
    c1, c2 = st.columns(2)
    with c1:
        recall = st.slider("召回率", 0.0, 1.0, float((run.get("scores") or {}).get("recall", 0.5)), 0.05)
        accuracy = st.slider("准确率", 0.0, 1.0, float((run.get("scores") or {}).get("accuracy", 0.5)), 0.05)
    with c2:
        hallucination = st.slider("幻觉率", 0.0, 1.0, float((run.get("scores") or {}).get("hallucination", 0.5)), 0.05)
        compliance = st.slider("合规率", 0.0, 1.0, float((run.get("scores") or {}).get("compliance", 0.5)), 0.05)

    reviewer = st.text_input("复核人", value="human")
    comment = st.text_area("复核意见", height=80)

    submitted = st.form_submit_button("提交复核", type="primary")

    if submitted:
        add_review(
            run_id=run["id"],
            reviewer=reviewer,
            human_scores={
                "recall": recall,
                "accuracy": accuracy,
                "hallucination": hallucination,
                "compliance": compliance,
            },
            comment=comment,
        )
        st.success("复核已提交")
        st.rerun()

st.divider()

# ---- 复核记录 ----
st.subheader("历史复核记录")
reviews = list_reviews(limit=50)

if reviews:
    rows = []
    for review in reviews:
        scores = review["human_scores"]
        rows.append({
            "复核ID": review["id"],
            "评测ID": review["run_id"],
            "复核人": review["reviewer"],
            "召回率": scores.get("recall", ""),
            "准确率": scores.get("accuracy", ""),
            "幻觉率": scores.get("hallucination", ""),
            "合规率": scores.get("compliance", ""),
            "意见": review["comment"][:30],
            "时间": review["created_at"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("还没有复核记录")
