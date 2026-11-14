# AI 语音智能客服助手

基于 **语音识别 + RAG 检索 + 语音合成** 的智能客服系统：用户按住麦克风说话，系统自动识别问题、
检索 FAQ 知识库、生成客服回答，并用语音播报出来。

## 功能特性

- **语音输入**：按住麦克风说话，自动转写成文字
- **FAQ 知识库**：内置常见问题，支持语义检索
- **智能回答**：Qwen 依据 FAQ 生成客服回复，资料中没有的会建议转人工
- **语音播报**：回答自动合成为语音播放
- **文字兜底**：没有麦克风也能打字提问
- **多轮对话**：保留最近 6 轮上下文

## 技术栈

| 环节 | 技术 |
|---|---|
| 界面 | Streamlit |
| 语音识别 ASR | DashScope `qwen3-omni-flash` |
| 语音合成 TTS | DashScope `cosyvoice-v2` |
| 对话生成 | Qwen `qwen-plus` |
| 检索 | LangChain + Chroma |
| 向量化 | DashScope `text-embedding-v4` |

## 工作流程

```
用户录音
   ↓  qwen3-omni-flash 语音识别
问题文字
   ↓  Chroma 检索 FAQ Top-3
参考资料 + 问题
   ↓  qwen-plus 生成回答
回答文字
   ↓  cosyvoice-v2 语音合成
语音播报
```

## 项目结构

```
ai智能对话助手/
├── app.py                # 主界面（语音输入 + 对话 + 播报）
├── core/
│   ├── config.py         # 全局配置与模型名
│   ├── asr.py            # 语音识别
│   ├── tts.py            # 语音合成
│   ├── kb.py             # FAQ 加载与入库
│   ├── chat.py           # 客服对话链
│   ├── cleaner.py        # 文本清洗
│   ├── splitter.py       # 文本分块
│   ├── embedder.py       # 向量化
│   ├── store.py          # Chroma 向量库
│   └── ui.py             # 界面样式
├── data/faq.txt          # 常见问题数据
├── requirements.txt
└── .env.example
```

## 快速开始

```bash
pip install -r requirements.txt
cp .env.example .env   # 填入 DASHSCOPE_API_KEY
streamlit run app.py
```

首次启动会自动把 `data/faq.txt` 导入向量库。浏览器打开后允许麦克风权限，按住说话即可。

## 示例问题

- 我的快递三天了还没到，怎么查物流？
- 收到的商品坏了，怎么退换？
- 怎么开发票？
- 支持哪些支付方式？
- 退款多久到账？

## 说明

- 语音识别与合成均使用 DashScope 接口，需要有效的 API Key
- 回答限制在三句话以内，便于语音播报
- FAQ 内容可自行替换 `data/faq.txt`，重启后自动入库
