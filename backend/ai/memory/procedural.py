"""L4 程序记忆

用户行为模式和习惯倾向的存储与识别。
MVP 阶段使用内存 dict 替代 Neo4j。
"""
from __future__ import annotations

import re
import time
import datetime
import logging
import threading
from collections import Counter

from ai.memory.types import (
    UserMemory, MemoryType, Pattern, PatternType,
)

logger = logging.getLogger(__name__)


class ProceduralMemory:
    """L4 程序记忆 — 行为模式

    全部 classmethod，无实例化。
    记录用户的行为模式：高频卦象、反复主题、提问风格等。
    """

    # user_id -> {
    #   "hexagram_counts": Counter,
    #   "question_keywords": Counter,
    #   "session_times": list[float],
    # }
    _profiles: dict[str, dict] = {}
    _lock = threading.RLock()  # [C1] 可重入锁，避免 count(None) 死锁

    @classmethod
    def record_session(
        cls,
        user_id: str,
        hexagram_name: str | None = None,
        question: str = "",
    ) -> None:
        """记录一次会话活动

        Args:
            user_id: 用户ID
            hexagram_name: 本次卦名
            question: 用户问题
        """
        now = time.time()
        with cls._lock:
            profile = cls._get_or_create_profile(user_id)

            # 记录卦象
            if hexagram_name:
                profile["hexagram_counts"][hexagram_name] += 1

            # 记录问题关键词
            if question:
                keywords = _extract_keywords(question)
                for kw in keywords:
                    profile["question_keywords"][kw] += 1

            # 记录会话时间
            profile["session_times"].append(now)
            # 只保留最近 100 次
            if len(profile["session_times"]) > 100:
                profile["session_times"] = profile["session_times"][-100:]

        logger.debug(
            "程序记忆记录: user=%s, hex=%s, keywords=%d",
            user_id, hexagram_name, len(question),
        )

    @classmethod
    def get_frequent_hexagrams(
        cls,
        user_id: str,
        limit: int = 5,
    ) -> tuple[tuple[str, float], ...]:
        """获取高频卦象

        Args:
            user_id: 用户ID
            limit: 返回数量

        Returns:
            (卦名, 频率) 列表
        """
        with cls._lock:
            profile = cls._profiles.get(user_id)
            if profile is None:
                return ()

            counts = profile["hexagram_counts"]
            total = sum(counts.values())
            if total == 0:
                return ()

            most_common = counts.most_common(limit)

        return tuple((name, count / total) for name, count in most_common)

    @classmethod
    def get_question_themes(cls, user_id: str) -> tuple[str, ...]:
        """获取用户关注的主题

        基于问题关键词频率提取。

        Args:
            user_id: 用户ID

        Returns:
            主题关键词列表（频率降序）
        """
        with cls._lock:
            profile = cls._profiles.get(user_id)
            if profile is None:
                return ()

            keywords = profile["question_keywords"]

        return tuple(word for word, _ in keywords.most_common(10))

    @classmethod
    def get_patterns(cls, user_id: str) -> tuple[Pattern, ...]:
        """获取用户行为模式

        自动分析并返回已识别的模式。

        Args:
            user_id: 用户ID

        Returns:
            行为模式列表
        """
        # [M2] 在锁内拷贝数据，避免并发修改
        with cls._lock:
            profile = cls._profiles.get(user_id)
            if profile is None:
                return ()
            session_times = list(profile.get("session_times", []))
            hex_counts = profile["hexagram_counts"].copy()
            keyword_counts = profile["question_keywords"].copy()

        patterns: list[Pattern] = []
        now = time.time()

        # 1. 高频卦象模式
        hex_freq = cls.get_frequent_hexagrams(user_id, limit=3)
        for hex_name, freq in hex_freq:
            if freq > 0.15:  # 超过 15% 算高频
                patterns.append(Pattern(
                    pattern_type=PatternType.FREQUENT_HEXAGRAM,
                    description=f"频繁占卜 {hex_name} 卦（{freq:.0%}）",
                    frequency=int(freq * 100),
                    confidence=min(freq * 2, 1.0),
                    first_seen=session_times[0] if session_times else now,
                    last_seen=session_times[-1] if session_times else now,
                ))

        # 2. 反复主题模式
        themes = cls.get_question_themes(user_id)
        if len(themes) >= 3:
            patterns.append(Pattern(
                pattern_type=PatternType.RECURRING_THEME,
                description=f"反复关注主题: {', '.join(themes[:3])}",
                frequency=len(themes),
                confidence=0.7,
                first_seen=session_times[0] if session_times else now,
                last_seen=session_times[-1] if session_times else now,
            ))

        # 3. 时间规律模式
        time_pattern = cls._detect_time_pattern(session_times)
        if time_pattern:
            patterns.append(time_pattern)

        return tuple(patterns)

    @classmethod
    def get_profile_summary(cls, user_id: str) -> dict:
        """获取用户档案摘要

        Args:
            user_id: 用户ID

        Returns:
            摘要字典
        """
        profile = cls._profiles.get(user_id)
        if profile is None:
            return {}

        hex_freq = cls.get_frequent_hexagrams(user_id, limit=3)
        themes = cls.get_question_themes(user_id)
        patterns = cls.get_patterns(user_id)

        return {
            "total_sessions": len(profile.get("session_times", [])),
            "frequent_hexagrams": [
                {"name": name, "frequency": freq}
                for name, freq in hex_freq
            ],
            "themes": themes,
            "patterns_count": len(patterns),
        }

    @classmethod
    def get_session_stats(cls, user_id: str) -> tuple[int, float]:
        """获取用户会话统计

        Args:
            user_id: 用户ID

        Returns:
            (总会话数, 最后活跃时间戳)
        """
        with cls._lock:
            profile = cls._profiles.get(user_id)
            if profile is None:
                return (0, 0.0)
            times = profile.get("session_times", [])
            return (len(times), times[-1] if times else 0.0)

    @classmethod
    def count(cls, user_id: str | None = None) -> int:
        """统计模式数量

        [H1 修复] 动态计算而非读取空列表。

        Args:
            user_id: 用户ID，None 则统计全部

        Returns:
            模式数量
        """
        if user_id is None:
            total = 0
            with cls._lock:
                for uid in cls._profiles:
                    total += len(cls.get_patterns(uid))
            return total
        return len(cls.get_patterns(user_id))

    @classmethod
    def _get_or_create_profile(cls, user_id: str) -> dict:
        """获取或创建用户档案（调用者需持有锁）"""
        if user_id not in cls._profiles:
            cls._profiles[user_id] = {
                "hexagram_counts": Counter(),
                "question_keywords": Counter(),
                "session_times": [],
            }
        return cls._profiles[user_id]

    @classmethod
    def _detect_time_pattern(
        cls,
        session_times: list[float],
    ) -> Pattern | None:
        """检测时间规律

        分析会话时间的分布，识别规律性行为。

        Args:
            session_times: 会话时间戳列表

        Returns:
            检测到的时间模式，或 None
        """
        if len(session_times) < 5:
            return None

        # 分析小时分布
        hours = [
            datetime.datetime.fromtimestamp(t).hour
            for t in session_times[-20:]  # 最近 20 次
        ]
        hour_counts = Counter(hours)
        most_common_hour, count = hour_counts.most_common(1)[0]

        if count >= len(hours) * 0.3:  # 30% 以上在同一时段
            if 5 <= most_common_hour < 12:
                period = "上午"
            elif 12 <= most_common_hour < 18:
                period = "下午"
            elif 18 <= most_common_hour < 22:
                period = "晚间"
            else:
                period = "深夜"

            return Pattern(
                pattern_type=PatternType.TIME_PATTERN,
                description=f"习惯在{period}时段占卜",
                frequency=count,
                confidence=count / len(hours),
                first_seen=session_times[0],
                last_seen=session_times[-1],
            )

        return None

    @classmethod
    def reset(cls) -> None:
        """重置所有数据（测试用）"""
        with cls._lock:
            cls._profiles.clear()


def _extract_keywords(text: str) -> list[str]:
    """从文本中提取关键词

    简单实现：按标点分词，过滤停用词和短词。

    Args:
        text: 输入文本

    Returns:
        关键词列表
    """
    # 中文停用词
    stop_words = {
        "的", "了", "在", "是", "我", "有", "和", "就",
        "不", "人", "都", "一", "一个", "上", "也", "很",
        "到", "说", "要", "去", "你", "会", "着", "没有",
        "看", "好", "自己", "这", "他", "她", "它", "们",
        "什么", "吗", "呢", "吧", "啊", "怎么", "如何",
        "请问", "请", "问", "想", "能", "可以", "帮",
    }
    words = re.split(r'[\s,，。、；：！？\?\.!;:\-\(\)\[\]]+', text)
    return [
        w for w in words
        if len(w) >= 2 and w not in stop_words
    ]
