import streamlit as st
#设置页面的配置项
st.set_page_config(
    page_title="AI智能助手",
    page_icon="🤖",
    #布局
    layout="wide",
    #控制的是侧边栏的部分
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)
#段落文字
st.write("这是一个段落文字, 支持 **Markdown** 语法哦~")
#代码块
st.code("print('Hello, Streamlit!')", language="python")

st.divider()

#============================ AI 对话助手部分 ============================

import os
from openai import OpenAI

st.header("AI 智能对话助手")

#创建与ai大模型交互的客户端对象(放在函数里, 每次请求时再创建, 避免页面刷新就报错)
def get_client(api_key):
    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        #本机 Brotli 1.0.9 与 httpx2 不兼容, 服务器返回 brotli 压缩时解压会报错, 所以禁用压缩
        default_headers={"Accept-Encoding": "identity"},
    )

#---- 侧边栏: 配置项 ----
with st.sidebar:
    st.subheader("⚙️ 配置")
    #优先读取环境变量 DEEPSEEK_API_KEY, 也可以手动输入
    api_key = st.text_input(
        "DeepSeek API Key",
        value=os.environ.get('DEEPSEEK_API_KEY', ''),
        type="password",
    )
    system_prompt = st.text_area(
        "系统提示词",
        value="你是一名非常可爱的ai小助理，你的名字叫做小的，请你用温柔的语气回答用户的问题",
        height=120,
    )
    #清空对话按钮
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

#---- 会话状态: 保存聊天记录 ----
#session_state 中的数据在一次会话的多次页面刷新之间一直保留
if "messages" not in st.session_state:
    st.session_state.messages = []

#---- 渲染历史聊天记录 ----
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

#---- 接收用户输入并回复 ----
prompt = st.chat_input("请输入你想问的问题...")

if prompt:
    #1. 没有填写 API Key 就给出提示
    if not api_key:
        st.warning("请先在左侧侧边栏填写 DeepSeek API Key")
        st.stop()

    #2. 把用户的问题显示在页面上, 并记录到会话状态
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    #3. 调用大模型, 以流式的方式输出回答
    with st.chat_message("assistant"):
        try:
            client = get_client(api_key)
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    *st.session_state.messages,
                ],
                stream=True,
            )
            #st.write_stream 会把流式片段一边接收一边显示, 最后返回完整文本
            answer = st.write_stream(
                chunk.choices[0].delta.content or ""
                for chunk in response
                if chunk.choices
            )
        except Exception as e:
            #出错时给出友好提示, 并把错误信息显示出来
            st.error(f"调用大模型失败: {e}")
            st.stop()

    #4. 把ai的回答也记录到会话状态中
    st.session_state.messages.append({"role": "assistant", "content": answer})