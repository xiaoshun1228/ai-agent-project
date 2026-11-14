"""语音识别（ASR）：把用户录音转成文字。

使用 qwen3-omni-flash 多模态模型，直接把音频理解成文字。
"""

import os
import tempfile

import dashscope
from dashscope import MultiModalConversation

from core.config import ASR_MODEL, DASHSCOPE_API_KEY

# 设置全局 API Key
dashscope.api_key = DASHSCOPE_API_KEY

# 提示词：要求只输出转写文字，避免模型附带解释
ASR_PROMPT = "请把这段音频准确转写成文字，只输出文字本身，不要添加任何解释。"


def transcribe(audio_bytes: bytes, suffix: str = ".wav") -> str:
    """识别语音内容。

    参数:
        audio_bytes: 音频二进制数据（Streamlit 录音默认是 WAV）
        suffix: 音频文件后缀
    返回:
        识别出的文字
    异常:
        RuntimeError: 接口返回失败时抛出
    """
    # 多模态接口需要文件路径，先把音频写进临时文件
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        # Windows 路径转成 file:/// 形式
        file_url = "file:///" + tmp_path.replace("\\", "/")

        response = MultiModalConversation.call(
            model=ASR_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"audio": file_url},
                        {"text": ASR_PROMPT},
                    ],
                }
            ],
        )

        # 接口失败时抛出异常
        if response.status_code != 200:
            raise RuntimeError(f"语音识别失败：{response.message}")

        content = response.output.choices[0].message.content

        # 返回结构通常是 [{'text': '...'}]
        if isinstance(content, list):
            return "".join(item.get("text", "") for item in content).strip()

        return str(content).strip()

    finally:
        # 无论成功失败都删除临时文件
        os.unlink(tmp_path)
