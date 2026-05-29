"""企业管理API

连接 ai.enterprise.tenant_manager.TenantManager，
提供租户管理、用户管理、配额查询接口。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai.enterprise.tenant_manager import TenantManager
from ai.enterprise.types import Role

router = APIRouter(prefix="/api/enterprise", tags=["enterprise"])

# 角色字符串 -> 枚举映射
_ROLE_MAP = {
    "owner": Role.OWNER,
    "admin": Role.ADMIN,
    "analyst": Role.ANALYST,
    "viewer": Role.VIEWER,
}


class CreateTenantRequest(BaseModel):
    """创建租户请求"""
    name: str = Field(..., description="租户名称")
    max_users: int = Field(10, description="最大用户数")
    max_api_calls_per_day: int = Field(10000, description="每日最大API调用数")


class AddUserRequest(BaseModel):
    """添加用户请求"""
    user_id: str = Field(..., description="用户ID")
    email: str = Field("", description="邮箱")
    role: str = Field("viewer", description="角色: owner / admin / analyst / viewer")


@router.post("/tenants")
async def create_tenant(request: CreateTenantRequest):
    """创建租户"""
    tenant = TenantManager.create_tenant(
        name=request.name,
        max_users=request.max_users,
        max_api_calls_per_day=request.max_api_calls_per_day,
    )
    return {
        "tenant": {
            "tenant_id": tenant.tenant_id,
            "name": tenant.name,
            "status": tenant.status.value,
            "max_users": tenant.max_users,
            "max_api_calls_per_day": tenant.max_api_calls_per_day,
            "created_at": tenant.created_at,
        }
    }


@router.get("/tenants")
async def list_tenants():
    """列出所有租户"""
    tenants = TenantManager.list_tenants()
    return {
        "tenants": [
            {
                "tenant_id": t.tenant_id,
                "name": t.name,
                "status": t.status.value,
                "max_users": t.max_users,
                "max_api_calls_per_day": t.max_api_calls_per_day,
                "created_at": t.created_at,
            }
            for t in tenants
        ]
    }


@router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: str):
    """获取租户详情"""
    tenant = TenantManager.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail=f"租户不存在: {tenant_id}")

    return {
        "tenant": {
            "tenant_id": tenant.tenant_id,
            "name": tenant.name,
            "status": tenant.status.value,
            "max_users": tenant.max_users,
            "max_api_calls_per_day": tenant.max_api_calls_per_day,
            "created_at": tenant.created_at,
        }
    }


@router.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(tenant_id: str):
    """暂停租户"""
    success = TenantManager.suspend_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"租户不存在: {tenant_id}")
    return {"status": "suspended", "tenant_id": tenant_id}


@router.post("/tenants/{tenant_id}/activate")
async def activate_tenant(tenant_id: str):
    """激活租户"""
    success = TenantManager.activate_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"租户不存在: {tenant_id}")
    return {"status": "activated", "tenant_id": tenant_id}


@router.post("/tenants/{tenant_id}/users")
async def add_user(tenant_id: str, request: AddUserRequest):
    """添加用户到租户"""
    role = _ROLE_MAP.get(request.role)
    if role is None:
        raise HTTPException(
            status_code=400,
            detail=f"无效的角色: {request.role}，可选值: {list(_ROLE_MAP.keys())}",
        )

    user = TenantManager.add_user(
        tenant_id=tenant_id,
        user_id=request.user_id,
        email=request.email,
        role=role,
    )
    if user is None:
        raise HTTPException(
            status_code=400,
            detail="添加用户失败：租户不存在或已达用户上限",
        )

    return {
        "user": {
            "user_id": user.user_id,
            "tenant_id": user.tenant_id,
            "role": user.role.value,
            "email": user.email,
            "is_active": user.is_active,
        }
    }


@router.get("/tenants/{tenant_id}/users")
async def list_users(tenant_id: str):
    """列出租户用户"""
    # 先检查租户是否存在
    tenant = TenantManager.get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail=f"租户不存在: {tenant_id}")

    users = TenantManager.list_tenant_users(tenant_id)
    return {
        "users": [
            {
                "user_id": u.user_id,
                "tenant_id": u.tenant_id,
                "role": u.role.value,
                "email": u.email,
                "is_active": u.is_active,
            }
            for u in users
        ]
    }


@router.get("/tenants/{tenant_id}/quota")
async def get_quota(tenant_id: str, api_calls_today: int = 0):
    """获取租户配额使用情况"""
    quota = TenantManager.get_quota_usage(tenant_id, api_calls_today=api_calls_today)
    if quota is None:
        raise HTTPException(status_code=404, detail=f"租户不存在: {tenant_id}")

    return {
        "quota": {
            "tenant_id": quota.tenant_id,
            "user_count": quota.user_count,
            "max_users": quota.max_users,
            "api_calls_today": quota.api_calls_today,
            "max_api_calls_per_day": quota.max_api_calls_per_day,
        }
    }


@router.delete("/users/{user_id}")
async def remove_user(user_id: str):
    """移除用户"""
    success = TenantManager.remove_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"用户不存在: {user_id}")
    return {"status": "removed", "user_id": user_id}


@router.get("/health")
async def enterprise_health():
    """企业管理模块健康检查"""
    return {
        "status": "ok",
        "module": "enterprise",
        "total_tenants": TenantManager.count_tenants(),
        "total_users": TenantManager.count_users(),
    }
