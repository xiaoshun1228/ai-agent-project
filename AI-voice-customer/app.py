"""AI 语音智能客服助手 —— 主界面。

功能：
- 按住麦克风说话，自动识别成文字
- 检索 FAQ 知识库，生成客服回答
- 回答自动语音播报
- 也支持文字输入
"""

import streamlit as st

from core.asr import transcribe
from core.chat import answer_stream
from core.kb import init_kb
from core.store import count
from core.tts import synthesize
from core.ui import setup_page, source_card, title

# 页面配置
setup_page("AI 语音智能客服", "🎧")

# 首次运行时自动导入 FAQ（知识库为空才执行）
init_kb()

# ---------------- 侧边栏 ----------------
with st.sidebar:
    st.markdown("### 🎧 语音客服")
    st.success(f"FAQ 知识库 · {count()} 条")

    st.divider()

    # 是否自动朗读回答
    voice_on = st.toggle("语音播报", value=True, help="回答生成后自动朗读")
    # 是否显示匹配到的 FAQ 原文
    show_ref = st.checkbox("显示匹配的 FAQ", value=False)

    st.divider()

    # 清空对话
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pop("last_audio", None)
        st.rerun()

    st.caption("使用麦克风需要在浏览器中允许录音权限")

# ---------------- 主区域 ----------------
title("AI 语音智能客服", "按住麦克风说话，我会听懂并回答你")

# 会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []

# 渲染历史对话
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # 历史里的语音回答也保留播放按钮
        if message.get("audio"):
            st.audio(message["audio"], format="audio/mp3")

        if show_ref and message.get("sources"):
            for index in message["sources"]:
                source_card("FAQ", index)

# ---------------- 语音输入 ----------------
audio_value = st.audio_input("🎙️ 按住说话")

if audio_value is not None:
    audio_bytes = audio_value.getvalue()
    digest = hash(audio_bytes)

    # 同一段音频只识别一次，避免页面刷新重复调用
    if st.session_state.get("last_audio") != digest:
        st.session_state.last_audio = digest

        with st.spinner("正在识别语音..."):
            try:
                recognized = transcribe(audio_bytes)
            except Exception as exc:
                st.error(f"语音识别失败：{exc}")
                recognized = ""

        if recognized:
            st.session_state.pending = recognized
            st.rerun()

# ---------------- 文字输入 ----------------
question = st.chat_input("也可以直接打字提问，例如：怎么申请退货？")
question = question or st.session_state.pop("pending", None)

if question:
    # 1. 显示用户问题
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # 2. 生成回答
    with st.chat_message("assistant"):
        try:
            stream, docs = answer_stream(
                question,
                k=3,
                history=st.session_state.messages[:-1],
            )
            answer_text = st.write_stream(stream)
        except Exception as exc:
            st.error(f"回答生成失败：{exc}")
            answer_text = ""
            docs = []

        # 3. 语音播报
        audio_bytes = None
        if answer_text and voice_on:
            with st.spinner("正在合成语音..."):
                try:
                    audio_bytes = synthesize(answer_text)
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                except Exception as exc:
                    st.caption(f"语音播报失败：{exc}")

        # 4. 显示匹配的 FAQ
        if show_ref and docs:
            for doc in docs:
                source_card("FAQ", doc.metadata.get("chunk_index", "?"))

    # 5. 记入会话
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer_text,
            "audio": audio_bytes,
            "sources": [doc.metadata.get("chunk_index", "?") for doc in docs],
        }
    )
