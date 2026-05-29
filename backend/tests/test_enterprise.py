"""企业版模块测试"""

from __future__ import annotations

import pytest
from ai.enterprise.types import (
    TenantStatus,
    Role,
    Permission,
    ROLE_PERMISSIONS,
    Tenant,
    TenantUser,
    QuotaUsage,
)
from ai.enterprise.tenant_manager import TenantManager


class TestTenantManager:
    """租户管理器测试"""

    def setup_method(self):
        TenantManager.clear()

    def test_create_tenant(self):
        """创建租户"""
        tenant = TenantManager.create_tenant("测试公司")
        assert tenant.name == "测试公司"
        assert tenant.status == TenantStatus.ACTIVE
        assert TenantManager.count_tenants() == 1

    def test_get_tenant(self):
        """获取租户"""
        tenant = TenantManager.create_tenant("测试公司")
        fetched = TenantManager.get_tenant(tenant.tenant_id)
        assert fetched is not None
        assert fetched.name == "测试公司"

    def test_suspend_activate_tenant(self):
        """暂停/激活租户"""
        tenant = TenantManager.create_tenant("测试公司")
        TenantManager.suspend_tenant(tenant.tenant_id)
        t = TenantManager.get_tenant(tenant.tenant_id)
        assert t.status == TenantStatus.SUSPENDED

        TenantManager.activate_tenant(tenant.tenant_id)
        t = TenantManager.get_tenant(tenant.tenant_id)
        assert t.status == TenantStatus.ACTIVE

    def test_add_user(self):
        """添加用户"""
        tenant = TenantManager.create_tenant("测试公司", max_users=5)
        user = TenantManager.add_user(
            tenant.tenant_id, "user_1", "test@test.com", Role.ADMIN
        )
        assert user is not None
        assert user.role == Role.ADMIN
        assert TenantManager.count_users() == 1

    def test_add_user_limit(self):
        """用户数限制"""
        tenant = TenantManager.create_tenant("测试公司", max_users=2)
        TenantManager.add_user(tenant.tenant_id, "u1")
        TenantManager.add_user(tenant.tenant_id, "u2")
        result = TenantManager.add_user(tenant.tenant_id, "u3")
        assert result is None

    def test_remove_user(self):
        """移除用户"""
        tenant = TenantManager.create_tenant("测试公司")
        TenantManager.add_user(tenant.tenant_id, "user_1")
        assert TenantManager.remove_user("user_1") is True
        assert TenantManager.get_user("user_1") is None

    def test_update_role(self):
        """更新角色"""
        tenant = TenantManager.create_tenant("测试公司")
        TenantManager.add_user(tenant.tenant_id, "user_1", role=Role.VIEWER)
        TenantManager.update_role("user_1", Role.ADMIN)
        user = TenantManager.get_user("user_1")
        assert user.role == Role.ADMIN

    def test_list_tenant_users(self):
        """列出租户用户"""
        tenant = TenantManager.create_tenant("测试公司")
        TenantManager.add_user(tenant.tenant_id, "u1")
        TenantManager.add_user(tenant.tenant_id, "u2")

        users = TenantManager.list_tenant_users(tenant.tenant_id)
        assert len(users) == 2

    def test_has_permission(self):
        """权限检查"""
        tenant = TenantManager.create_tenant("测试公司")
        TenantManager.add_user(
            tenant.tenant_id, "user_1", role=Role.ANALYST
        )
        assert TenantManager.has_permission(
            "user_1", Permission.VIEW_ANALYTICS
        ) is True
        assert TenantManager.has_permission(
            "user_1", Permission.MANAGE_USERS
        ) is False

    def test_owner_has_all_permissions(self):
        """所有者拥有全部权限"""
        tenant = TenantManager.create_tenant("测试公司")
        TenantManager.add_user(
            tenant.tenant_id, "owner", role=Role.OWNER
        )
        for perm in Permission:
            assert TenantManager.has_permission("owner", perm) is True

    def test_suspended_tenant_no_permission(self):
        """暂停租户的用户无权限"""
        tenant = TenantManager.create_tenant("测试公司")
        TenantManager.add_user(tenant.tenant_id, "user_1")
        TenantManager.suspend_tenant(tenant.tenant_id)
        assert TenantManager.has_permission(
            "user_1", Permission.VIEW_ANALYTICS
        ) is False

    def test_get_quota_usage(self):
        """获取配额使用情况"""
        tenant = TenantManager.create_tenant("测试公司", max_users=10)
        TenantManager.add_user(tenant.tenant_id, "u1")
        TenantManager.add_user(tenant.tenant_id, "u2")

        quota = TenantManager.get_quota_usage(tenant.tenant_id)
        assert quota is not None
        assert quota.user_count == 2
        assert quota.max_users == 10

    def test_list_tenants(self):
        """列出租户"""
        TenantManager.create_tenant("公司A")
        TenantManager.create_tenant("公司B")
        tenants = TenantManager.list_tenants()
        assert len(tenants) == 2


class TestEnterpriseTypes:
    """企业版类型测试"""

    def test_tenant_frozen(self):
        """Tenant 不可变"""
        tenant = Tenant(tenant_id="test", name="测试")
        with pytest.raises(AttributeError):
            tenant.name = "新名称"  # type: ignore

    def test_tenant_user_frozen(self):
        """TenantUser 不可变"""
        user = TenantUser(user_id="u1", tenant_id="t1")
        with pytest.raises(AttributeError):
            user.role = Role.ADMIN  # type: ignore

    def test_role_permissions(self):
        """角色权限映射"""
        assert Permission.MANAGE_TENANT in ROLE_PERMISSIONS[Role.OWNER]
        assert Permission.MANAGE_TENANT not in ROLE_PERMISSIONS[Role.ADMIN]
        assert Permission.VIEW_ANALYTICS in ROLE_PERMISSIONS[Role.VIEWER]

    def test_tenant_status_enum(self):
        """租户状态枚举"""
        assert TenantStatus.ACTIVE.value == "活跃"
        assert TenantStatus.SUSPENDED.value == "已暂停"
        assert TenantStatus.TRIAL.value == "试用"

    def test_role_enum(self):
        """角色枚举"""
        assert Role.OWNER.value == "所有者"
        assert Role.ADMIN.value == "管理员"
        assert Role.VIEWER.value == "查看者"
