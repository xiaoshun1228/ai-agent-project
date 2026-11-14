"""OSS 预签名上传接口：前端拿签名直传阿里云，图片不经过后端。"""

import os
from datetime import timedelta
from pathlib import Path

import alibabacloud_oss_v2 as oss
from alibabacloud_oss_v2.exceptions import CredentialsEmptyError
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException

# 明确加载项目根目录的 .env，并覆盖系统里可能残留的旧 OSS 环境变量
load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=True)

router = APIRouter()

# OSS 配置
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "oss-cn-beijing.aliyuncs.com")
OSS_BUCKET = os.getenv("OSS_BUCKET")

# 常见图片类型映射，根据扩展名设置 Content-Type
CONTENT_TYPE_MAP = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}


def get_oss_client():
    """创建 OSS 客户端。

    凭证从环境变量读取（ALIBABA_CLOUD_ACCESS_KEY_ID / SECRET）。
    未配置凭证时给出明确提示，不影响服务启动。
    """
    try:
        credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()
    except CredentialsEmptyError:
        raise HTTPException(
            status_code=503,
            detail="未配置 OSS 凭证, 请设置环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID 和 ALIBABA_CLOUD_ACCESS_KEY_SECRET",
        )

    cfg = oss.config.load_default()
    cfg.credentials_provider = credentials_provider
    # 必须指定 Region，SDK 会根据 Region 自动构造访问域名
    cfg.region = os.getenv("OSS_REGION", "cn-beijing")
    return oss.Client(cfg)


@router.get("/oss/presign")
def presign_upload(filename: str):
    """生成图片上传预签名 URL。

    参数:
        filename: 要上传的文件名（决定 Content-Type 和对象 Key）
    返回:
        uploadUrl: 前端用来 PUT 上传的签名地址
        contentType: 上传时要带的 Content-Type
        accessUrl: 上传完成后可直接访问的图片地址
    """
    # 根据扩展名判断 Content-Type
    ext = filename.split(".")[-1].lower() if "." in filename else "jpg"
    content_type = CONTENT_TYPE_MAP.get(ext, "application/octet-stream")

    # 没配置 bucket 时直接报错
    if not OSS_BUCKET:
        raise HTTPException(status_code=503, detail="未配置 OSS_BUCKET 环境变量")

    client = get_oss_client()

    # 生成预签名上传地址，有效期 1 小时
    pre_result = client.presign(
        oss.PutObjectRequest(
            bucket=OSS_BUCKET,
            key=filename,
            content_type=content_type,
        ),
        expires=timedelta(seconds=3600),
    )

    # 返回上传地址和上传后的访问地址
    return {
        "uploadUrl": pre_result.url.strip('"'),
        "contentType": content_type,
        "accessUrl": f"https://{OSS_BUCKET}.{OSS_ENDPOINT}/{filename}",
    }
