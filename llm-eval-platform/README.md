# 轻量化大模型 RAG / Agent 自动化评测中台

一个可运行的 AI 应用评测平台：管理评测用例、批量执行评测、用大模型自动打分、
可视化对比结果、支持人工复核回流。

面向 RAG 问答、Agent 工具调用、客服合规三类场景，核心指标：
**召回率、准确率、幻觉率、合规率**。

---

## 一、功能特性

| 功能 | 说明 |
|---|---|
| 评测用例管理 | 新增、编辑、删除、版本管理（编辑自动升版本） |
| 三类评测 | RAG 问答、Agent 工具调用、客服合规 |
| LLM-as-Judge | 用大模型自动打分，输出四项指标 |
| 批量评测 | 多选用例一次跑完，实时进度 |
| 可视化报表 | 总体指标、按类型/模型对比、人工 vs 自动对比、趋势 |
| 人工复核回流 | 人工打分写回数据库，可与自动分对比 |
| 双形态交付 | Streamlit 界面 + FastAPI 接口，共用核心逻辑 |

---

## 二、技术栈

| 模块 | 技术 |
|---|---|
| 后端接口 | FastAPI |
| 界面 | Streamlit |
| 编排 | LangChain |
| 大模型 | Qwen（DashScope） |
| 自动评分 | LLM-as-Judge（Qwen 作为评委） |
| 数据库 | SQLite |
| 向量检索 | Chroma |
| 数据处理 | pandas |

---

## 三、项目结构

```
llm-eval-platform/
├── app.py                      # 总览页（Streamlit）
├── pages/
│   ├── 1_用例管理.py            # 增删改查、版本管理
│   ├── 2_执行评测.py            # 批量执行
│   ├── 3_结果分析.py            # 可视化报表
│   └── 4_人工复核.py            # 人工打分回流
├── api.py                      # FastAPI 接口
├── core/
│   ├── config.py               # 配置
│   ├── models.py               # 数据模型
│   ├── db.py                   # SQLite 存取
│   ├── judge.py                # LLM-as-Judge 打分
│   ├── metrics.py              # 指标聚合
│   ├── evaluators.py           # 三类评测器
│   ├── runner.py               # 批量调度
│   └── report.py               # 报表与导出
├── data/
│   ├── sample_cases.json       # 示例用例
│   └── eval.db                 # SQLite（首次运行自动生成）
├── import_sample.py            # 导入示例用例
├── requirements.txt
└── .env.example
```

---

## 四、快速开始

### 1. 环境准备

```bash
cd D:\pycharm_work\llm-eval-platform

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 配置密钥

```bash
copy .env.example .env
```

用记事本打开 `.env`，填写：

```
DASHSCOPE_API_KEY=你的通义千问Key
```

### 3. 导入示例用例

```bash
python import_sample.py
```

会导入 9 条用例（RAG / Agent / 合规各 3 条）。

### 4. 启动界面

```bash
streamlit run app.py
```

浏览器打开 `http://localhost:8501`。

### 5. 可选：启动 API 服务

```bash
.venv\Scripts\python.exe -m uvicorn api:app --reload
```

或先激活虚拟环境再执行 `uvicorn api:app --reload`。

- 服务地址：`http://127.0.0.1:8000`
- 接口文档：`http://127.0.0.1:8000/docs`（访问根地址会自动跳转到这里）
- ReDoc 文档：`http://127.0.0.1:8000/redoc`

---

## 五、使用教程

### 页面 1：总览

显示用例数、评测次数、复核次数，以及最近 20 条评测结果。

### 页面 2：用例管理

- 顶部可按类型筛选
- 「新增用例」填写问题、参考答案、参考资料（RAG 用）、期望工具（Agent 用）
- 「编辑用例」保存后版本号自动 +1
- 「删除用例」是软删除，历史评测记录保留

### 页面 3：执行评测

1. 选择类型（可选）
2. 多选要评测的用例
3. 确认被测模型（默认 qwen-plus）
4. 点「开始评测」，进度条实时更新
5. 完成后查看结果表格，展开可看每条详情

