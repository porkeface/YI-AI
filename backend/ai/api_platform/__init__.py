"""开放API平台模块

开发者API平台，包括：
- APIKeyManager: API密钥管理
- APIRateLimiter: 速率限制器
- 类型定义: 密钥、权限、速率限制
"""

from ai.api_platform.api_keys import APIKeyManager
from ai.api_platform.rate_limiter import APIRateLimiter
from ai.api_platform.types import (
    APIKeyStatus,
    APIPermission,
    APIKeyInfo,
    RateLimitInfo,
    APIUsageRecord,
)

__all__ = [
    # 核心
    "APIKeyManager",
    "APIRateLimiter",
    # 类型
    "APIKeyStatus",
    "APIPermission",
    "APIKeyInfo",
    "RateLimitInfo",
    "APIUsageRecord",
]
