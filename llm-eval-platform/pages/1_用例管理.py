"""评测用例管理：增删查、版本管理。"""

import json

import pandas as pd
import streamlit as st

from core.db import add_case, delete_case, get_case, init_db, list_cases, update_case

init_db()

st.set_page_config(page_title="用例管理", page_icon="📝", layout="wide")
st.title("📝 评测用例管理")

# ---- 筛选与列表 ----
task_type = st.selectbox("按类型筛选", ["全部", "rag", "agent", "compliance"])
cases = list_cases(task_type=None if task_type == "全部" else task_type)

if cases:
    rows = [
        {
            "ID": c["id"],
            "类型": c["task_type"],
            "问题": c["question"][:50],
            "参考答案": c["expected_answer"][:40],
            "版本": c["version"],
            "创建时间": c["created_at"],
        }
        for c in cases
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("当前没有用例，请在下方新增。")

st.divider()

# ---- 新增用例 ----
st.subheader("➕ 新增用例")

with st.form("new_case_form"):
    new_type = st.selectbox("评测类型", ["rag", "agent", "compliance"])
    new_question = st.text_area("问题 / 用户输入", height=80)
    new_expected = st.text_area("参考答案", height=80)
    new_contexts = st.text_area(
        "参考资料（RAG 用，每行一条）",
        height=100,
        help="仅 RAG 评测需要，其它类型可以留空",
    )
    new_tools = st.text_input(
        "期望工具（Agent 用，逗号分隔，如 web_search,calculator）",
        help="仅 Agent 评测需要",
    )
    submitted = st.form_submit_button("保存用例", type="primary")

    if submitted:
        if not new_question.strip():
            st.warning("问题不能为空")
        else:
            case_id = add_case(
                task_type=new_type,
                question=new_question.strip(),
                expected_answer=new_expected.strip(),
                contexts=[line.strip() for line in new_contexts.splitlines() if line.strip()],
                expected_tools=[t.strip() for t in new_tools.split(",") if t.strip()],
            )
            st.success(f"已新增用例 #{case_id}")
            st.rerun()

st.divider()

# ---- 编辑与版本管理 ----
st.subheader("✏️ 编辑用例（自动升版本）")

if cases:
    case_options = {f'#{c["id"]} {c["question"][:30]}': c["id"] for c in cases}
    selected_label = st.selectbox("选择要编辑的用例", list(case_options.keys()))
    selected_id = case_options[selected_label]
    case = get_case(selected_id)

    with st.form("edit_case_form"):
        edit_type = st.selectbox(
            "类型", ["rag", "agent", "compliance"],
            index=["rag", "agent", "compliance"].index(case["task_type"]),
        )
        edit_question = st.text_area("问题", value=case["question"], height=80)
        edit_expected = st.text_area("参考答案", value=case["expected_answer"], height=80)
        edit_contexts = st.text_area(
            "参考资料（每行一条）",
            value="\n".join(case["contexts"]),
            height=100,
        )
        edit_tools = st.text_input(
            "期望工具（逗号分隔）",
            value=",".join(case["expected_tools"]),
        )
        save = st.form_submit_button("保存修改")

        if save:
            update_case(
                selected_id,
                task_type=edit_type,
                question=edit_question.strip(),
                expected_answer=edit_expected.strip(),
                contexts=[line.strip() for line in edit_contexts.splitlines() if line.strip()],
                expected_tools=[t.strip() for t in edit_tools.split(",") if t.strip()],
                version_up=True,  # 版本号加一
            )
            st.success("已保存，版本号已更新")
            st.rerun()

    # ---- 删除 ----
    st.divider()
    st.subheader("🗑️ 删除用例")
    st.caption("删除是软删除，历史评测记录会保留。")
    if st.button(f"删除用例 #{selected_id}", type="secondary"):
        delete_case(selected_id)
        st.success("已删除")
        st.rerun()
else:
    st.info("暂无可用用例")
