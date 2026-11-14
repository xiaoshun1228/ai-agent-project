"""FastAPI 应用入口：注册接口、配置跨域、挂载前端页面。"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import chat, oss
from app.common.logger import setup_logging

# 初始化日志配置（控制台输出，格式见 common/logger.py）
setup_logging()

# 创建 FastAPI 应用，标题和版本会显示在 /docs 接口文档页
app = FastAPI(
    title="Personal Chief API",
    description="私厨",
    version="0.1.0",
)

# 跨域配置：允许浏览器扩展或前端页面直接调用接口
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # 开发阶段放开；生产环境建议改成具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册业务路由，统一挂到 /api/v1 前缀下
app.include_router(chat.router, prefix="/api/v1", tags=["对话"])
app.include_router(oss.router, prefix="/api/v1", tags=["申请上传签名url"])

# 前端静态资源目录（Next.js 构建产物）
static_dir = os.path.join(os.path.dirname(__file__), "static")


class SPAStaticFiles(StaticFiles):
    """单页应用静态文件服务：找不到文件时回退到 index.html。

    前端使用路由（如 /chat、/history）时，刷新页面会请求这些路径，
    磁盘上没有对应文件，需要回退到 index.html 交给前端路由处理。
    """

    async def get_response(self, path, scope):
        # Windows 上路径可能被转成反斜杠，统一换成 / 再判断
        clean_path = path.replace("\\", "/").lstrip("/")

        # 未匹配的 API 路径直接返回 404，不要回退到前端页面
        if clean_path == "api" or clean_path.startswith("api/"):
            raise StarletteHTTPException(status_code=404)

        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            # 旧版 Starlette 找不到文件时抛异常，这里回退到首页
            if exc.status_code == 404:
                return await super().get_response("index.html", scope)
            raise

        # 新版 Starlette 找不到文件时返回 404 响应（不抛异常），同样回退
        if response.status_code == 404:
            return await super().get_response("index.html", scope)

        return response


# 只有静态目录存在时才挂载，避免目录缺失导致启动失败
if os.path.exists(static_dir):
    app.mount("/", SPAStaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    # 直接运行本文件时启动服务：python -m app.main
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, reload=True)
