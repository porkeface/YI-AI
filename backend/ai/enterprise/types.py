"""企业版类型定义"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TenantStatus(str, Enum):
    """租户状态"""
    ACTIVE = "活跃"
    SUSPENDED = "已暂停"
    TRIAL = "试用"
    EXPIRED = "已过期"


class Role(str, Enum):
    """用户角色"""
    OWNER = "所有者"
    ADMIN = "管理员"
    ANALYST = "分析师"
    VIEWER = "查看者"


class Permission(str, Enum):
    """权限"""
    MANAGE_TENANT = "管理租户"
    MANAGE_USERS = "管理用户"
    VIEW_ANALYTICS = "查看分析"
    USE_API = "使用API"
    EXPORT_DATA = "导出数据"
    MANAGE_PLUGINS = "管理插件"


# 角色权限映射
ROLE_PERMISSIONS: dict[Role, tuple[Permission, ...]] = {
    Role.OWNER: (
        Permission.MANAGE_TENANT,
        Permission.MANAGE_USERS,
        Permission.VIEW_ANALYTICS,
        Permission.USE_API,
        Permission.EXPORT_DATA,
        Permission.MANAGE_PLUGINS,
    ),
    Role.ADMIN: (
        Permission.MANAGE_USERS,
        Permission.VIEW_ANALYTICS,
        Permission.USE_API,
        Permission.EXPORT_DATA,
        Permission.MANAGE_PLUGINS,
    ),
    Role.ANALYST: (
        Permission.VIEW_ANALYTICS,
        Permission.USE_API,
        Permission.EXPORT_DATA,
    ),
    Role.VIEWER: (
        Permission.VIEW_ANALYTICS,
    ),
}


@dataclass(frozen=True)
class Tenant:
    """租户

    Attributes:
        tenant_id: 租户ID
        name: 租户名称
        status: 租户状态
        max_users: 最大用户数
        max_api_calls_per_day: 每日最大API调用数
        created_at: 创建时间戳
    """
    tenant_id: str
    name: str
    status: TenantStatus = TenantStatus.ACTIVE
    max_users: int = 10
    max_api_calls_per_day: int = 10000
    created_at: float = 0.0


@dataclass(frozen=True)
class TenantUser:
    """租户用户

    Attributes:
        user_id: 用户ID
        tenant_id: 租户ID
        role: 角色
        email: 邮箱
        is_active: 是否激活
    """
    user_id: str
    tenant_id: str
    role: Role = Role.VIEWER
    email: str = ""
    is_active: bool = True


@dataclass(frozen=True)
class QuotaUsage:
    """配额使用情况

    Attributes:
        tenant_id: 租户ID
        user_count: 当前用户数
        max_users: 最大用户数
        api_calls_today: 今日API调用数
        max_api_calls_per_day: 每日最大调用数
    """
    tenant_id: str
    user_count: int = 0
    max_users: int = 10
    api_calls_today: int = 0
    max_api_calls_per_day: int = 10000
