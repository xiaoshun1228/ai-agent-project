# AI 应用开发项目集

四个基于大语言模型（LLM）的 AI 应用项目，覆盖 **对话应用、多角色人设、Agent 工具调用、RAG 知识库问答** 四类主流场景。
全部使用 Python 开发，独立完成需求设计、编码、调试与部署。

## 项目列表

| 项目 | 技术栈 | 核心能力 |
|---|---|---|
| [AI 智能对话助手](./ai智能对话助手) | Streamlit + OpenAI SDK + DeepSeek | 多轮对话、流式输出、上下文管理 |
| [AI 多角色聊天应用](./ai对话女友) | Streamlit + OpenAI SDK + DeepSeek | 多角色人设、本地持久化、对话导出 |
| [私人厨师 Agent](./ai私人厨师) | FastAPI + LangChain + LangGraph + Qwen | 工具调用、多模态识别、状态持久化 |
| [员工手册知识库](./handbook-rag) | Streamlit + LangChain + Chroma + Qwen | 数据清洗、RAG 检索、引用溯源 |

---

## 1. AI 智能对话助手

Web 端大模型对话应用，支持多轮上下文、流式输出与自定义系统提示词。

- **上下文管理**：使用 `list[dict]` 维护消息历史，设计截断策略（保留最近 N 条）控制 token 消耗
- **流式输出**：通过 `yield` 生成器逐段接收模型响应，实现打字机效果
- **健壮性**：API Key 缺失、网络异常均有友好提示

```bash
pip install -r requirements.txt
streamlit run 17.ai对话助手.py
```

## 2. AI 多角色聊天应用

支持多套人设切换的对话应用，聊天记录本地持久化，可随时导出。

- **人设配置**：字典集中管理多套 system prompt，支持用户自定义角色
- **参数调节**：通过 `temperature` 滑块动态控制回复风格
- **持久化**：JSON 文件按角色分别保存对话，重启后继续
- **状态管理**：基于 Streamlit `session_state`，刷新不丢失

```bash
pip install -r requirements.txt
streamlit run ai_girlfriend.py
```

## 3. 私人厨师 Agent

基于 LangChain Agent 的智能食谱推荐服务，接收食材照片或清单，自动检索并排序推荐菜谱。

- **Agent 架构**：LangChain `create_agent` + 工具调用循环
- **多模态**：接入 Qwen 多模态模型，支持图片识别食材
- **工具调用**：Tavily 联网检索真实菜谱，避免模型编造
- **状态持久化**：LangGraph `SqliteSaver` 保存会话与记忆
- **服务化**：FastAPI 提供流式接口，挂载前端静态页面
- **文件上传**：阿里云 OSS 直传签名

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 4. 企业员工手册数据清洗与智能问答知识库平台

基于 RAG 的企业手册问答系统：上传文档后自动清洗、分块、向量化入库，员工可用自然语言提问并获得带引用出处的回答。

- **数据清洗流水线**：噪声过滤（页码/目录/符号行）、敏感信息脱敏、重复条款去重
- **RAG 检索问答**：Chroma 向量检索 Top-K → Prompt 拼装 → Qwen 流式生成
- **引用溯源**：回答附带命中的文档块，便于核对
- **防幻觉**：System Prompt 限定只依据参考资料回答，`temperature=0.1`
- **双页面界面**：问答页 + 知识库管理页（上传、清洗预览、入库）

```bash
pip install -r requirements.txt
cp .env.example .env   # 填入 DASHSCOPE_API_KEY
streamlit run app.py
```

---

## 环境要求

- Python 3.12+
- 各项目所需 API Key 见对应目录下的 `.env.example`

## 说明

- 所有密钥均通过环境变量读取，仓库中不包含任何明文密钥
- 本地数据库、虚拟环境、日志文件已通过 `.gitignore` 排除
