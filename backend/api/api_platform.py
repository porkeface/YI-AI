"""API密钥管理API

连接 ai.api_platform.api_keys.APIKeyManager 和 ai.api_platform.rate_limiter.APIRateLimiter，
提供密钥创建、验证、撤销、使用量查询接口。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

from ai.api_platform.api_keys import APIKeyManager
from ai.api_platform.rate_limiter import APIRateLimiter
from ai.api_platform.types import APIPermission

router = APIRouter(prefix="/api/api-platform", tags=["api-platform"])

# 权限字符串 -> 枚举映射
_PERM_MAP = {
    "divination": APIPermission.DIVINATION,
    "analysis": APIPermission.ANALYSIS,
    "history": APIPermission.HISTORY,
    "knowledge": APIPermission.KNOWLEDGE,
    "plugin": APIPermission.PLUGIN,
}


class CreateKeyRequest(BaseModel):
    """创建API密钥请求"""
    name: str = Field(..., description="密钥名称")
    owner_id: str = Field(..., description="所有者ID")
    permissions: list[str] = Field(
        default=["divination", "analysis", "history"],
        description="权限列表: divination / analysis / history / knowledge / plugin",
    )
    rate_limit: int = Field(60, description="每分钟请求限制")
    expires_in_days: int = Field(0, description="过期天数，0表示永不过期")


@router.post("/keys")
async def create_api_key(request: CreateKeyRequest):
    """创建API密钥

    原始密钥只在创建时返回一次，请妥善保存。
    """
    # 转换权限列表
    perms = []
    for p in request.permissions:
        perm = _PERM_MAP.get(p)
        if perm is None:
            raise HTTPException(
                status_code=400,
                detail=f"无效的权限: {p}，可选值: {list(_PERM_MAP.keys())}",
            )
        perms.append(perm)

    raw_key, info = APIKeyManager.create_key(
        name=request.name,
        owner_id=request.owner_id,
        permissions=tuple(perms),
        rate_limit=request.rate_limit,
        expires_in_days=request.expires_in_days,
    )

    return {
        "key": raw_key,
        "key_id": info.key_id,
        "name": info.name,
        "permissions": [p.value for p in info.permissions],
        "rate_limit": info.rate_limit,
        "message": "请妥善保存密钥，后续无法再次查看",
    }


@router.get("/keys")
async def list_api_keys(owner_id: str | None = None):
    """列出API密钥（不包含原始密钥）"""
    keys = APIKeyManager.list_keys(owner_id=owner_id)
    return {
        "keys": [
            {
                "key_id": k.key_id,
                "name": k.name,
                "owner_id": k.owner_id,
                "status": k.status.value,
                "permissions": [p.value for p in k.permissions],
                "rate_limit": k.rate_limit,
                "created_at": k.created_at,
                "expires_at": k.expires_at,
                "last_used_at": k.last_used_at,
            }
            for k in keys
        ]
    }


@router.delete("/keys/{key_id}")
async def revoke_api_key(key_id: str):
    """撤销API密钥"""
    success = APIKeyManager.revoke_key(key_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"密钥不存在: {key_id}")

    return {"status": "revoked", "key_id": key_id}


@router.get("/keys/{key_id}/usage")
async def get_key_usage(key_id: str, limit: int = 60):
    """获取密钥当前速率限制使用情况"""
    info = APIKeyManager.get_key_info(key_id)
    if info is None:
        raise HTTPException(status_code=404, detail=f"密钥不存在: {key_id}")

    usage = APIRateLimiter.get_usage(key_id, limit=info.rate_limit)
    return {
        "key_id": key_id,
        "limit": usage.limit,
        "remaining": usage.remaining,
        "reset_at": usage.reset_at,
    }


@router.post("/validate")
async def validate_key(api_key: str = Header(..., alias="X-API-Key")):
    """通过请求头验证API密钥"""
    info = APIKeyManager.validate_key(api_key)
    if info is None:
        raise HTTPException(status_code=401, detail="无效或已过期的API密钥")

    return {
        "valid": True,
        "key_id": info.key_id,
        "name": info.name,
        "permissions": [p.value for p in info.permissions],
    }


@router.get("/health")
async def api_platform_health():
    """API平台模块健康检查"""
    return {"status": "ok", "module": "api_platform", "total_keys": APIKeyManager.count()}
