"""全局配置：路径、模型、环境变量。"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录
ROOT = Path(__file__).resolve().parents[1]

# 读取 .env
load_dotenv(ROOT / ".env")

# ---- DashScope 配置 ----
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# ---- 模型 ----
# 被测模型：生成回答
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen-plus")
# 评委模型：LLM-as-Judge 打分
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "qwen-plus")
# 向量模型
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v4")

# ---- 存储路径 ----
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "eval.db"           # SQLite 数据库
CHROMA_DIR = DATA_DIR / "chroma_tmp"     # RAG 评测用的临时向量库

# 确保 data 目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
