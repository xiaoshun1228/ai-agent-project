#定义模型
import os
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
#使用支持识图的 qwen3-vl-plus(qwen-plus 只能聊天, 不能看图)
model = init_chat_model(
    "qwen3-vl-plus",
    model_provider="openai",
    #接口地址优先从环境变量读取, 没设置就用官方默认地址
    base_url=os.environ.get(
        "DASHSCOPE_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ),
    api_key=os.environ.get("DASHSCOPE_API_KEY"),
    #default_headers 用于绕开本机 httpx2 解压 brotli 响应的 bug
    default_headers={"Accept-Encoding": "identity"},
)
#定义工具(API Key 会自动从环境变量 TAVILY_API_KEY 读取)
from langchain_tavily import TavilySearch
web_search = TavilySearch(max_results=5, topic='general')
#添加记忆管理(仅本地直接运行时启用; langgraph dev 里由平台自动管理持久化)
checkpointer = None
if __name__ == "__main__":
    import sqlite3
    from pathlib import Path
    from langgraph.checkpoint.sqlite import SqliteSaver
    #连接数据库(数据库文件和脚本放在同一个目录, 文件不存在会自动创建)
    db_path = Path(__file__).resolve().parent / "个人私厨.db"
    connection = sqlite3.connect(db_path, check_same_thread=False)
    #初始化checkpointer
    checkpointer = SqliteSaver(connection)
    #自动建表
    checkpointer.setup()
#定义智能体
from langchain.agents import create_agent
system_prompt = """
1.你是一名私人厨师。收到用户提供的食材照片或清单后，请按以下流程操作:
1.识别和评估食材:若用户提供照片，首先辨识所有可见食材。基于食材的外观状态，评估其新鲜度与可用量，整理出一份“当前可用
食材清单”。
2.智能食谱检索:优先调用web_search工具，以“可用食材清单”为核心关键词，查找可行菜谱。
3.多维度评估与排序:从营养价值和制作难度两个维度对检索到的候选食谱进行量化打分，并根据得分排序，制作简单且营养丰富的排
名靠前。
4.结构化方案输出:把排序后的食谱整理为一份结构清晰的建议报告，要包含食谱信息、得分、推荐理由、食谱的参考图片，帮助用户
快速做出决策。
请严格按照流程，优先调用web_search 工具搜索食谱，搜索不到的情况下才能自己发挥。
"""
agent = create_agent(
    model=model,
    tools=[web_search],
    system_prompt=system_prompt,
    checkpointer=checkpointer,
)
#测试(只有直接运行本文件时才执行; langgraph dev 导入时不会跑这些测试)
if __name__ == "__main__":
    from langchain.messages import HumanMessage

    #图片必须是"可直接访问的图片直链", 网页地址(如 imageshop 的页面链接)模型读不了
    image_url = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600"

    multimodal_message = HumanMessage(content=[
        {"type": "text", "text": "看看能帮我做什么"},
        #OpenAI 兼容接口的图片格式是 image_url 里再嵌套 url
        {"type": "image_url", "image_url": {"url": image_url}},
    ])
    #thread_id 相当于会话编号: 换一个新编号就是一段全新的对话(避免复用旧数据)
    config = {"configurable": {"thread_id": "kitchen_1"}}
    response = agent.invoke({"messages": [multimodal_message]}, config=config)
    #注意: 返回字典的键是 "messages", 不是 "message"
    for message in response["messages"]:
        message.pretty_print()

    response = agent.invoke(
        {"messages": [HumanMessage(content="我喜欢第三道菜，可以说的更详细点吗")]},
        config=config,
    )
    #只打印最后一条回复(历史消息已经在上一次打印过了)
    response["messages"][-1].pretty_print()

    #关闭数据库连接
    connection.close()
