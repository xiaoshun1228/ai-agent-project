"""全局配置：加载 .env，统一模型名称。"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录
ROOT = Path(__file__).resolve().parents[1]

# 读取项目根目录下的 .env
load_dotenv(ROOT / ".env")

# 阿里云 DashScope Key
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

# 语音识别模型（多模态，直接理解音频内容）
ASR_MODEL = "qwen3-omni-flash"

# 语音合成模型与音色
TTS_MODEL = "cosyvoice-v2"
TTS_VOICE = "longxiaochun_v2"

# 对话模型（可用环境变量覆盖）
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen-plus")

# 数据目录（存放 FAQ 文档）
DATA_DIR = ROOT / "data"
