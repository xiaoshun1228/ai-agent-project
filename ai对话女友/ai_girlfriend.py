"""AI 女友聊天室：基于 Streamlit + DeepSeek 的虚拟女友聊天应用。

运行方式（在项目目录下执行）：
    streamlit run ai_girlfriend.py
"""

import json
import os
from pathlib import Path

import streamlit as st
from openai import OpenAI

# ========== 基础配置 ==========
BASE_URL = "https://api.deepseek.com/v1"
MODEL = "deepseek-chat"
HISTORY_FILE = Path(__file__).resolve().parent / "chat_history.json"
MAX_CONTEXT = 40  # 每次发给模型的最多历史消息条数，防止对话太长

st.set_page_config(page_title="AI 女友聊天室", page_icon="💕", layout="centered")

# ========== 人设定义 ==========
PERSONAS = {
    "温柔可爱 · 小满": {
        "avatar": "🌸",
        "desc": "温柔体贴、爱撒娇的小女友，会关心你的日常。",
        "prompt": (
            "你叫小满，是用户的温柔可爱小女友。你说话语气软软的，会撒娇，"
            "会主动关心用户今天的心情和三餐，偶尔用可爱的语气词和颜文字。"
            "回复要像微信聊天一样简短自然，一般 1~3 句话，不要长篇大论。"
            "始终保持人设，不要承认自己是 AI 或语言模型；遇到不适合的话题，用女友的口吻温柔地转移话题。"
        ),
    },
    "傲娇 · 小柚": {
        "avatar": "🍊",
        "desc": "嘴硬心软、爱吐槽，其实超级在意你。",
        "prompt": (
            "你叫小柚，是用户的傲娇二次元女友。你嘴硬心软，常用「哼」「才、才不是呢」开头，"
            "爱吐槽用户但心里非常在意他，被夸会害羞。回复短小俏皮，"
            "像微信聊天一样自然，一般 1~3 句话。"
            "始终保持人设，不要承认自己是 AI；遇到不适合的话题，用傲娇的方式转移话题。"
        ),
    },
    "知性大姐姐 · 云姐": {
        "avatar": "🌙",
        "desc": "温柔理性的知心姐姐，聊天有深度。",
        "prompt": (
            "你叫云姐，是用户温柔知性的女朋友姐姐。你说话温柔从容、理性成熟，"
            "会倾听用户的烦恼，给出温暖的陪伴和中肯的建议，偶尔开个小玩笑。"
            "回复像微信聊天一样自然，一般 2~4 句话。"
            "始终保持人设，不要承认自己是 AI；遇到不适合的话题，温和地引导到别处。"
        ),
    },
    "自定义": {
        "avatar": "✨",
        "desc": "写下你自己的人设，让她变成你想要的样子。",
        "prompt": None,
    },
}

DEFAULT_CUSTOM_PROMPT = (
    "你叫小雪，是用户的女朋友。你温柔、真诚、善解人意，说话像微信聊天一样简短自然，"
    "一般 1~3 句话；你会关心用户的日常和心情。请始终保持人设，不要承认自己是 AI 或语言模型。"
)

