# 私人厨师 Agent

一个基于 **LangChain Agent** 的智能食谱推荐服务：用户上传食材照片或输入食材清单，
Agent 会自动联网检索可行菜谱，按营养和难度打分排序，输出结构化的推荐方案。

项目覆盖「Agent 工具调用 + 多模态识别 + 会话持久化 + 后端服务化」完整链路。

---

## 一、功能特性

| 功能 | 说明 |
|---|---|
| 🍳 食材识别 | 支持上传食材照片，多模态模型自动识别 |
| 🔍 联网检索 | 通过 Tavily 搜索真实菜谱，避免模型凭空编造 |
| 📊 智能排序 | 从营养价值、制作难度两个维度打分排序 |
| 📝 结构化输出 | 输出菜谱名称、得分、推荐理由和参考图片 |
| 🧠 会话记忆 | 基于 LangGraph 的 `SqliteSaver` 持久化多轮对话 |
| 🌊 流式接口 | FastAPI 提供 SSE 流式响应，前端实时显示 |
| 🖼️ 图片上传 | 阿里云 OSS 预签名直传，不经过后端中转 |
| 🖥️ 内置前端 | 挂载构建好的静态页面，启动即可使用 |

---

## 二、技术栈

| 模块 | 技术 |
|---|---|
| 后端框架 | FastAPI + Uvicorn |
| Agent 框架 | LangChain `create_agent` |
| 会话持久化 | LangGraph `SqliteSaver` |
| 大模型 | Qwen `qwen3-omni-flash`（多模态） |
| 联网检索 | Tavily Search |
| 对象存储 | 阿里云 OSS（预签名上传） |
| 前端 | 静态页面（Next.js 构建产物） |
| 数据校验 | Pydantic |

---

## 三、工作流程

```
用户上传食材照片 / 输入食材清单
        │
        ▼
FastAPI 接收请求（message + image_url + thread_id）
        │
        ▼
LangChain Agent 启动
        │
        ├─▶ 多模态模型识别图片中的食材
        ├─▶ 调用 Tavily 联网检索菜谱
        └─▶ 对候选菜谱打分、排序
        │
        ▼
SSE 流式返回生成内容
        │
        ▼
会话状态写入 SQLite（按 thread_id 隔离）
```

---

## 四、项目结构

```
AI私人厨师/
├── app/
│   ├── main.py                  # FastAPI 入口、路由挂载、静态文件服务
│   ├── agents/
│   │   ├── personal_chief_agent.py  # Agent 定义、流式对话、会话管理
│   │   └── logger.py
│   ├── api/
│   │   └── v1/
│   │       ├── chat.py          # 对话接口（流式 / 历史 / 清空）
│   │       └── oss.py           # OSS 预签名上传接口
│   ├── common/
│   │   └── logger.py            # 日志配置
│   ├── models/
│   │   └── schemas.py           # 请求数据模型
│   └── static/                  # 前端静态资源
├── 私人厨师本地运行代码.py         # 本地快速体验脚本
├── requirements.txt
└── .env.example
```

---

## 五、快速开始

### 1. 环境准备

```bash
cd AI私人厨师
python -m venv .venv
.venv\Scripts\activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 配置环境变量

```bash
copy .env.example .env
```

编辑 `.env`，至少填写以下两项：

```
# 通义千问 Key（必需）
DASHSCOPE_API_KEY=sk-xxxxxxxx

# Tavily 搜索 Key（必需，用于联网检索菜谱）
TAVILY_API_KEY=tvly-xxxxxxxx
```

如果要用图片上传功能，还需要配置阿里云 OSS：

```
OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
OSS_REGION=cn-beijing
OSS_BUCKET=你的bucket名称
ALIBABA_CLOUD_ACCESS_KEY_ID=你的AccessKeyId
ALIBABA_CLOUD_ACCESS_KEY_SECRET=你的AccessKeySecret
```

> 不配置 OSS 时，服务仍可正常启动，只是图片上传接口会返回 503。

### 4. 启动服务

```bash
uvicorn app.main:app --reload
```

浏览器打开 `http://127.0.0.1:8000`，即可看到内置的对话页面。

接口文档：`http://127.0.0.1:8000/docs`

---

## 六、接口说明

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/chat/stream` | 流式对话（SSE） |
| GET | `/api/v1/chat/messages?thread_id=xxx` | 获取历史消息 |
| DELETE | `/api/v1/chat/messages?thread_id=xxx` | 清空会话 |
| GET | `/api/v1/oss/presign?filename=xxx.jpg` | 获取图片上传预签名 URL |

**请求示例：**

```json
POST /api/v1/chat/stream
{
  "message": "我有鸡蛋、西红柿和土豆，能做什么菜？",
  "image_url": null,
  "thread_id": "user-001"
}
```

---

## 七、核心实现说明

### 1. Agent 定义（`personal_chief_agent.py`）

```python
agent = create_agent(
    model=model,            # qwen3-omni-flash 多模态模型
    tools=[tavily],         # Tavily 联网搜索
    checkpointer=checkpointer,  # SQLite 会话记忆
    system_prompt=system_prompt,  # 四步工作流提示词
)
```

System Prompt 规定了 Agent 的工作步骤：
识别食材 → 检索菜谱 → 打分排序 → 结构化输出。

### 2. 流式输出

```python
for chunk, metadata in agent.stream(
    {"messages": [message]},
    {"configurable": {"thread_id": thread_id}},
    stream_mode="messages",
):
    yield chunk.content
```

`stream_mode="messages"` 让 Agent 每生成一段文字就立即返回，前端可以实时显示。

### 3. 会话隔离

- 每个用户传入唯一的 `thread_id`
- `SqliteSaver` 按 `thread_id` 保存 checkpoint
- 同一 `thread_id` 的对话会自动带上历史上下文

### 4. 图片处理

两种方式：

- **直接传图片 URL**：`image_url` 填公网可访问地址
- **前端直传 OSS**：先请求 `/api/v1/oss/presign` 拿到预签名 URL，
  前端直接 PUT 上传，再把返回的 URL 传给对话接口

好处是图片不经过后端服务器，节省带宽。

### 5. 静态页面服务

`main.py` 中自定义了 `SPAStaticFiles`：

- `/api/` 开头的请求走接口
- 其他路径找不到文件时回退到 `index.html`，支持前端单页路由

---

## 八、本地命令行体验

不想启动服务时，可以直接运行：

```bash
python 私人厨师本地运行代码.py
```

在终端里输入食材清单，查看 Agent 的推荐结果。

---

## 九、常见问题

**Q：启动报错「未配置 OSS 凭证」？**
A：说明没配 OSS 相关环境变量，不影响对话功能，只是图片上传不可用。

**Q：Agent 返回「信息检索失败」？**
A：检查 `TAVILY_API_KEY` 是否正确，以及网络能否访问 Tavily。

**Q：历史对话怎么清空？**
A：调用 `DELETE /api/v1/chat/messages?thread_id=xxx`，或在前端点清空按钮。

**Q：数据库文件在哪？**
A：项目根目录的 `db/personal_chief.db`，首次运行自动创建。

---

## 十、开发记录

| 阶段 | 内容 |
|---|---|
| 1 | 搭建 FastAPI 服务与静态页面 |
| 2 | 接入 Qwen 多模态模型与 Tavily 搜索 |
| 3 | LangChain Agent 编排与 SQLite 会话持久化 |
| 4 | SSE 流式接口与 OSS 预签名上传 |
