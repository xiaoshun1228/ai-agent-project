"""企业员工手册智能问答 —— 主界面。

运行：
    streamlit run app.py
"""

import streamlit as st

from core.chain import answer_stream
from core.store import count
from core.ui import setup_page, source_card, stat_box, title

# 页面基础配置（标题、图标、样式）
setup_page("员工手册智能助手", "📖")

# ---------------- 侧边栏 ----------------
with st.sidebar:
    st.markdown("### 📖 员工手册助手")

    # 知识库状态：空库时提醒去管理页上传
    block_count = count()
    if block_count == 0:
        st.warning("知识库为空\n\n请先在「知识库管理」页上传手册")
    else:
        st.success(f"知识库已就绪 · {block_count} 个文本块")

    st.divider()

    # 检索条数：越大参考的信息越多，但可能更慢
    top_k = st.slider(
        "检索条数 Top-K",
        min_value=1,
        max_value=8,
        value=4,
        help="每次回答参考的文本块数量，越大信息越全但可能更慢",
    )

    # 是否显示引用出处
    show_sources = st.checkbox("显示引用出处", value=True)

    st.divider()

    # 清空对话按钮
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption("回答只依据已上传的手册内容")

# ---------------- 主区域 ----------------
title("企业员工手册智能问答", "基于 RAG 检索增强生成 · 回答附带原文出处")

# 初始化会话状态：messages 保存整段对话
if "messages" not in st.session_state:
    st.session_state.messages = []

# 空状态：还没有任何对话时，展示示例问题按钮
if not st.session_state.messages:
    st.info("你好！我是员工手册助手，手册里有的内容我都能回答。试试这些问题：")
    examples = ["出差报销多久内提交？", "迟到多久算旷工？", "报销超过 5000 元谁审批？"]

    # 三列并排展示示例问题
    cols = st.columns(3)
    for col, question in zip(cols, examples):
        # 点击后把问题存进 pending，触发 rerun 后统一处理
        if col.button(question, use_container_width=True):
            st.session_state.pending = question
            st.rerun()

# 渲染历史对话
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # 如果开启显示出处，就在回答下方列出引用来源
        if show_sources and message.get("sources"):
            for source in message["sources"]:
                source_card(source["name"], source["index"])

# 底部输入框：用户输入问题
question = st.chat_input("请输入你的问题，例如：出差报销多久内提交？")

# 兼容示例按钮：输入为空时取 pending
question = question or st.session_state.pop("pending", None)

if question:
    # 1. 先把用户问题显示出来，并记入会话
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # 2. 生成回答
    with st.chat_message("assistant"):
        # 知识库为空时直接提示，不调用模型
        if count() == 0:
            st.warning("知识库为空，请先到「知识库管理」页上传员工手册。")
            answer_text = "知识库为空，暂时无法回答。"
            sources = []
        else:
            # 传历史对话时要排除最后一条（本次问题），避免重复
            stream, docs = answer_stream(
                question,
                k=top_k,
                history=st.session_state.messages[:-1],
            )

            # write_stream 一边接收一边显示，返回完整文本
            answer_text = st.write_stream(stream)

            # 从检索结果的元数据里取引用来源
            sources = [
                {
                    "name": doc.metadata.get("doc_name", "未知文档"),
                    "index": doc.metadata.get("chunk_index", "?"),
                }
                for doc in docs
            ]

            if show_sources:
                for source in sources:
                    source_card(source["name"], source["index"])

    # 3. 把回答也记入会话，页面刷新后仍能显示
    st.session_state.messages.append(
        {"role": "assistant", "content": answer_text, "sources": sources}
    )
