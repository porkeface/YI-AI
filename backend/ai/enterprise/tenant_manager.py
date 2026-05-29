"""租户管理器

管理多租户隔离、用户角色、配额。
线程安全 — 使用锁保护共享状态。
"""

from __future__ import annotations

import logging
import threading
import time

from ai.enterprise.types import (
    Permission,
    QuotaUsage,
    ROLE_PERMISSIONS,
    Role,
    Tenant,
    TenantStatus,
    TenantUser,
)

logger = logging.getLogger(__name__)


class TenantManager:
    """租户管理器

    classmethod-only API — 所有状态存储在模块级变量中。
    """

    # 模块级状态
    _tenants: dict[str, Tenant] = {}
    _users: dict[str, TenantUser] = {}  # user_id -> TenantUser
    _tenant_users: dict[str, set[str]] = {}  # tenant_id -> {user_ids}
    _lock = threading.Lock()

    # ---- 租户管理 ----

    @classmethod
    def create_tenant(
        cls,
        name: str,
        max_users: int = 10,
        max_api_calls_per_day: int = 10000,
    ) -> Tenant:
        """创建租户

        Args:
            name: 租户名称
            max_users: 最大用户数
            max_api_calls_per_day: 每日最大API调用数

        Returns:
            创建的租户
        """
        import secrets
        tenant_id = "tenant_" + secrets.token_hex(8)

        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            status=TenantStatus.ACTIVE,
            max_users=max_users,
            max_api_calls_per_day=max_api_calls_per_day,
            created_at=time.time(),
        )

        with cls._lock:
            cls._tenants[tenant_id] = tenant
            cls._tenant_users[tenant_id] = set()

        logger.info("tenant_created: %s (%s)", tenant_id, name)
        return tenant

    @classmethod
    def get_tenant(cls, tenant_id: str) -> Tenant | None:
        """获取租户信息"""
        with cls._lock:
            return cls._tenants.get(tenant_id)

    @classmethod
    def list_tenants(
        cls,
        status: TenantStatus | None = None,
    ) -> tuple[Tenant, ...]:
        """列出租户"""
        with cls._lock:
            results = []
            for t in cls._tenants.values():
                if status and t.status != status:
                    continue
                results.append(t)
            return tuple(results)

    @classmethod
    def suspend_tenant(cls, tenant_id: str) -> bool:
        """暂停租户"""
        return cls._update_tenant_status(tenant_id, TenantStatus.SUSPENDED)

    @classmethod
    def activate_tenant(cls, tenant_id: str) -> bool:
        """激活租户"""
        return cls._update_tenant_status(tenant_id, TenantStatus.ACTIVE)

    # ---- 用户管理 ----

    @classmethod
    def add_user(
        cls,
        tenant_id: str,
        user_id: str,
        email: str = "",
        role: Role = Role.VIEWER,
    ) -> TenantUser | None:
        """添加用户到租户

        Args:
            tenant_id: 租户ID
            user_id: 用户ID
            email: 邮箱
            role: 角色

        Returns:
            创建的用户，失败返回 None
        """
        with cls._lock:
            tenant = cls._tenants.get(tenant_id)
            if tenant is None:
                return None

            # 检查用户数限制
            current_users = len(cls._tenant_users.get(tenant_id, set()))
            if current_users >= tenant.max_users:
                logger.warning(
                    "tenant_user_limit: %s (%d/%d)",
                    tenant_id, current_users, tenant.max_users,
                )
                return None

            user = TenantUser(
                user_id=user_id,
                tenant_id=tenant_id,
                role=role,
                email=email,
                is_active=True,
            )

            cls._users[user_id] = user
            cls._tenant_users.setdefault(tenant_id, set()).add(user_id)

        logger.info("user_added: %s to %s as %s", user_id, tenant_id, role.value)
        return user

    @classmethod
    def remove_user(cls, user_id: str) -> bool:
        """移除用户"""
        with cls._lock:
            user = cls._users.get(user_id)
            if user is None:
                return False

            del cls._users[user_id]
            tenant_users = cls._tenant_users.get(user.tenant_id)
            if tenant_users:
                tenant_users.discard(user_id)

        return True

    @classmethod
    def get_user(cls, user_id: str) -> TenantUser | None:
        """获取用户信息"""
        with cls._lock:
            return cls._users.get(user_id)

    @classmethod
    def update_role(cls, user_id: str, role: Role) -> bool:
        """更新用户角色"""
        with cls._lock:
            user = cls._users.get(user_id)
            if user is None:
                return False
            cls._users[user_id] = TenantUser(
                user_id=user.user_id,
                tenant_id=user.tenant_id,
                role=role,
                email=user.email,
                is_active=user.is_active,
            )
            return True

    @classmethod
    def list_tenant_users(cls, tenant_id: str) -> tuple[TenantUser, ...]:
        """列出租户用户"""
        with cls._lock:
            user_ids = cls._tenant_users.get(tenant_id, set())
            return tuple(
                cls._users[uid]
                for uid in user_ids
                if uid in cls._users
            )

    # ---- 权限检查 ----

    @classmethod
    def has_permission(
        cls,
        user_id: str,
        permission: Permission,
    ) -> bool:
        """检查用户是否有指定权限

        Args:
            user_id: 用户ID
            permission: 权限

        Returns:
            是否有权限
        """
        with cls._lock:
            user = cls._users.get(user_id)
            if user is None or not user.is_active:
                return False

            # 检查租户状态
            tenant = cls._tenants.get(user.tenant_id)
            if tenant is None or tenant.status == TenantStatus.SUSPENDED:
                return False

        role_perms = ROLE_PERMISSIONS.get(user.role, ())
        return permission in role_perms

    # ---- 配额 ----

    @classmethod
    def get_quota_usage(
        cls,
        tenant_id: str,
        api_calls_today: int = 0,
    ) -> QuotaUsage | None:
        """获取配额使用情况"""
        with cls._lock:
            tenant = cls._tenants.get(tenant_id)
            if tenant is None:
                return None

            user_count = len(cls._tenant_users.get(tenant_id, set()))

        return QuotaUsage(
            tenant_id=tenant_id,
            user_count=user_count,
            max_users=tenant.max_users,
            api_calls_today=api_calls_today,
            max_api_calls_per_day=tenant.max_api_calls_per_day,
        )

    # ---- 内部方法 ----

    @classmethod
    def _update_tenant_status(
        cls,
        tenant_id: str,
        status: TenantStatus,
    ) -> bool:
        """更新租户状态"""
        with cls._lock:
            tenant = cls._tenants.get(tenant_id)
            if tenant is None:
                return False
            cls._tenants[tenant_id] = Tenant(
                tenant_id=tenant.tenant_id,
                name=tenant.name,
                status=status,
                max_users=tenant.max_users,
                max_api_calls_per_day=tenant.max_api_calls_per_day,
                created_at=tenant.created_at,
            )
            return True

    @classmethod
    def count_tenants(cls) -> int:
        """获取租户总数"""
        with cls._lock:
            return len(cls._tenants)

    @classmethod
    def count_users(cls) -> int:
        """获取用户总数"""
        with cls._lock:
            return len(cls._users)

    @classmethod
    def clear(cls) -> None:
        """清空所有数据（用于测试）"""
        with cls._lock:
            cls._tenants.clear()
            cls._users.clear()
            cls._tenant_users.clear()
