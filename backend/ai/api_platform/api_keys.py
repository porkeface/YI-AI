"""API密钥管理

提供API密钥的创建、验证、撤销和查询功能。
线程安全 — 使用锁保护共享状态。
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import threading
import time

from ai.api_platform.types import (
    APIKeyInfo,
    APIKeyStatus,
    APIPermission,
)

logger = logging.getLogger(__name__)

# API密钥前缀
_KEY_PREFIX = "yi_"


class APIKeyManager:
    """API密钥管理器

    classmethod-only API — 所有状态存储在模块级变量中。
    """

    # 模块级状态
    _keys: dict[str, APIKeyInfo] = {}  # key_id -> info
    _hash_to_id: dict[str, str] = {}   # key_hash -> key_id
    _lock = threading.Lock()

    @classmethod
    def create_key(
        cls,
        name: str,
        owner_id: str,
        permissions: tuple[APIPermission, ...] = (
            APIPermission.DIVINATION,
            APIPermission.ANALYSIS,
            APIPermission.HISTORY,
        ),
        rate_limit: int = 60,
        expires_in_days: int = 0,
    ) -> tuple[str, APIKeyInfo]:
        """创建API密钥

        Args:
            name: 密钥名称
            owner_id: 所有者ID
            permissions: 权限列表
            rate_limit: 每分钟请求限制
            expires_in_days: 过期天数（0表示永不过期）

        Returns:
            (原始密钥, 密钥信息) 元组。原始密钥只返回一次。
        """
        # 生成密钥
        raw_key = _KEY_PREFIX + secrets.token_urlsafe(32)
        key_hash = cls._hash_key(raw_key)
        key_id = "key_" + secrets.token_hex(8)

        now = time.time()
        expires_at = (
            now + expires_in_days * 86400 if expires_in_days > 0 else 0.0
        )

        info = APIKeyInfo(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            owner_id=owner_id,
            status=APIKeyStatus.ACTIVE,
            permissions=permissions,
            rate_limit=rate_limit,
            created_at=now,
            expires_at=expires_at,
        )

        with cls._lock:
            cls._keys[key_id] = info
            cls._hash_to_id[key_hash] = key_id

        logger.info("api_key_created: %s (%s)", key_id, name)
        return raw_key, info

    @classmethod
    def validate_key(cls, raw_key: str) -> APIKeyInfo | None:
        """验证API密钥

        Args:
            raw_key: 原始密钥

        Returns:
            密钥信息，无效返回 None
        """
        key_hash = cls._hash_key(raw_key)

        with cls._lock:
            key_id = cls._hash_to_id.get(key_hash)
            if key_id is None:
                return None

            info = cls._keys.get(key_id)
            if info is None:
                return None

        # 检查状态
        if info.status != APIKeyStatus.ACTIVE:
            return None

        # 检查过期
        if info.expires_at > 0 and time.time() > info.expires_at:
            cls._update_status(key_id, APIKeyStatus.EXPIRED)
            return None

        # 更新最后使用时间
        cls._update_last_used(key_id)

        return info

    @classmethod
    def revoke_key(cls, key_id: str) -> bool:
        """撤销密钥

        Args:
            key_id: 密钥ID

        Returns:
            是否撤销成功
        """
        return cls._update_status(key_id, APIKeyStatus.REVOKED)

    @classmethod
    def get_key_info(cls, key_id: str) -> APIKeyInfo | None:
        """获取密钥信息

        Args:
            key_id: 密钥ID

        Returns:
            密钥信息，不存在返回 None
        """
        with cls._lock:
            return cls._keys.get(key_id)

    @classmethod
    def list_keys(
        cls,
        owner_id: str | None = None,
        status: APIKeyStatus | None = None,
    ) -> tuple[APIKeyInfo, ...]:
        """列出密钥

        Args:
            owner_id: 按所有者筛选
            status: 按状态筛选

        Returns:
            符合条件的密钥信息列表（不包含key_hash）
        """
        with cls._lock:
            results = []
            for info in cls._keys.values():
                if owner_id and info.owner_id != owner_id:
                    continue
                if status and info.status != status:
                    continue
                results.append(info)
            return tuple(results)

    @classmethod
    def has_permission(
        cls,
        info: APIKeyInfo,
        permission: APIPermission,
    ) -> bool:
        """检查密钥是否有指定权限

        Args:
            info: 密钥信息
            permission: 权限

        Returns:
            是否有权限
        """
        return permission in info.permissions

    @classmethod
    def _update_status(
        cls,
        key_id: str,
        status: APIKeyStatus,
    ) -> bool:
        """更新密钥状态"""
        with cls._lock:
            info = cls._keys.get(key_id)
            if info is None:
                return False
            cls._keys[key_id] = APIKeyInfo(
                key_id=info.key_id,
                key_hash=info.key_hash,
                name=info.name,
                owner_id=info.owner_id,
                status=status,
                permissions=info.permissions,
                rate_limit=info.rate_limit,
                created_at=info.created_at,
                expires_at=info.expires_at,
                last_used_at=info.last_used_at,
            )
            return True

    @classmethod
    def _update_last_used(cls, key_id: str) -> None:
        """更新最后使用时间"""
        with cls._lock:
            info = cls._keys.get(key_id)
            if info is None:
                return
            cls._keys[key_id] = APIKeyInfo(
                key_id=info.key_id,
                key_hash=info.key_hash,
                name=info.name,
                owner_id=info.owner_id,
                status=info.status,
                permissions=info.permissions,
                rate_limit=info.rate_limit,
                created_at=info.created_at,
                expires_at=info.expires_at,
                last_used_at=time.time(),
            )

    @classmethod
    def _hash_key(cls, raw_key: str) -> str:
        """计算密钥哈希"""
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @classmethod
    def count(cls) -> int:
        """获取密钥总数"""
        with cls._lock:
            return len(cls._keys)

    @classmethod
    def clear(cls) -> None:
        """清空所有密钥（用于测试）"""
        with cls._lock:
            cls._keys.clear()
            cls._hash_to_id.clear()
