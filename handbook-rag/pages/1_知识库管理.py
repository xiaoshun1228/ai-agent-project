"""知识库管理页：上传手册 -> 清洗预览 -> 分块入库。"""

from pathlib import Path

import streamlit as st

from core.cleaner import clean_text
from core.loader import load_file, read_uploaded
from core.splitter import split_document
from core.store import add_chunks, clear, count
from core.ui import setup_page, stat_box, title

# 页面基础配置
setup_page("知识库管理", "📚")

title("知识库管理", "上传员工手册 → 自动清洗 → 分块入库")

# ---------------- 当前状态 ----------------
current_blocks = count()

# 三列展示：块数 / 清洗步骤 / 存储引擎
col1, col2, col3 = st.columns(3)
with col1:
    stat_box(current_blocks, "知识库文本块")
with col2:
    stat_box("5 步", "清洗流水线")
with col3:
    stat_box("Chroma", "向量存储")

st.divider()

# ---------------- 上传区域 ----------------
uploaded = st.file_uploader(
    "上传员工手册（支持 txt / md / pdf）",
    type=["txt", "md", "pdf"],
    help="上传后会先清洗，你可以预览效果再决定是否入库",
)

# 用户选择了文件才进入处理流程
if uploaded is not None:
    # 把上传的二进制内容读成文本
    raw_text = read_uploaded(uploaded.name, uploaded.getvalue())

    if not raw_text.strip():
        st.error("文件内容为空，或 PDF 是扫描件无法提取文字。")
    else:
        # 执行清洗流水线，拿到干净文本和统计
        cleaned_text, stats = clean_text(raw_text)
        st.success(f"清洗完成：{stats.summary()}")

        # 两个标签页：对比清洗前后
        tab_clean, tab_raw = st.tabs(["清洗后", "原始文本"])
        with tab_clean:
            st.text_area(
                "清洗后内容",
                cleaned_text,
                height=260,
                label_visibility="collapsed",
            )
        with tab_raw:
            st.text_area(
                "原始内容",
                raw_text,
                height=260,
                label_visibility="collapsed",
            )

        # 分块参数可调
        st.markdown("##### 分块设置")
        chunk_col1, chunk_col2 = st.columns(2)
        with chunk_col1:
            chunk_size = st.slider("每块字数", 100, 800, 300, 50)
        with chunk_col2:
            chunk_overlap = st.slider("相邻块重叠字数", 0, 200, 50, 10)

        # 预览会切成多少块
        chunks = split_document(
            cleaned_text,
            Path(uploaded.name).stem,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        st.info(f"预计切分为 **{len(chunks)}** 个文本块")

        # 确认后写入向量库
        if st.button("✅ 导入知识库", type="primary", use_container_width=True):
            added = add_chunks(chunks)
            st.success(f"已导入 {added} 块，当前知识库共 {count()} 块。")
            st.rerun()

st.divider()

# ---------------- 快捷操作 ----------------
action_col1, action_col2 = st.columns(2)

with action_col1:
    # 一键导入内置示例文档，方便演示
    if st.button("📥 导入示例文档", use_container_width=True):
        document = load_file("data/员工手册_示例.txt")
        cleaned_text, _ = clean_text(document.text)
        chunks = split_document(cleaned_text, document.name)
        added = add_chunks(chunks)
        st.success(f"示例文档已导入 {added} 块。")
        st.rerun()

with action_col2:
    # 清空知识库放在折叠区，避免误点
    with st.expander("🗑️ 清空知识库"):
        st.caption("清空后需要重新导入文档。")
        if st.button("确认清空", use_container_width=True):
            clear()
            st.success("知识库已清空。")
            st.rerun()
