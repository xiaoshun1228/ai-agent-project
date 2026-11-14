import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api.v1 import chat
from app.api.v1 import oss
from app.common.logger import setup_logging

# 初始化日志配置
setup_logging()

app = FastAPI(
    title="Personal Chief API",
    description="私厨",
    version="0.1.0"
)

# 1. 配置跨域资源共享 (CORS)
# 插件开发中，由于请求来自浏览器扩展环境，必须正确配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议指定插件的 ID 或具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2.挂载路由
app.include_router(chat.router, prefix="/api/v1", tags=["对话"])
app.include_router(oss.router, prefix="/api/v1", tags=["申请上传签名url"])

# 3.挂载前端资源(放在 API 路由之后: 先匹配 API, 其余请求交给静态文件)
static_dir = os.path.join(os.path.dirname(__file__), "static")


class SPAStaticFiles(StaticFiles):
    """静态文件服务: 找不到文件时回退到 index.html, 支持前端单页应用路由"""

    async def get_response(self, path, scope):
        # 未匹配的 API 路径直接返回 404, 不回退到前端页面
        #Windows 上路径可能被 normpath 转成反斜杠, 统一换成 / 再判断
        clean_path = path.replace("\\", "/").lstrip("/")
        if clean_path == "api" or clean_path.startswith("api/"):
            raise StarletteHTTPException(status_code=404)
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404:
                return await super().get_response("index.html", scope)
            raise
        # 新版 Starlette 找不到文件时返回 404 响应(不抛异常), 这里回退到前端首页
        if response.status_code == 404:
            return await super().get_response("index.html", scope)
        return response


if os.path.exists(static_dir):
    app.mount("/", SPAStaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # 启动命令：python -m app.main
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, reload=True)
