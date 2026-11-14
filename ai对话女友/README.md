# AI 多角色聊天应用

一个支持**多套人设切换**的 AI 聊天应用：用户可以选择不同的角色性格与模型对话，
对话记录本地持久化，随时可以导出。

适合演示「多角色 Prompt 设计 + 上下文管理 + 状态持久化」这几类常见需求。

---

## 一、功能特性

| 功能 | 说明 |
|---|---|
| 🎭 多套人设 | 内置温柔、傲娇、知性三套角色，另有自定义人设 |
| 🎚️ 风格调节 | `temperature` 滑块控制回复的活泼程度 |
| 💬 流式输出 | 回答逐字显示，有打字机效果 |
| 💾 本地持久化 | 每个角色的聊天记录分别保存到本地 JSON 文件 |
| 📥 导出记录 | 一键把当前角色的对话导出为 JSON |
| 🚀 快捷开场 | 空白对话时提供三条开场白，点一下就能开始 |
| 🧠 上下文控制 | 每次只发送最近 40 条消息，避免对话过长 |

---

## 二、技术栈

| 模块 | 技术 |
|---|---|
| Web 界面 | Streamlit |
| 模型调用 | OpenAI SDK（兼容接口） |
| 大模型 | DeepSeek `deepseek-chat` |
| 数据存储 | 本地 JSON 文件 |
| 流式输出 | 生成器 + `st.write_stream` |

---

## 三、工作流程

```
用户选择角色（人设 Prompt）
        │
        ▼
用户输入消息
        │
        ▼
拼接消息列表：System Prompt + 最近 40 条历史 + 新消息
        │
        ▼
调用 DeepSeek（stream=True）
        │
        ▼
逐段接收文字 → 页面实时显示
        │
        ▼
写入该角色的聊天记录 → 保存到 chat_history.json
```

---

## 四、项目结构

```
ai对话女友/
├── ai_girlfriend.py        # 应用主程序（单文件实现）
├── chat_history.json       # 聊天记录（首次运行后自动生成）
├── requirements.txt
└── README.md
```

---

## 五、快速开始

### 1. 环境准备

```bash
cd ai对话女友
python -m venv .venv
.venv\Scripts\activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 配置 API Key

本项目使用 DeepSeek 的模型，二选一：

**方式一：页面上直接填写**

启动后，在左侧侧边栏的「DeepSeek API Key」输入框里粘贴 Key。

**方式二：环境变量**

```bash
# Windows 当前终端
set DEEPSEEK_API_KEY=sk-xxxxxxxx
```

> Key 获取地址：https://platform.deepseek.com/api_keys

### 4. 启动

```bash
streamlit run ai_girlfriend.py
```

浏览器打开 `http://localhost:8501`。

---

## 六、使用说明

1. 左侧侧边栏选择角色（如「温柔可爱 · 小满」）
2. 在下方输入框输入消息，回车发送
3. 回答会逐字显示，并自动保存到本地
4. 切换角色时，每个角色的对话是独立的

**侧边栏功能：**

| 功能 | 说明 |
|---|---|
| 选择角色 | 四套人设：小满、小柚、云姐、自定义 |
| 自定义人设 | 选择「自定义」后可编辑角色 Prompt |
| 回复活泼度 | 0 ~ 1.5，越高越活泼，越低越稳重 |
| 清空当前对话 | 只清空当前角色的记录 |
| 导出聊天记录 | 导出为 JSON 文件，文件名带角色名 |

---

## 七、核心实现说明

### 1. 人设配置（`PERSONAS` 字典）

每个角色包含三个字段：

```python
"温柔可爱 · 小满": {
    "avatar": "🌸",          # 头像
    "desc": "温柔体贴...",     # 界面上的角色说明
    "prompt": "你叫小满...",   # 发给模型的 System Prompt
}
```

新增角色只需要在字典里加一项，不需要改其他代码。

### 2. 上下文截断

```python
return [{"role": "system", "content": system_prompt}] + history[-MAX_CONTEXT:]
```

- `history[-40:]`：只取最近 40 条
- 作用：控制 token 消耗，避免请求超限、费用失控

### 3. 本地持久化

- 数据结构：`{角色名: [消息列表]}`
- 每次生成回答后写入 `chat_history.json`
- 启动时读取，实现「关掉再打开，聊天记录还在」

### 4. 状态管理

使用 Streamlit 的 `st.session_state` 保存当前会话数据，
页面刷新时数据不丢失。

---

## 八、常见问题

**Q：提示「请先填写 API Key」？**
A：在侧边栏填写 DeepSeek Key，或提前设置环境变量 `DEEPSEEK_API_KEY`。

**Q：聊天记录存在哪里？**
A：项目目录下的 `chat_history.json`，只保存在本地，不会上传。

**Q：如何新增一个角色？**
A：在 `PERSONAS` 字典里新增一项，填好头像、说明和 Prompt 即可。

**Q：回答太长或太短怎么办？**
A：在角色的 Prompt 里明确要求「回复控制在 1~3 句话」，或在侧边栏调低「回复活泼度」。

---

## 九、开发记录

| 阶段 | 内容 |
|---|---|
| 1 | 基础对话与流式输出 |
| 2 | 多角色人设配置与切换 |
| 3 | 聊天记录本地持久化与导出 |
| 4 | 参数调节与界面优化 |