### 页面 4：结果分析

- 总体四项指标
- 按评测类型对比（柱状图）
- 按模型对比（需要跑过多个模型）
- 人工复核 vs 自动评分对比
- 一键导出 CSV

### 页面 5：人工复核

1. 选择一条评测记录
2. 查看问题、参考答案、模型预测、自动评分
3. 用四个滑块给出人工分
4. 填写复核意见后提交
5. 复核记录会出现在下方，也会参与「结果分析」的对比

---

## 六、评测原理

### 三类评测怎么跑

| 类型 | 流程 |
|---|---|
| RAG | 参考资料存入 Chroma → 检索相关片段 → Qwen 基于片段回答 |
| Agent | 给出工具列表 → Qwen 判断该调哪个工具 → 对比期望工具 |
| 合规 | Qwen 以客服身份回答 → 评委检查是否违反合规要求 |

### LLM-as-Judge 怎么打分

评委（Qwen）接收：问题、参考答案、AI 回答、参考资料，
输出严格 JSON：

```json
{"recall": 0.8, "accuracy": 0.9, "hallucination": 0.1, "compliance": 1.0, "reason": "..."}
```

程序解析 JSON 后存入数据库；解析失败时使用默认中性分（0.5），并记录原因。

### 指标含义

| 指标 | 含义 | 方向 |
|---|---|---|
| 召回率 | 参考答案的关键信息被覆盖多少 | 越高越好 |
| 准确率 | 回答与参考答案语义是否一致 | 越高越好 |
| 幻觉率 | 回答中编造内容的比例 | **越低越好** |
| 合规率 | 是否符合客服合规要求 | 越高越好 |

---

## 七、API 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 自动跳转到接口文档 `/docs` |
| GET | `/health` | 健康检查 |
| POST | `/cases` | 新增用例 |
| GET | `/cases` | 查询用例 |
| DELETE | `/cases/{id}` | 删除用例 |
| POST | `/run` | 批量执行评测 |
| GET | `/runs` | 查询评测结果 |
| POST | `/reviews` | 提交人工复核 |
| GET | `/reviews` | 查询复核记录 |
| GET | `/report` | 汇总报表 |
| GET | `/export.csv` | 导出 CSV |

---

## 八、常见问题

**Q：评测很慢？**
A：每条用例要调用 2 次模型（生成 + 评委），RAG 还要调向量化。
建议每次跑 5~10 条，避免长时间等待。

**Q：评分不稳定？**
A：评委温度设为 0，但大模型仍有轻微波动。
对关键用例可以用人工复核打分回流。

**Q：数据库在哪？**
A：`data/eval.db`，首次运行自动创建。删除它可重置所有数据。

**Q：怎么换评委模型？**
A：在 `.env` 里修改 `JUDGE_MODEL`， например换成 qwen-max 提升评分质量。

**Q：Chroma 数据存哪？**
A：RAG 评测用的是临时集合，不落盘；`data/chroma_tmp/` 已被 `.gitignore` 排除。

**Q：启动 API 后浏览器打不开或显示 404？**
A：请访问 `http://127.0.0.1:8000/docs`。根地址 `/` 已配置自动跳转到文档。
如果根地址仍返回 404，通常是 8000 端口上残留了旧的 uvicorn 进程（`Ctrl+C` 只结束了父进程，子进程成了孤儿），
请求被随机分发到旧代码。先确认端口占用：

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select-Object ProcessId,CommandLine
```

找到残留的 uvicorn/Python 进程后，用 `taskkill /F /PID <PID>` 结束，再重新启动服务。
也可以直接换端口避开占用：`uvicorn api:app --reload --port 8010`，访问 `http://127.0.0.1:8010/docs`。

**Q：打开 `/docs` 是空白页？**
A：Swagger UI 的 JS/CSS 默认从 `cdn.jsdelivr.net` 加载，国内网络可能很慢或被拦截。
可将文档页资源改为国内 CDN 或本地静态文件。
