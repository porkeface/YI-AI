"""L1 工作记忆

会话级短期存储，TTL 2小时。
MVP 阶段使用内存 dict 替代 Redis。
"""
from __future__ import annotations

import time
import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)

# 默认 TTL: 2 小时
_DEFAULT_TTL = 7200


class WorkingMemory:
    """L1 工作记忆 — 会话级短期存储

    全部 classmethod，无实例化。
    内部使用 dict 存储会话数据，支持 TTL 自动过期。
    """

    _store: dict[str, dict[str, Any]] = {}
    _lock = threading.Lock()
    # 每条记录: {"data": dict, "expires_at": float, "user_id": str}

    @classmethod
    def get_session(cls, session_id: str) -> dict | None:
        """获取会话数据

        Args:
            session_id: 会话ID

        Returns:
            会话数据字典，不存在或已过期返回 None
        """
        with cls._lock:
            entry = cls._store.get(session_id)
            if entry is None:
                return None
            if time.time() > entry["expires_at"]:
                del cls._store[session_id]
                logger.debug("工作记忆过期: session=%s", session_id)
                return None
            return entry["data"]

    @classmethod
    def update_session(
        cls,
        session_id: str,
        data: dict,
        user_id: str = "",
        ttl: int = _DEFAULT_TTL,
    ) -> None:
        """更新会话数据

        已有会话会合并更新，新字段覆盖旧字段。

        Args:
            session_id: 会话ID
            data: 要更新的数据
            user_id: 用户ID
            ttl: 过期时间（秒），默认 2 小时
        """
        with cls._lock:
            existing = cls._store.get(session_id)
            if existing is not None and time.time() <= existing["expires_at"]:
                existing["data"].update(data)
                existing["expires_at"] = time.time() + ttl
                if user_id:
                    existing["user_id"] = user_id
            else:
                cls._store[session_id] = {
                    "data": dict(data),
                    "expires_at": time.time() + ttl,
                    "user_id": user_id,
                }
        logger.debug("工作记忆更新: session=%s, keys=%s", session_id, list(data.keys()))

    @classmethod
    def clear_session(cls, session_id: str) -> bool:
        """清除会话

        Args:
            session_id: 会话ID

        Returns:
            是否存在并被清除
        """
        with cls._lock:
            if session_id in cls._store:
                del cls._store[session_id]
                logger.debug("工作记忆清除: session=%s", session_id)
                return True
            return False

    @classmethod
    def get_recent_hexagrams(cls, user_id: str, limit: int = 5) -> list[str]:
        """获取用户最近的卦象（最近的在前）

        Args:
            user_id: 用户ID
            limit: 返回数量

        Returns:
            最近的卦名列表（去重，最近的在前）
        """
        now = time.time()
        entries: list[tuple[float, str]] = []

        with cls._lock:
            for entry in cls._store.values():
                if entry["user_id"] != user_id:
                    continue
                if now > entry["expires_at"]:
                    continue
                hex_name = entry["data"].get("current_hexagram")
                if hex_name:
                    entries.append((entry["expires_at"], hex_name))

        # 按过期时间降序（过期时间晚 = 更新）
        entries.sort(key=lambda x: x[0], reverse=True)

        # 去重，保留最新的
        seen: set[str] = set()
        result: list[str] = []
        for _, hex_name in entries:
            if hex_name not in seen:
                result.append(hex_name)
                seen.add(hex_name)
                if len(result) >= limit:
                    break

        return result

    @classmethod
    def get_all_active_sessions(cls) -> list[str]:
        """获取所有活跃会话ID

        Returns:
            活跃会话ID列表
        """
        now = time.time()
        with cls._lock:
            expired = [sid for sid, entry in cls._store.items() if now > entry["expires_at"]]
            for sid in expired:
                del cls._store[sid]
            return list(cls._store.keys())

    @classmethod
    def cleanup_expired(cls) -> int:
        """清理所有过期会话

        Returns:
            清理的会话数
        """
        now = time.time()
        with cls._lock:
            expired = [sid for sid, entry in cls._store.items() if now > entry["expires_at"]]
            for sid in expired:
                del cls._store[sid]
        if expired:
            logger.info("工作记忆清理过期会话: %d个", len(expired))
        return len(expired)

    @classmethod
    def reset(cls) -> None:
        """重置所有数据（测试用）"""
        with cls._lock:
            cls._store.clear()
