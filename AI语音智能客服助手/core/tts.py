"""语音合成（TTS）：把客服回答转成语音。

使用 cosyvoice-v2 模型，输出 mp3 音频。
"""

import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer

from core.config import DASHSCOPE_API_KEY, TTS_MODEL, TTS_VOICE

# 设置全局 API Key
dashscope.api_key = DASHSCOPE_API_KEY


def synthesize(text: str) -> bytes:
    """把文字合成为语音。

    参数:
        text: 要朗读的文字
    返回:
        mp3 音频二进制；文字为空时返回空 bytes
    异常:
        RuntimeError: 合成失败时抛出
    """
    # 去掉不适合朗读的 Markdown 符号
    clean_text = text.replace("*", "").replace("#", "").replace("`", "").strip()
    if not clean_text:
        return b""

    synthesizer = SpeechSynthesizer(model=TTS_MODEL, voice=TTS_VOICE)
    audio = synthesizer.call(clean_text)

    if not audio:
        raise RuntimeError("语音合成失败，请检查网络或账户额度")

    return audio
