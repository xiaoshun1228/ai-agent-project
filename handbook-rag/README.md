# 企业员工手册数据清洗与智能问答知识库平台

基于 **RAG（检索增强生成）** 的企业员工手册问答系统：上传手册文档后自动完成数据清洗、分块、向量化入库，
员工用自然语言提问即可获得准确回答，并附带原文出处。

## 功能特性

- **数据清洗流水线**：格式归一、噪声过滤（页码/目录/符号行）、敏感信息脱敏、重复条款去重
- **知识库构建**：文本分块 → 向量化 → 存入 Chroma 持久化向量库
- **智能问答**：语义检索 Top-K → 拼装 Prompt → Qwen 流式生成
- **引用溯源**：回答附带命中的文档块，便于核对
- **多轮对话**：保留最近 6 轮上下文，支持连续追问
- **双页面界面**：问答页 + 知识库管理页（上传、清洗预览、入库）

## 技术栈

| 模块 | 技术 |
|---|---|
| Web 界面 | Streamlit |
| 编排框架 | LangChain（LCEL） |
| 向量数据库 | Chroma |
| 向量化 | DashScope text-embedding-v4 |
| 大模型 | Qwen（DashScope） |
| 语言 | Python 3.12 |

## 系统架构

```
构建知识库：
  文档 → loader 读取 → cleaner 清洗 → splitter 分块 → embedder 向量化 → Chroma 入库

问答：
  问题 → 向量检索 Top-K → 拼装上下文 → Prompt → Qwen → 流式回答 + 引用出处
```

## 核心实现

### 1. 数据清洗流水线（`core/cleaner.py`）

| 步骤 | 做法 |
|---|---|
| 格式归一 | 统一换行符、合并连续空格 |
| 噪声过滤 | 正则匹配页码、目录点线、纯符号行 |
| 敏感信息脱敏 | 正则分组替换：手机号 `138****5678`、身份证保留前 6 后 4、邮箱保留首字母 |
| 重复条款去重 | 内容 MD5 哈希 + 集合判重，O(1) 查询 |

### 2. 文本分块（`core/splitter.py`）

- 中文优先的切分顺序：段落 → 句子 → 字符
- 默认 300 字/块、重叠 50 字，避免切分点落在句中导致语义割裂

### 3. 检索问答链（`core/chain.py`）

```python
chain = PROMPT | get_llm(streaming=True) | StrOutputParser()
stream = chain.stream({"context": context, "question": question, "history": history})
```

- System Prompt 限定「只依据参考资料回答」，`temperature=0.1` 降低幻觉
- 检索结果的 `doc_name` / `chunk_index` 随回答一起返回，用于展示引用

## 项目结构

```
handbook-rag/
├── app.py                    # 问答主界面
├── pages/
│   └── 1_知识库管理.py        # 上传、清洗预览、入库
├── core/
│   ├── loader.py             # 文档读取（txt/md/pdf）
│   ├── cleaner.py            # 数据清洗流水线
│   ├── splitter.py           # 文本分块
│   ├── embedder.py           # 向量化
│   ├── store.py              # Chroma 向量库封装
│   ├── chain.py              # 检索问答链
│   └── ui.py                 # 界面公共样式
├── data/                     # 示例文档
├── demo_clean.py             # 清洗效果演示
├── demo_index.py             # 分块入库与检索演示
├── demo_chat.py              # 问答链演示
├── requirements.txt
└── .env.example
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY

# 3. 启动应用
streamlit run app.py
```

浏览器打开 `http://localhost:8501`，先到「知识库管理」页上传手册或导入示例文档，再回到首页提问。

## 演示

命令行验证：

```bash
python -X utf8 demo_clean.py   # 查看清洗效果
python -X utf8 demo_index.py   # 分块、入库、检索
python -X utf8 demo_chat.py    # 完整问答流程
```

示例问答：

| 问题 | 回答 |
|---|---|
| 出差报销需要多久内提交？ | 出差结束后 7 个工作日内（第三章第 2 条） |
| 迟到多久算旷工？ | 超过 30 分钟视为旷工半天（第二章第 2 条） |
| 公司年假有几天？ | 手册中未找到相关内容 |

## 开发记录

- [x] D1 项目骨架 + 文档读取 + 数据清洗
- [x] D2 文本分块 + 向量化 + Chroma 入库
- [x] D3 检索问答链 + 流式输出 + 引用来源
- [x] D4 双页面界面
