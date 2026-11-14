import alibabacloud_oss_v2 as oss
from alibabacloud_oss_v2.exceptions import CredentialsEmptyError
from fastapi import APIRouter, HTTPException
from datetime import timedelta
import os
from pathlib import Path
# 加载环境变量
from dotenv import load_dotenv

# 明确加载项目根目录的 .env, 并覆盖系统里可能残留的旧 OSS 环境变量
load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=True)
router = APIRouter()

# OSS 域名配置
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "oss-cn-beijing.aliyuncs.com")
OSS_BUCKET = os.getenv("OSS_BUCKET")


def get_oss_client():
    """按需创建 OSS 客户端; 未配置凭证时给出明确提示, 不影响服务启动"""
    try:
        credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()
    except CredentialsEmptyError:
        raise HTTPException(
            status_code=503,
            detail="未配置 OSS 凭证, 请设置环境变量 OSS_ACCESS_KEY_ID 和 OSS_ACCESS_KEY_SECRET",
        )
    cfg = oss.config.load_default()
    cfg.credentials_provider = credentials_provider
    # 必须指定Region ID，SDK会根据Region自动构造HTTPS访问域名
    cfg.region = os.getenv("OSS_REGION", "cn-beijing")
    return oss.Client(cfg)


@router.get("/oss/presign")
def chat_endpoint(filename: str):
    # 根据文件扩展名判断 Content-Type
    content_type_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    ext = filename.split(".")[-1].lower() if "." in filename else "jpg"
    content_type = content_type_map.get(ext, "application/octet-stream")

    if not OSS_BUCKET:
        raise HTTPException(status_code=503, detail="未配置 OSS_BUCKET 环境变量")

    client = get_oss_client()
    pre_result = client.presign(oss.PutObjectRequest(
        bucket=OSS_BUCKET,
        key=filename,
        content_type=content_type,
    ), expires=timedelta(seconds=3600))

    # 返回上传 URL 和可访问的图片路径
    return {
        "uploadUrl": pre_result.url.strip('"'),
        "contentType": content_type,
        "accessUrl": f"https://{OSS_BUCKET}.{OSS_ENDPOINT}/{filename}"
    }
