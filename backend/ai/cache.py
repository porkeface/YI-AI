"""
多级缓存策略 - Phase 2.5
L1: 进程内 LRU 缓存
L2: Redis 缓存（可选，无Redis时退化为仅L1）
支持: Cache-Aside、Write-Through、Embedding缓存、AI结果缓存
"""
from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_latency_ms: float = 0.0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


_MISSING = object()  # 哨兵对象，区分"未缓存"和"缓存了 None"


class LRUCache:
    """
    进程内 LRU 缓存
    基于 OrderedDict 实现，适用于 async 单线程事件循环。
    """

    def __init__(self, max_size: int = 1000, default_ttl: float = 3600.0) -> None:
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._stats = CacheStats()

    def get(self, key: str) -> Any:
        """获取缓存值，未命中返回 _MISSING 哨兵"""
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                self._cache.move_to_end(key)
                self._stats.hits += 1
                return value
            else:
                del self._cache[key]
        self._stats.misses += 1
        return _MISSING

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        """设置缓存值"""
        if key in self._cache:
            self._cache.move_to_end(key)
        elif len(self._cache) >= self._max_size:
            # 淘汰最久未使用
            self._cache.popitem(last=False)
            self._stats.evictions += 1

        expiry = time.time() + (ttl or self._default_ttl)
        self._cache[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def stats(self) -> CacheStats:
        return self._stats


class MultiLevelCache:
    """
    多级缓存管理器
    L1: 进程内 LRU（快，小容量）
    L2: Redis（大容量，可选）
    """

    def __init__(
        self,
        l1_max_size: int = 500,
        l1_ttl: float = 300.0,    # 5分钟
        l2_ttl: float = 3600.0,   # 1小时
        redis_client: Any | None = None,
    ) -> None:
        self._l1 = LRUCache(max_size=l1_max_size, default_ttl=l1_ttl)
        self._l2_ttl = l2_ttl
        self._redis = redis_client
        self._stats = CacheStats()

    async def get(self, key: str) -> Any:
        """获取：L1 -> L2，未命中返回 None"""
        # L1 查找
        value = self._l1.get(key)
        if value is not _MISSING:
            self._stats.hits += 1
            return value

        # L2 查找（Redis）
        if self._redis:
            try:
                raw = await self._redis.get(key)
                if raw:
                    value = json.loads(raw)
                    # 回填 L1
                    self._l1.set(key, value)
                    self._stats.hits += 1
                    return value
            except Exception:
                pass  # Redis 不可用时静默降级

        self._stats.misses += 1
        return None

    async def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        """设置：同时写 L1 和 L2"""
        # L1
        self._l1.set(key, value, ttl)

        # L2
        if self._redis:
            try:
                await self._redis.setex(
                    key,
                    int(ttl or self._l2_ttl),
                    json.dumps(value, ensure_ascii=False),
                )
            except Exception:
                pass  # Redis 不可用时静默降级

    async def delete(self, key: str) -> None:
        """删除：同时清除 L1 和 L2"""
        self._l1.delete(key)
        if self._redis:
            try:
                await self._redis.delete(key)
            except Exception:
                pass

    async def invalidate_pattern(self, pattern: str) -> int:
        """按模式失效缓存（glob 风格: * 匹配任意字符）"""
        import fnmatch
        count = 0
        # L1 清理
        keys_to_delete = [key for key in self._l1._cache if fnmatch.fnmatch(key, pattern)]
        for key in keys_to_delete:
            self._l1.delete(key)
            count += 1

        # L2 清理
        if self._redis:
            try:
                cursor = 0
                while True:
                    cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)
                    if keys:
                        await self._redis.delete(*keys)
                        count += len(keys)
                    if cursor == 0:
                        break
            except Exception:
                pass

        return count

    @property
    def stats(self) -> CacheStats:
        return self._stats


class CacheKeyBuilder:
    """缓存键构建器"""

    @staticmethod
    def hexagram(name: str) -> str:
        return f"hexagram:{name}:full"

    @staticmethod
    def hexagram_relations(name: str) -> str:
        return f"hexagram:{name}:relations"

    @staticmethod
    def interpretation(hexagram: str, question: str, ganzhi: dict) -> str:
        content = f"{hexagram}:{question}:{json.dumps(ganzhi, sort_keys=True)}"
        h = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"cache:interpretation:{h}"

    @staticmethod
    def embedding(text: str) -> str:
        h = hashlib.sha256(text.encode()).hexdigest()[:16]
        return f"cache:embedding:{h}"

    @staticmethod
    def rag_result(query: str, hexagram: str) -> str:
        content = f"{query}:{hexagram}"
        h = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"cache:rag:{h}"

    @staticmethod
    def user_profile(user_id: str) -> str:
        return f"user:{user_id}:profile"

    @staticmethod
    def user_recent(user_id: str) -> str:
        return f"user:{user_id}:recent"

    @staticmethod
    def rate_limit(user_id: str, action: str) -> str:
        return f"ratelimit:{user_id}:{action}"


class RateLimiter:
    """
    滑动窗口频率限制器
    基于进程内计数（生产环境应使用Redis）
    """

    def __init__(self) -> None:
        self._windows: dict[str, list[float]] = {}

    def check(self, key: str, max_count: int, window_seconds: float) -> tuple[bool, int]:
        """
        检查频率限制
        返回: (是否允许, 剩余次数)
        """
        now = time.time()
        window_start = now - window_seconds

        if key not in self._windows:
            self._windows[key] = []

        # 清理窗口外的记录
        self._windows[key] = [t for t in self._windows[key] if t > window_start]

        current = len(self._windows[key])
        allowed = current < max_count

        if allowed:
            self._windows[key].append(now)

        remaining = max(0, max_count - current - (1 if allowed else 0))
        return allowed, remaining
