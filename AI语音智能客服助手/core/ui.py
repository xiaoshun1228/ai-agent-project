"""界面公共配置：页面设置 + 全局样式。"""

import streamlit as st

# 全局 CSS：隐藏默认菜单/页脚，统一标题、卡片、按钮样式
CSS = """
<style>
    #MainMenu, footer {visibility: hidden;}

    .block-container {padding-top: 2rem; padding-bottom: 2rem;}

    .main-title {
        font-size: 1.9rem;
        font-weight: 700;
        color: #1F2937;
        margin-bottom: 0.1rem;
        letter-spacing: -0.5px;
    }
    .sub-title {
        color: #6B7280;
        font-size: 0.92rem;
        margin-bottom: 1.6rem;
    }

    .source-card {
        background: #F1F5F9;
        border-left: 3px solid #2563EB;
        border-radius: 6px;
        padding: 0.45rem 0.75rem;
        font-size: 0.83rem;
        color: #475569;
        margin-top: 0.35rem;
    }

    .stat-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 0.9rem 1rem;
        text-align: center;
    }
    .stat-value {font-size: 1.5rem; font-weight: 700; color: #2563EB;}
    .stat-label {font-size: 0.8rem; color: #64748B; margin-top: 0.15rem;}

    .stChatMessage {padding: 0.5rem 0;}
    .stButton > button {border-radius: 8px;}
</style>
"""


def setup_page(title: str, icon: str = "📖") -> None:
    """统一页面配置与样式。

    每个页面开头调用一次，负责设置标题、图标、宽屏布局，
    并把上面的 CSS 注入到页面里。
    """
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CSS, unsafe_allow_html=True)


def title(main: str, sub: str = "") -> None:
    """页面主标题 + 副标题。"""
    st.markdown(f'<div class="main-title">{main}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="sub-title">{sub}</div>', unsafe_allow_html=True)


def stat_box(value, label: str) -> None:
    """小统计卡片（显示一个数值 + 说明）。"""
    st.markdown(
        f'<div class="stat-box"><div class="stat-value">{value}</div>'
        f'<div class="stat-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


def source_card(name: str, index) -> None:
    """引用出处卡片，显示命中的文档名和块序号。"""
    st.markdown(
        f'<div class="source-card">📎 {name} · 第 {index} 块</div>',
        unsafe_allow_html=True,
    )
