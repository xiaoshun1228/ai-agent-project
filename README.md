# AI 应用开发项目集

这是一个包含三个 AI 应用项目的代码仓库，覆盖大模型应用开发的主流方向：
**语音交互、RAG 知识库问答、AI 应用评测**。

所有项目均使用 Python 编写，独立完成需求设计、编码、调试与部署，代码带中文注释，便于阅读和讲解。

---

## 一、项目导航

| # | 项目 | 一句话说明 | 技术栈 |
|---|---|---|---|
| 1 | [AI-voice-customer](./AI-voice-customer) | 按住麦克风说话，听懂问题并语音回答 | Streamlit + DashScope + LangChain + Chroma |
| 2 | [RAG-handbook](./RAG-handbook) | 上传企业手册，自动清洗并支持带出处的问答 | Streamlit + LangChain + Chroma + Qwen |
| 3 | [llm-eval-platform](./llm-eval-platform) | RAG / Agent / 合规应用自动化评测与打分 | FastAPI + Streamlit + LLM-as-Judge + SQLite |

---

## 二、项目概览

### 1. AI 语音智能客服

面向客服场景的语音问答系统，完整覆盖「语音识别 → 知识库检索 → 生成回答 → 语音合成」链路。

- 语音识别用 `qwen3-omni-flash` 多模态模型，无需单独部署识别服务
- FAQ 知识库用 Chroma 向量检索，回答只依据资料，避免编造
- 语音合成用 `cosyvoice-v2`，回答自动朗读
- 没有麦克风时支持文字输入

📁 目录：`AI-voice-customer/`
📄 详细说明：[README](./AI-voice-customer/README.md)

### 2. 企业员工手册知识库

RAG 知识库问答平台，重点体现「数据清洗 + 检索增强 + 引用溯源」。

- 五步数据清洗流水线：去噪、归一、脱敏、去重
- 文本分块（定长 + 重叠）后向量化入 Chroma
- 检索 Top-K 拼装 Prompt，回答附带原文出处
- 资料中没有答案时明确说明，不编造

📁 目录：`RAG-handbook/`
📄 详细说明：[README](./RAG-handbook/README.md)

### 3. 大模型应用评测中台

面向 RAG / Agent / 客服合规的自动化评测平台，用 LLM-as-Judge 替代人工打分。

- 评测用例管理：增删查、版本管理
- 三类评测器：RAG 问答、Agent 工具调用、客服合规
- LLM-as-Judge：召回率、准确率、幻觉率、合规率四项指标
- 批量执行 + 实时进度
- 可视化报表：按类型/模型对比、人工 vs 自动对比、趋势
- 人工复核打分回流
- 双形态交付：Streamlit 界面 + FastAPI 接口

📁 目录：`llm-eval-platform/`
📄 详细说明：[README](./llm-eval-platform/README.md)

---

## 三、技术栈总览

| 能力 | 使用技术 |
|---|---|
| Web 界面 | Streamlit |
| 后端服务 | FastAPI + Uvicorn |
| 大模型调用 | DashScope（Qwen）、DeepSeek、OpenAI 兼容接口 |
| Agent 编排 | LangChain、LangGraph |
| 向量检索 | Chroma、text-embedding-v4 |
| 语音能力 | qwen3-omni-flash（识别）、cosyvoice-v2（合成） |
| 自动评测 | LLM-as-Judge（召回率 / 准确率 / 幻觉率 / 合规率） |
| 数据持久化 | JSON、SQLite、Chroma |
| 工程工具 | Git、virtualenv、python-dotenv |

---

## 四、环境要求

- Python 3.12 及以上
- 各项目依赖见各自目录下的 `requirements.txt`
- 各项目所需 API Key 见各自目录下的 `.env.example`

---

## 五、启动方式

> **说明**：项目支持两种启动方式，二者共用同一套核心逻辑（`core/` 目录），可以单独启动，也可以同时启动（端口不同，互不冲突）。

| 启动方式 | 命令 | 默认端口 | 适用场景 |
|---|---|---|---|
| Web 界面 | `streamlit run app.py` | 8501 | 自己使用、演示展示 |
| API 接口 | `uvicorn api:app --reload` | 8000 | 前后端分离、供其他程序调用 |

### 通用步骤

每个项目都有独立依赖，建议**进入对应目录**后单独创建虚拟环境：

```bash
cd <项目目录>

# 1. 创建并激活虚拟环境（Windows）
python -m venv .venv
.venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 配置密钥
copy .env.example .env
# 用记事本打开 .env，填入自己的 API Key
```

### 各项目启动命令

| 项目 | Web 界面 | API 接口 |
|---|---|---|
| [AI-voice-customer](./AI-voice-customer) | `streamlit run app.py` | `uvicorn api:app --reload` |
| [RAG-handbook](./RAG-handbook) | `streamlit run app.py` | `uvicorn api:app --reload` |
| [llm-eval-platform](./llm-eval-platform) | `streamlit run app.py` | `uvicorn api:app --reload` |

API 启动后，浏览器打开 `http://127.0.0.1:8000/docs` 可查看自动生成的接口文档，并直接在线测试。

---

## 六、目录结构

```
个人项目/
├── README.md                  # 本文件：项目集总览
├── AI-voice-customer/         # 项目 1：AI 语音智能客服
│   ├── app.py
│   ├── core/
│   ├── data/
│   ├── README.md
│   └── requirements.txt
├── RAG-handbook/              # 项目 2：员工手册知识库
│   ├── app.py
│   ├── pages/
│   ├── core/
│   ├── README.md
│   └── requirements.txt
└── llm-eval-platform/         # 项目 3：大模型应用评测中台
    ├── app.py
    ├── api.py
    ├── pages/
    ├── core/
    ├── data/
    ├── README.md
    └── requirements.txt
```

---

## 七、说明

- 所有 API Key 均通过 `.env` 环境变量读取，仓库中不包含任何明文密钥
- 虚拟环境（`.venv`）、向量库（`chroma_db`）、本地数据库和日志文件均已通过 `.gitignore` 排除
- 每个项目都可独立运行，互不依赖
