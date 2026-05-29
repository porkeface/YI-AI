"""L2 情景记忆

具体占卜事件的持久化存储。
MVP 阶段使用内存 list 替代 SQLAlchemy + Qdrant。
支持时间衰减和关键词检索。
"""
from __future__ import annotations

import math
import re
import time
import uuid
import logging
import threading

from ai.memory.types import UserMemory, MemoryType

logger = logging.getLogger(__name__)

# 衰减半衰期（天）
_HALF_LIFE_DAYS = 30
# 最大存储条数
_MAX_STORE_SIZE = 10000


class EpisodicMemory:
    """L2 情景记忆 — 具体事件存储

    全部 classmethod，无实例化。
    内部使用 list 存储，支持时间衰减和关键词检索。
    """

    _store: list[UserMemory] = []
    _lock = threading.Lock()

    @classmethod
    def store(
        cls,
        user_id: str,
        content: str,
        hexagram_name: str | None = None,
        importance: float = 0.5,
    ) -> UserMemory:
        """存储一条情景记忆

        Args:
            user_id: 用户ID
            content: 记忆内容
            hexagram_name: 关联卦名
            importance: 重要度 0.0-1.0

        Returns:
            创建的记忆对象
        """
        now = time.time()
        memory = UserMemory(
            memory_id=str(uuid.uuid4()),
            user_id=user_id,
            memory_type=MemoryType.EPISODIC,
            content=content,
            hexagram_name=hexagram_name,
            importance=_clamp(importance, 0.0, 1.0),
            access_count=0,
            last_accessed=now,
            created_at=now,
            decay_factor=1.0,
        )
        with cls._lock:
            # [M7] 超出上限时淘汰最旧的
            if len(cls._store) >= _MAX_STORE_SIZE:
                cls._store = cls._store[-_MAX_STORE_SIZE // 2:]
                logger.warning("情景记忆超出上限，淘汰旧记忆")
            cls._store.append(memory)
        logger.debug(
            "情景记忆存储: user=%s, hex=%s, len=%d",
            user_id, hexagram_name, len(content),
        )
        return memory

    @classmethod
    def recall(
        cls,
        user_id: str,
        query: str,
        limit: int = 10,
    ) -> tuple[UserMemory, ...]:
        """关键词召回

        基于内容关键词匹配 + 重要度加权排序。

        Args:
            user_id: 用户ID
            query: 查询文本
            limit: 返回数量

        Returns:
            匹配的记忆列表（按相关度排序）
        """
        now = time.time()
        query_lower = query.lower()

        # [L5] 空查询直接返回
        if not query_lower.strip():
            return ()

        candidates: list[tuple[float, UserMemory]] = []

        with cls._lock:
            store_snapshot = list(cls._store)

        for mem in store_snapshot:
            if mem.user_id != user_id:
                continue
            # 更新衰减
            decayed = cls._apply_decay(mem, now)
            # 关键词匹配得分
            content_lower = decayed.content.lower()
            keyword_score = _keyword_match(query_lower, content_lower)
            if keyword_score <= 0:
                continue
            # 综合得分 = 关键词匹配 * 重要度 * 衰减系数
            total_score = keyword_score * decayed.importance * decayed.decay_factor
            candidates.append((total_score, decayed))

        # 按得分降序
        candidates.sort(key=lambda x: x[0], reverse=True)

        result = tuple(mem for _, mem in candidates[:limit])

        # 更新访问计数
        for mem in result:
            cls._update_access(mem)

        return result

    @classmethod
    def get_user_history(
        cls,
        user_id: str,
        limit: int = 20,
    ) -> tuple[UserMemory, ...]:
        """获取用户历史记录

        按创建时间倒序返回。

        Args:
            user_id: 用户ID
            limit: 返回数量

        Returns:
            记忆列表
        """
        now = time.time()
        with cls._lock:
            user_memories = [
                cls._apply_decay(m, now)
                for m in cls._store
                if m.user_id == user_id
            ]
        user_memories.sort(key=lambda m: m.created_at, reverse=True)
        return tuple(user_memories[:limit])

    @classmethod
    def get_by_hexagram(
        cls,
        user_id: str,
        hexagram_name: str,
    ) -> tuple[UserMemory, ...]:
        """获取与特定卦象相关的记忆

        Args:
            user_id: 用户ID
            hexagram_name: 卦名

        Returns:
            相关记忆列表
        """
        with cls._lock:
            return tuple(
                m for m in cls._store
                if m.user_id == user_id and m.hexagram_name == hexagram_name
            )

    @classmethod
    def count(cls, user_id: str | None = None) -> int:
        """统计记忆条数

        Args:
            user_id: 用户ID，None 则统计全部

        Returns:
            记忆条数
        """
        with cls._lock:
            if user_id is None:
                return len(cls._store)
            return sum(1 for m in cls._store if m.user_id == user_id)

    @classmethod
    def get_compressible(
        cls,
        user_id: str,
        importance_threshold: float,
        access_threshold: int,
    ) -> tuple[UserMemory, ...]:
        """获取可压缩的记忆（在锁内读取）

        Args:
            user_id: 用户ID
            importance_threshold: 重要度阈值
            access_threshold: 访问次数阈值

        Returns:
            可压缩的记忆列表
        """
        with cls._lock:
            return tuple(
                m for m in cls._store
                if m.user_id == user_id
                and m.importance < importance_threshold
                and m.access_count >= access_threshold
            )

    @classmethod
    def remove_by_ids(cls, ids: set[str]) -> int:
        """按ID批量移除记忆

        Args:
            ids: 要移除的记忆ID集合

        Returns:
            实际移除的数量
        """
        with cls._lock:
            before = len(cls._store)
            cls._store = [m for m in cls._store if m.memory_id not in ids]
            return before - len(cls._store)

    @classmethod
    def apply_decay_all(cls, user_id: str) -> int:
        """对用户所有记忆执行衰减

        Args:
            user_id: 用户ID

        Returns:
            衰减的记忆条数
        """
        now = time.time()
        with cls._lock:
            count = 0
            new_store: list[UserMemory] = []
            for mem in cls._store:
                if mem.user_id == user_id:
                    decayed = cls._apply_decay(mem, now)
                    new_store.append(decayed)
                    count += 1
                else:
                    new_store.append(mem)
            cls._store = new_store
        return count

    @classmethod
    def _apply_decay(cls, mem: UserMemory, now: float) -> UserMemory:
        """应用时间衰减

        衰减公式: new_factor = old_factor * exp(-lambda * days)
        lambda = ln(2) / half_life_days

        Args:
            mem: 原始记忆
            now: 当前时间戳

        Returns:
            衰减后的新记忆对象
        """
        days_elapsed = (now - mem.last_accessed) / 86400
        if days_elapsed <= 0:
            return mem
        lam = math.log(2) / _HALF_LIFE_DAYS
        new_factor = mem.decay_factor * math.exp(-lam * days_elapsed)
        new_factor = max(new_factor, 0.01)  # 最小衰减系数
        if abs(new_factor - mem.decay_factor) < 1e-6:
            return mem
        return UserMemory(
            memory_id=mem.memory_id,
            user_id=mem.user_id,
            memory_type=mem.memory_type,
            content=mem.content,
            hexagram_name=mem.hexagram_name,
            importance=mem.importance,
            access_count=mem.access_count,
            last_accessed=mem.last_accessed,
            created_at=mem.created_at,
            decay_factor=new_factor,
        )

    @classmethod
    def _update_access(cls, mem: UserMemory) -> None:
        """更新记忆访问计数（原地修改 store 中的对象引用）"""
        now = time.time()
        with cls._lock:
            for i, m in enumerate(cls._store):
                if m.memory_id == mem.memory_id:
                    cls._store[i] = UserMemory(
                        memory_id=m.memory_id,
                        user_id=m.user_id,
                        memory_type=m.memory_type,
                        content=m.content,
                        hexagram_name=m.hexagram_name,
                        importance=m.importance,
                        access_count=m.access_count + 1,
                        last_accessed=now,
                        created_at=m.created_at,
                        decay_factor=m.decay_factor,
                    )
                    break

    @classmethod
    def reset(cls) -> None:
        """重置所有数据（测试用）"""
        with cls._lock:
            cls._store.clear()

    @classmethod
    def replace_for_test(cls, new_store: list[UserMemory]) -> None:
        """替换存储数据（仅测试用，持有锁）"""
        with cls._lock:
            cls._store = list(new_store)


def _keyword_match(query: str, content: str) -> float:
    """关键词匹配得分

    将 query 按字符切分，计算在 content 中的匹配比例。

    Args:
        query: 查询文本（小写）
        content: 内容文本（小写）

    Returns:
        匹配得分 0.0-1.0
    """
    if not query or not content:
        return 0.0
    # 按空格和标点分词
    words = re.split(r'[\s,，。、；：！？\?\.!;:\-\(\)\[\]]+', query)
    words = [w for w in words if len(w) >= 1]
    if not words:
        return 0.0
    matched = sum(1 for w in words if w in content)
    return matched / len(words)


def _clamp(value: float, min_val: float, max_val: float) -> float:
    """限制值在范围内"""
    return max(min_val, min(value, max_val))
