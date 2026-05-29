"""API速率限制器

基于滑动窗口的速率限制，按密钥ID独立限流。
线程安全 — 使用锁保护共享状态。
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque

from ai.api_platform.types import RateLimitInfo

logger = logging.getLogger(__name__)


class APIRateLimiter:
    """API速率限制器

    classmethod-only API — 使用滑动窗口算法。
    窗口大小固定为60秒。
    """

    # 模块级状态
    _windows: dict[str, deque[float]] = {}  # key_id -> timestamps
    _lock = threading.Lock()
    _window_seconds: int = 60

    @classmethod
    def check_and_consume(
        cls,
        key_id: str,
        limit: int,
    ) -> RateLimitInfo:
        """检查并消费一个请求

        如果允许，记录请求时间并返回允许结果。
        如果超限，返回拒绝结果。

        Args:
            key_id: 密钥ID
            limit: 每窗口最大请求数

        Returns:
            速率限制信息
        """
        now = time.time()
        window_start = now - cls._window_seconds

        with cls._lock:
            if key_id not in cls._windows:
                cls._windows[key_id] = deque()

            window = cls._windows[key_id]

            # 清理过期记录
            while window and window[0] < window_start:
                window.popleft()

            current_count = len(window)

            if current_count < limit:
                # 允许请求
                window.append(now)
                remaining = limit - current_count - 1
                reset_at = now + cls._window_seconds
                return RateLimitInfo(
                    key_id=key_id,
                    limit=limit,
                    remaining=remaining,
                    reset_at=reset_at,
                )
            else:
                # 超限
                oldest = window[0] if window else now
                reset_at = oldest + cls._window_seconds
                return RateLimitInfo(
                    key_id=key_id,
                    limit=limit,
                    remaining=0,
                    reset_at=reset_at,
                )

    @classmethod
    def get_usage(cls, key_id: str, limit: int) -> RateLimitInfo:
        """获取当前使用情况（不消费）

        Args:
            key_id: 密钥ID
            limit: 每窗口最大请求数

        Returns:
            速率限制信息
        """
        now = time.time()
        window_start = now - cls._window_seconds

        with cls._lock:
            window = cls._windows.get(key_id)
            if window is None:
                return RateLimitInfo(
                    key_id=key_id,
                    limit=limit,
                    remaining=limit,
                    reset_at=now + cls._window_seconds,
                )

            # 清理过期记录
            while window and window[0] < window_start:
                window.popleft()

            current_count = len(window)
            remaining = max(0, limit - current_count)
            oldest = window[0] if window else now
            reset_at = oldest + cls._window_seconds

            return RateLimitInfo(
                key_id=key_id,
                limit=limit,
                remaining=remaining,
                reset_at=reset_at,
            )

    @classmethod
    def reset(cls, key_id: str) -> None:
        """重置指定密钥的速率限制

        Args:
            key_id: 密钥ID
        """
        with cls._lock:
            cls._windows.pop(key_id, None)

    @classmethod
    def clear(cls) -> None:
        """清空所有速率限制（用于测试）"""
        with cls._lock:
            cls._windows.clear()
