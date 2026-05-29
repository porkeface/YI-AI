"""企业版模块

企业级功能，包括：
- TenantManager: 租户管理器（多租户隔离、RBAC、配额）
- 类型定义: 租户、用户、角色、权限
"""

from ai.enterprise.tenant_manager import TenantManager
from ai.enterprise.types import (
    TenantStatus,
    Role,
    Permission,
    ROLE_PERMISSIONS,
    Tenant,
    TenantUser,
    QuotaUsage,
)

__all__ = [
    # 核心
    "TenantManager",
    # 类型
    "TenantStatus",
    "Role",
    "Permission",
    "ROLE_PERMISSIONS",
    "Tenant",
    "TenantUser",
    "QuotaUsage",
]