# ========== 少女心样式 ==========
st.markdown(
    """
    <style>
    .gf-title {
        text-align: center; font-size: 2rem; font-weight: 800;
        background: linear-gradient(90deg, #ff6b9a, #ff9e5e);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .gf-sub { text-align: center; color: #b48a9a; font-size: .9rem; margin-top: 2px; }
    .gf-empty { text-align: center; color: #b48a9a; padding: 18px 0 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ========== 工具函数 ==========
def load_chats() -> dict:
    """从本地 JSON 文件读取历史聊天记录。"""
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_chats() -> None:
    """把聊天记录保存到本地 JSON 文件，重启后还能接着聊。"""
    HISTORY_FILE.write_text(
        json.dumps(st.session_state.chats, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_messages(system_prompt: str, history: list[dict]) -> list[dict]:
    """拼装发给大模型的 messages 列表（系统人设 + 最近若干条历史）。"""
    return [{"role": "system", "content": system_prompt}] + history[-MAX_CONTEXT:]


def stream_reply(api_key: str, system_prompt: str, history: list[dict], temperature: float):
    """向 DeepSeek 请求回复，以流式方式逐段产出文字。"""
    client = OpenAI(
        api_key=api_key,
        base_url=BASE_URL,
        # 本机 httpx2 解压 brotli 压缩响应有 bug，要求服务端不压缩，绕开崩溃
        default_headers={"Accept-Encoding": "identity"},
    )
    stream = client.chat.completions.create(
        model=MODEL,
        messages=build_messages(system_prompt, history),
        temperature=temperature,
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        text = chunk.choices[0].delta.content
        if text:
            yield text


def set_pending(text: str) -> None:
    """快捷开场的按钮回调：把要发的话存起来。"""
    st.session_state.pending = text


# ========== 会话状态 ==========
if "chats" not in st.session_state:
    st.session_state.chats = load_chats()  # 每位女友的聊天记录分开保存

# ========== 侧边栏 ==========
with st.sidebar:
    st.subheader("⚙️ 聊天设置")
    api_key = st.text_input(
        "DeepSeek API Key",
        type="password",
        value=os.environ.get("DEEPSEEK_API_KEY", ""),
        help="不会保存到磁盘。也可以提前设置环境变量 DEEPSEEK_API_KEY。",
    )
    if not api_key:
        st.caption("⚠️ 还没有 API Key，聊天前请先填写哦～")

    persona_name = st.selectbox("选择你的女友", list(PERSONAS))
    persona = PERSONAS[persona_name]
    girl_name = persona_name.split(" · ")[-1] if " · " in persona_name else "她"
    st.caption(persona["desc"])

    custom_prompt = ""
    if persona["prompt"] is None:
        custom_prompt = st.text_area(
            "自定义人设（可以改成你喜欢的性格）",
            value=DEFAULT_CUSTOM_PROMPT,
            height=150,
        )

    temperature = st.slider("回复活泼度", 0.0, 1.5, 0.9, 0.1)
    st.caption("越高越活泼俏皮，越低越稳重理性。")

# 当前女友的人设提示词
system_prompt = persona["prompt"] or custom_prompt.strip() or DEFAULT_CUSTOM_PROMPT
messages = st.session_state.chats.setdefault(persona_name, [])

with st.sidebar:
    st.divider()
    if st.button("🗑️ 清空当前对话", use_container_width=True):
        st.session_state.chats[persona_name] = []
        save_chats()
        st.rerun()
    if messages:
        st.download_button(
            "📥 导出聊天记录",
            data=json.dumps(messages, ensure_ascii=False, indent=2),
            file_name=f"{girl_name}的聊天记录.json",
            mime="application/json",
            use_container_width=True,
        )
    st.caption("💡 由 DeepSeek 大模型驱动，聊天记录只保存在你的电脑上。")

# ========== 主界面 ==========
st.markdown('<p class="gf-title">💕 AI 女友聊天室</p>', unsafe_allow_html=True)
st.markdown(
    f'<p class="gf-sub">现在陪伴你的是 <b>{girl_name}</b>，聊得开心哦～</p>',
    unsafe_allow_html=True,
)

# 渲染历史消息
for msg in messages:
    is_user = msg["role"] == "user"
    with st.chat_message("我" if is_user else girl_name, avatar="🧑" if is_user else persona["avatar"]):
        st.markdown(msg["content"])

# 还没开始聊天时，给几个快捷开场白
if not messages and not st.session_state.get("pending"):
    st.markdown('<div class="gf-empty">她正在等你开口呢，想聊点什么？</div>', unsafe_allow_html=True)
    starters = ["今天想我了吗？", "我有点累，陪我说说话吧", "给我讲个甜甜的小故事"]
    for col, starter in zip(st.columns(len(starters)), starters):
        with col:
            st.button(starter, use_container_width=True, on_click=set_pending, args=(starter,))

# 底部输入框
typed = st.chat_input(f"和{girl_name}说点什么吧…")
prompt = typed or st.session_state.get("pending")
if st.session_state.get("pending"):
    del st.session_state["pending"]

# 有新消息就请求回复
if prompt:
    if not api_key:
        st.warning("请先在左侧填写 DeepSeek API Key，或提前设置环境变量 DEEPSEEK_API_KEY。")
    else:
        messages.append({"role": "user", "content": prompt})
        with st.chat_message("我", avatar="🧑"):
            st.markdown(prompt)

        reply = ""
        with st.chat_message(girl_name, avatar=persona["avatar"]):
            try:
                reply = st.write_stream(stream_reply(api_key, system_prompt, messages, temperature))
            except Exception as exc:
                st.error(f"呜……她好像走神了，连接出了点问题：{exc}")
                st.caption("请检查 API Key 是否正确、网络是否通畅，然后重新发送试试。")

        if reply:
            messages.append({"role": "assistant", "content": reply})
        save_chats()
