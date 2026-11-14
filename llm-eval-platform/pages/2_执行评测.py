"""批量执行评测。"""

import pandas as pd
import streamlit as st

from core.db import init_db, list_cases
from core.runner import run_batch

init_db()

st.set_page_config(page_title="执行评测", page_icon="🚀", layout="wide")
st.title("🚀 批量执行评测")

cases = list_cases()

if not cases:
    st.warning("没有可用用例，请先到「用例管理」添加。")
    st.stop()

# ---- 选择用例 ----
task_type = st.selectbox("评测类型", ["全部", "rag", "agent", "compliance"])
filtered = cases if task_type == "全部" else [c for c in cases if c["task_type"] == task_type]

case_options = {
    f'#{c["id"]} [{c["task_type"]}] {c["question"][:40]}': c["id"]
    for c in filtered
}

selected_labels = st.multiselect(
    "选择要评测的用例（可多选）",
    options=list(case_options.keys()),
)
selected_ids = [case_options[label] for label in selected_labels]

model = st.text_input("被测模型", value="qwen-plus", help="DashScope 支持的模型名")

st.caption(f"已选 {len(selected_ids)} 条用例")

# ---- 执行 ----
if st.button("开始评测", type="primary", disabled=not selected_ids):
    progress = st.progress(0.0)
    status = st.empty()
    results = []

    def on_progress(done, total, result):
        progress.progress(done / total)
        status.write(f"进度：{done}/{total} · 当前结果：{result['status']}")
        results.append(result)

    with st.spinner("评测进行中，请稍候..."):
        run_batch(selected_ids, model=model, progress_callback=on_progress)

    st.success(f"评测完成，共 {len(results)} 条")

    # 结果表格
    rows = []
    for item in results:
        scores = item.get("scores") or {}
        rows.append({
            "用例": item["case_id"],
            "类型": item["task_type"],
            "召回率": scores.get("recall", ""),
            "准确率": scores.get("accuracy", ""),
            "幻觉率": scores.get("hallucination", ""),
            "合规率": scores.get("compliance", ""),
            "耗时(s)": item["latency"],
            "状态": item["status"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # 展开看详情
    with st.expander("查看每条详情"):
        for item in results:
            st.markdown(f"**用例 #{item['case_id']}**（{item['task_type']}）")
            st.write("问题：", item["question"])
            st.write("预测：", item["pred_answer"])
            if item.get("tool_calls"):
                st.write("调用工具：", ", ".join(item["tool_calls"]))
            st.write("评分：", item.get("scores"))
            st.divider()
