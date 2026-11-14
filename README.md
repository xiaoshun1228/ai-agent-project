# AI 应用开发项目集

这是一个包含四个 AI 应用项目的代码仓库，覆盖大模型应用开发的主流方向：
**对话应用、多角色人设、Agent 工具调用、RAG 知识库问答、语音交互**。

所有项目均使用 Python 编写，独立完成需求设计、编码、调试与部署，代码带中文注释，便于阅读和讲解。

---

## 一、项目导航

| # | 项目 | 一句话说明 | 技术栈 |
|---|---|---|---|
| 1 | [AI 语音智能客服](./voice-customer-service) | 按住麦克风说话，听懂问题并语音回答 | Streamlit + DashScope + LangChain + Chroma |
| 2 | [AI 多角色聊天应用](./ai对话女友) | 多套人设切换的聊天应用，聊天记录本地保存 | Streamlit + OpenAI SDK + DeepSeek |
| 3 | [私人厨师 Agent](./ai私人厨师) | 上传食材照片，自动检索菜谱并打分排序 | FastAPI + LangChain + LangGraph + Qwen |
| 4 | [员工手册知识库](./handbook-rag) | 上传企业手册，自动清洗并支持带出处的问答 | Streamlit + LangChain + Chroma + Qwen |

---

## 二、项目概览

### 1. AI 语音智能客服

面向客服场景的语音问答系统，完整覆盖「语音识别 → 知识库检索 → 生成回答 → 语音合成」链路。

- 语音识别用 `qwen3-omni-flash` 多模态模型，无需单独部署识别服务
- FAQ 知识库用 Chroma 向量检索，回答只依据资料，避免编造
- 语音合成用 `cosyvoice-v2`，回答自动朗读
- 没有麦克风时支持文字输入

📁 目录：`voice-customer-service/`
📄 详细说明：[README](./voice-customer-service/README.md)

### 2. AI 多角色聊天应用

支持多套人设切换的聊天应用，适合演示「角色扮演 + 上下文管理」。

- 四套预置人设 + 自定义人设
- `temperature` 滑块调节回复风格
- 对话按角色分别保存到本地 JSON，重启不丢
- 支持导出聊天记录

📁 目录：`ai对话女友/`
📄 详细说明：[README](./ai对话女友/README.md)

### 3. 私人厨师 Agent

基于 LangChain Agent 的智能食谱推荐服务，体现「工具调用 + 多轮记忆 + 服务化」。

- LangChain `create_agent` 构建 Agent 循环
- Qwen 多模态模型识别食材照片
- Tavily 联网检索真实菜谱，避免模型编造
- LangGraph `SqliteSaver` 持久化会话
- FastAPI 提供 SSE 流式接口，挂载前端页面
- 阿里云 OSS 预签名直传图片

📁 目录：`ai私人厨师/`
📄 详细说明：[README](./ai私人厨师/README.md)

### 4. 企业员工手册知识库

RAG 知识库问答平台，重点体现「数据清洗 + 检索增强 + 引用溯源」。

- 五步数据清洗流水线：去噪、归一、脱敏、去重
- 文本分块（定长 + 重叠）后向量化入 Chroma
- 检索 Top-K 拼装 Prompt，回答附带原文出处
- 资料中没有答案时明确说明，不编造

📁 目录：`handbook-rag/`
📄 详细说明：[README](./handbook-rag/README.md)

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
| 数据持久化 | JSON、SQLite、Chroma |
| 工程工具 | Git、virtualenv、python-dotenv |

---

## 四、环境要求

- Python 3.12 及以上
- 各项目依赖见各自目录下的 `requirements.txt`
- 各项目所需 API Key 见各自目录下的 `.env.example`

---

## 五、统一运行方式

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

# 4. 启动
streamlit run app.py          # Streamlit 项目
uvicorn app.main:app --reload # FastAPI 项目
```

---

## 六、目录结构

```
个人项目/
├── README.md                  # 本文件：项目集总览
├── voice-customer-service/    # 项目 1：AI 语音智能客服
│   ├── app.py
│   ├── core/
│   ├── data/
│   ├── README.md
│   └── requirements.txt
├── ai对话女友/                 # 项目 2：AI 多角色聊天应用
│   ├── ai_girlfriend.py
│   ├── README.md
│   └── requirements.txt
├── ai私人厨师/                 # 项目 3：私人厨师 Agent
│   ├── app/
│   ├── 私人厨师本地运行代码.py
│   ├── README.md
│   └── requirements.txt
└── handbook-rag/              # 项目 4：员工手册知识库
    ├── app.py
    ├── pages/
    ├── core/
    ├── README.md
    └── requirements.txt
```

---

## 七、说明

- 所有 API Key 均通过 `.env` 环境变量读取，仓库中不包含任何明文密钥
- 虚拟环境（`.venv`）、向量库（`chroma_db`）、本地数据库和日志文件均已通过 `.gitignore` 排除
- 每个项目都可独立运行，互不依赖
