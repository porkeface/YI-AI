"""L3 语义记忆

用户关注的知识概念关系图。
MVP 阶段使用内存 dict 替代 Neo4j。
"""
from __future__ import annotations

import math
import time
import logging
import threading

from ai.memory.types import UserMemory, MemoryType

logger = logging.getLogger(__name__)

# 衰减半衰期（天）
_HALF_LIFE_DAYS = 60


class SemanticMemory:
    """L3 语义记忆 — 概念关系图

    全部 classmethod，无实例化。
    用 dict 存储用户的概念关系网络。
    """

    # user_id -> {concept: {related_concepts, access_count, last_accessed, created_at}}
    _graphs: dict[str, dict[str, dict]] = {}
    _lock = threading.Lock()

    @classmethod
    def add_concept(
        cls,
        user_id: str,
        concept: str,
        related_concepts: tuple[str, ...] = (),
    ) -> None:
        """添加概念及其关联

        已有概念会更新关联和访问计数。

        Args:
            user_id: 用户ID
            concept: 概念名称
            related_concepts: 关联概念列表
        """
        now = time.time()
        with cls._lock:
            if user_id not in cls._graphs:
                cls._graphs[user_id] = {}

            graph = cls._graphs[user_id]

            if concept in graph:
                node = graph[concept]
                existing_related = set(node["related"])
                existing_related.update(related_concepts)
                node["related"] = frozenset(existing_related)
                node["access_count"] += 1
                node["last_accessed"] = now
            else:
                graph[concept] = {
                    "related": frozenset(related_concepts),
                    "access_count": 1,
                    "last_accessed": now,
                    "created_at": now,
                }

            # 反向关联
            for rc in related_concepts:
                if rc in graph:
                    existing = set(graph[rc]["related"])
                    existing.add(concept)
                    graph[rc]["related"] = frozenset(existing)
                else:
                    graph[rc] = {
                        "related": frozenset((concept,)),
                        "access_count": 0,
                        "last_accessed": now,
                        "created_at": now,
                    }

        logger.debug(
            "语义记忆添加: user=%s, concept=%s, related=%d",
            user_id, concept, len(related_concepts),
        )

    @classmethod
    def get_related(cls, user_id: str, concept: str) -> tuple[str, ...]:
        """获取概念的关联概念

        Args:
            user_id: 用户ID
            concept: 概念名称

        Returns:
            关联概念列表
        """
        with cls._lock:
            graph = cls._graphs.get(user_id, {})
            node = graph.get(concept)
            if node is None:
                return ()
            return tuple(node["related"])

    @classmethod
    def get_user_concepts(cls, user_id: str) -> tuple[str, ...]:
        """获取用户的所有概念

        Args:
            user_id: 用户ID

        Returns:
            概念列表（按访问次数降序）
        """
        with cls._lock:
            graph = cls._graphs.get(user_id, {})
            concepts = [
                (name, node["access_count"])
                for name, node in graph.items()
            ]
        concepts.sort(key=lambda x: x[1], reverse=True)
        return tuple(name for name, _ in concepts)

    @classmethod
    def recall(cls, user_id: str, query: str) -> tuple[str, ...]:
        """基于查询召回相关概念

        Args:
            user_id: 用户ID
            query: 查询文本

        Returns:
            相关概念列表
        """
        with cls._lock:
            graph = cls._graphs.get(user_id, {})
            if not graph:
                return ()

            query_lower = query.lower()
            matches: list[tuple[float, str]] = []

            for concept, node in graph.items():
                # 直接匹配
                if concept.lower() in query_lower:
                    score = 2.0 + node["access_count"] * 0.1
                    matches.append((score, concept))
                    continue

                # 关联匹配
                for related in node["related"]:
                    if related.lower() in query_lower:
                        score = 1.0 + node["access_count"] * 0.05
                        matches.append((score, concept))
                        break

        matches.sort(key=lambda x: x[0], reverse=True)
        return tuple(concept for _, concept in matches)

    @classmethod
    def count(cls, user_id: str | None = None) -> int:
        """统计概念数量

        Args:
            user_id: 用户ID，None 则统计全部

        Returns:
            概念数量
        """
        with cls._lock:
            if user_id is None:
                return sum(len(g) for g in cls._graphs.values())
            return len(cls._graphs.get(user_id, {}))

    @classmethod
    def apply_decay_all(cls, user_id: str) -> int:
        """对用户所有概念执行衰减

        衰减体现在访问计数减少，低计数的概念将被清理。
        清理后同步移除其他概念中的悬挂引用。

        Args:
            user_id: 用户ID

        Returns:
            衰减的概念数
        """
        now = time.time()
        with cls._lock:
            graph = cls._graphs.get(user_id)
            if graph is None:
                return 0

            lam = math.log(2) / _HALF_LIFE_DAYS
            count = 0
            to_remove: list[str] = []

            for concept, node in graph.items():
                days_elapsed = (now - node["last_accessed"]) / 86400
                if days_elapsed <= 0:
                    continue
                decay = math.exp(-lam * days_elapsed)
                node["access_count"] = max(1, int(node["access_count"] * decay))
                count += 1
                # 移除长时间未访问且计数低的概念
                if days_elapsed > 180 and node["access_count"] <= 1:
                    to_remove.append(concept)

            # 移除过期概念
            for concept in to_remove:
                del graph[concept]
                logger.debug("语义记忆衰减清理: user=%s, concept=%s", user_id, concept)

            # [C1 修复] 清理悬挂的反向引用
            if to_remove:
                removed = set(to_remove)
                for node in graph.values():
                    old_related = node["related"]
                    cleaned = frozenset(r for r in old_related if r not in removed)
                    if cleaned != old_related:
                        node["related"] = cleaned

        return count

    @classmethod
    def reset(cls) -> None:
        """重置所有数据（测试用）"""
        with cls._lock:
            cls._graphs.clear()
