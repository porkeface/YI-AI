"""API平台类型定义"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum


class APIKeyStatus(str, Enum):
    """API密钥状态"""
    ACTIVE = "活跃"
    REVOKED = "已撤销"
    EXPIRED = "已过期"


class APIPermission(str, Enum):
    """API权限"""
    DIVINATION = "起卦"        # 调用起卦API
    ANALYSIS = "分析"          # 调用分析API
    HISTORY = "历史"           # 查询历史记录
    KNOWLEDGE = "知识"         # 查询知识库
    PLUGIN = "插件"            # 管理插件


@dataclass(frozen=True)
class APIKeyInfo:
    """API密钥信息

    Attributes:
        key_id: 密钥ID（公钥，用于标识）
        key_hash: 密钥哈希（用于验证）
        name: 密钥名称
        owner_id: 所有者ID
        status: 密钥状态
        permissions: 权限列表
        rate_limit: 每分钟请求限制
        created_at: 创建时间戳
        expires_at: 过期时间戳（0表示永不过期）
        last_used_at: 最后使用时间戳
    """
    key_id: str
    key_hash: str
    name: str
    owner_id: str
    status: APIKeyStatus = APIKeyStatus.ACTIVE
    permissions: tuple[APIPermission, ...] = ()
    rate_limit: int = 60
    created_at: float = 0.0
    expires_at: float = 0.0
    last_used_at: float = 0.0


@dataclass(frozen=True)
class RateLimitInfo:
    """速率限制信息

    Attributes:
        key_id: 密钥ID
        limit: 限制次数
        remaining: 剩余次数
        reset_at: 重置时间戳
    """
    key_id: str
    limit: int
    remaining: int
    reset_at: float


@dataclass(frozen=True)
class APIUsageRecord:
    """API使用记录

    Attributes:
        key_id: 密钥ID
        endpoint: 调用端点
        timestamp: 调用时间戳
        response_time_ms: 响应时间(毫秒)
        status_code: HTTP状态码
    """
    key_id: str
    endpoint: str
    timestamp: float
    response_time_ms: float = 0.0
    status_code: int = 200
