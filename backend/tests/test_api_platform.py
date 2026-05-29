"""API平台测试

覆盖：API密钥管理、速率限制器。
"""

from __future__ import annotations

import time
import pytest
from ai.api_platform.types import (
    APIKeyStatus,
    APIPermission,
    APIKeyInfo,
    RateLimitInfo,
    APIUsageRecord,
)
from ai.api_platform.api_keys import APIKeyManager
from ai.api_platform.rate_limiter import APIRateLimiter


class TestAPIKeyManager:
    """API密钥管理器测试"""

    def setup_method(self):
        APIKeyManager.clear()

    def test_create_key(self):
        """创建密钥"""
        raw_key, info = APIKeyManager.create_key(
            "测试密钥", "user_1"
        )
        assert raw_key.startswith("yi_")
        assert info.name == "测试密钥"
        assert info.owner_id == "user_1"
        assert info.status == APIKeyStatus.ACTIVE
        assert APIKeyManager.count() == 1

    def test_validate_key(self):
        """验证密钥"""
        raw_key, info = APIKeyManager.create_key("测试", "user_1")
        validated = APIKeyManager.validate_key(raw_key)
        assert validated is not None
        assert validated.key_id == info.key_id

    def test_validate_invalid_key(self):
        """验证无效密钥"""
        assert APIKeyManager.validate_key("invalid_key") is None

    def test_revoke_key(self):
        """撤销密钥"""
        raw_key, info = APIKeyManager.create_key("测试", "user_1")
        result = APIKeyManager.revoke_key(info.key_id)
        assert result is True
        # 验证已撤销
        assert APIKeyManager.validate_key(raw_key) is None

    def test_expired_key(self):
        """过期密钥"""
        raw_key, info = APIKeyManager.create_key(
            "测试", "user_1", expires_in_days=0
        )
        # 手动设置过期时间为过去
        expired_info = APIKeyInfo(
            key_id=info.key_id,
            key_hash=info.key_hash,
            name=info.name,
            owner_id=info.owner_id,
            status=APIKeyStatus.ACTIVE,
            permissions=info.permissions,
            rate_limit=info.rate_limit,
            created_at=time.time() - 100000,
            expires_at=time.time() - 10000,
        )
        APIKeyManager._keys[info.key_id] = expired_info
        APIKeyManager._hash_to_id[info.key_hash] = info.key_id

        assert APIKeyManager.validate_key(raw_key) is None

    def test_list_keys(self):
        """列出密钥"""
        APIKeyManager.create_key("key1", "user_1")
        APIKeyManager.create_key("key2", "user_1")
        APIKeyManager.create_key("key3", "user_2")

        all_keys = APIKeyManager.list_keys()
        assert len(all_keys) == 3

        user1_keys = APIKeyManager.list_keys(owner_id="user_1")
        assert len(user1_keys) == 2

    def test_has_permission(self):
        """权限检查"""
        _, info = APIKeyManager.create_key(
            "测试", "user_1",
            permissions=(APIPermission.DIVINATION, APIPermission.HISTORY),
        )
        assert APIKeyManager.has_permission(info, APIPermission.DIVINATION) is True
        assert APIKeyManager.has_permission(info, APIPermission.ANALYSIS) is False

    def test_custom_permissions(self):
        """自定义权限"""
        _, info = APIKeyManager.create_key(
            "测试", "user_1",
            permissions=(APIPermission.DIVINATION,),
        )
        assert info.permissions == (APIPermission.DIVINATION,)

    def test_custom_rate_limit(self):
        """自定义速率限制"""
        _, info = APIKeyManager.create_key(
            "测试", "user_1", rate_limit=100
        )
        assert info.rate_limit == 100


class TestAPIRateLimiter:
    """速率限制器测试"""

    def setup_method(self):
        APIRateLimiter.clear()

    def test_consume_within_limit(self):
        """限制内消费"""
        result = APIRateLimiter.check_and_consume("key1", 5)
        assert result.remaining == 4
        assert result.limit == 5

    def test_consume_exceed_limit(self):
        """超限消费"""
        for _ in range(5):
            APIRateLimiter.check_and_consume("key1", 5)

        result = APIRateLimiter.check_and_consume("key1", 5)
        assert result.remaining == 0

    def test_independent_keys(self):
        """不同密钥独立限流"""
        APIRateLimiter.check_and_consume("key1", 5)
        result = APIRateLimiter.check_and_consume("key2", 5)
        assert result.remaining == 4

    def test_get_usage(self):
        """获取使用情况"""
        APIRateLimiter.check_and_consume("key1", 10)
        APIRateLimiter.check_and_consume("key1", 10)

        usage = APIRateLimiter.get_usage("key1", 10)
        assert usage.remaining == 8

    def test_get_usage_empty(self):
        """空使用情况"""
        usage = APIRateLimiter.get_usage("new_key", 10)
        assert usage.remaining == 10

    def test_reset(self):
        """重置限制"""
        for _ in range(5):
            APIRateLimiter.check_and_consume("key1", 5)

        APIRateLimiter.reset("key1")
        result = APIRateLimiter.check_and_consume("key1", 5)
        assert result.remaining == 4

    def test_clear(self):
        """清空所有"""
        APIRateLimiter.check_and_consume("key1", 5)
        APIRateLimiter.clear()
        usage = APIRateLimiter.get_usage("key1", 5)
        assert usage.remaining == 5


class TestAPIPlatformTypes:
    """API平台类型测试"""

    def test_api_key_info_frozen(self):
        """APIKeyInfo 不可变"""
        info = APIKeyInfo(
            key_id="test",
            key_hash="hash",
            name="测试",
            owner_id="user",
        )
        with pytest.raises(AttributeError):
            info.name = "新名称"  # type: ignore

    def test_rate_limit_info_frozen(self):
        """RateLimitInfo 不可变"""
        info = RateLimitInfo(
            key_id="test", limit=60, remaining=59, reset_at=0.0
        )
        with pytest.raises(AttributeError):
            info.remaining = 0  # type: ignore

    def test_api_key_status_enum(self):
        """密钥状态枚举"""
        assert APIKeyStatus.ACTIVE.value == "活跃"
        assert APIKeyStatus.REVOKED.value == "已撤销"
        assert APIKeyStatus.EXPIRED.value == "已过期"

    def test_api_permission_enum(self):
        """API权限枚举"""
        assert APIPermission.DIVINATION.value == "起卦"
        assert APIPermission.ANALYSIS.value == "分析"
        assert APIPermission.HISTORY.value == "历史"
