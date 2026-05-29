"""模式检测器

从用户历史数据中检测反复出现的模式：
- 卦象频率模式（某卦反复出现）
- 时间规律模式（固定时段占卜）
- 主题聚类模式（反复问同类问题）
- 情绪周期模式（情绪规律性波动）
- 变化序列模式（固定卦象变化路径）
"""

from __future__ import annotations

import logging
import time
from collections import Counter
from typing import Sequence

from ai.observation.types import (
    DetectedPattern,
    ObservationConfig,
    PatternCategory,
)
from ai.memory.types import UserMemory, MemoryType

logger = logging.getLogger(__name__)


class PatternDetector:
    """模式检测器

    纯函数式设计 — 所有方法为 classmethod，不维护状态。
    输入用户记忆列表，输出检测到的模式。
    """

    @classmethod
    def detect_all(
        cls,
        memories: Sequence[UserMemory],
        config: ObservationConfig | None = None,
    ) -> tuple[DetectedPattern, ...]:
        """执行全部模式检测

        Args:
            memories: 用户记忆列表
            config: 观察配置

        Returns:
            检测到的模式列表（按置信度降序）
        """
        if config is None:
            config = ObservationConfig()

        if len(memories) < config.min_sessions_for_pattern:
            return ()

        patterns: list[DetectedPattern] = []

        # 卦象频率模式
        freq_patterns = cls.detect_hexagram_frequency(memories, config)
        patterns.extend(freq_patterns)

        # 时间规律模式
        time_patterns = cls.detect_time_patterns(memories, config)
        patterns.extend(time_patterns)

        # 主题聚类模式
        topic_patterns = cls.detect_topic_clusters(memories, config)
        patterns.extend(topic_patterns)

        # 情绪周期模式
        emotion_patterns = cls.detect_emotional_cycles(memories, config)
        patterns.extend(emotion_patterns)

        # 变化序列模式
        seq_patterns = cls.detect_change_sequences(memories, config)
        patterns.extend(seq_patterns)

        # 按置信度降序排列，限制数量
        sorted_patterns = sorted(
            patterns, key=lambda p: p.confidence, reverse=True
        )
        return tuple(sorted_patterns[: config.max_patterns])

    @classmethod
    def detect_hexagram_frequency(
        cls,
        memories: Sequence[UserMemory],
        config: ObservationConfig,
    ) -> list[DetectedPattern]:
        """检测卦象频率模式

        当某卦出现频率显著高于均匀分布时，视为模式。

        Args:
            memories: 用户记忆列表
            config: 观察配置

        Returns:
            卦象频率模式列表
        """
        hexagram_counts: Counter[str] = Counter()
        hexagram_times: dict[str, list[float]] = {}

        for mem in memories:
            if mem.hexagram_name and mem.memory_type == MemoryType.EPISODIC:
                hexagram_counts[mem.hexagram_name] += 1
                hexagram_times.setdefault(
                    mem.hexagram_name, []
                ).append(mem.created_at)

        if not hexagram_counts:
            return []

        total = sum(hexagram_counts.values())
        # 均匀分布下每卦概率约 1/64
        expected_ratio = 1.0 / 64
        patterns = []

        for name, count in hexagram_counts.most_common(5):
            actual_ratio = count / total
            # 超过期望值3倍以上视为显著
            if actual_ratio > expected_ratio * 3 and count >= 3:
                confidence = min(1.0, actual_ratio / (expected_ratio * 5))
                times = hexagram_times.get(name, [])
                patterns.append(
                    DetectedPattern(
                        category=PatternCategory.HEXAGRAM_FREQUENCY,
                        description=(
                            f"卦象'{name}'出现{count}次"
                            f"（占比{actual_ratio:.0%}），显著高于平均"
                        ),
                        confidence=round(confidence, 3),
                        frequency=count,
                        examples=(name,),
                        first_seen=min(times) if times else 0.0,
                        last_seen=max(times) if times else 0.0,
                    )
                )

        return patterns

    @classmethod
    def detect_time_patterns(
        cls,
        memories: Sequence[UserMemory],
        config: ObservationConfig,
    ) -> list[DetectedPattern]:
        """检测时间规律模式

        分析用户占卜时间的分布，发现固定时段偏好。

        Args:
            memories: 用户记忆列表
            config: 观察配置

        Returns:
            时间规律模式列表
        """
        import datetime

        hour_counts: Counter[int] = Counter()
        weekday_counts: Counter[int] = Counter()

        for mem in memories:
            if mem.created_at > 0:
                dt = datetime.datetime.fromtimestamp(mem.created_at)
                hour_counts[dt.hour] += 1
                weekday_counts[dt.weekday()] += 1

        total = sum(hour_counts.values())
        if total < config.min_sessions_for_pattern:
            return []

        patterns = []

        # 检测时段偏好
        for hour, count in hour_counts.most_common(3):
            ratio = count / total
            if ratio > 0.25 and count >= 3:
                time_label = f"{hour:02d}:00-{(hour + 2) % 24:02d}:00"
                confidence = min(1.0, ratio / 0.4)
                patterns.append(
                    DetectedPattern(
                        category=PatternCategory.TIME_PATTERN,
                        description=(
                            f"偏好在{time_label}时段占卜"
                            f"（{count}次，占比{ratio:.0%}）"
                        ),
                        confidence=round(confidence, 3),
                        frequency=count,
                        examples=(time_label,),
                    )
                )

        # 检测星期偏好
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for wd, count in weekday_counts.most_common(2):
            ratio = count / total
            if ratio > 0.2 and count >= 3:
                confidence = min(1.0, ratio / 0.3)
                patterns.append(
                    DetectedPattern(
                        category=PatternCategory.TIME_PATTERN,
                        description=(
                            f"偏好在{weekday_names[wd]}占卜"
                            f"（{count}次，占比{ratio:.0%}）"
                        ),
                        confidence=round(confidence, 3),
                        frequency=count,
                        examples=(weekday_names[wd],),
                    )
                )

        return patterns

    @classmethod
    def detect_topic_clusters(
        cls,
        memories: Sequence[UserMemory],
        config: ObservationConfig,
    ) -> list[DetectedPattern]:
        """检测主题聚类模式

        通过关键词匹配发现用户反复关注的主题。

        Args:
            memories: 用户记忆列表
            config: 观察配置

        Returns:
            主题聚类模式列表
        """
        topic_keywords: dict[str, tuple[str, ...]] = {
            "事业": ("工作", "事业", "职业", "升职", "跳槽", "创业", "项目"),
            "感情": ("感情", "爱情", "婚姻", "恋爱", "对象", "分手", "复合"),
            "财运": ("财运", "投资", "理财", "赚钱", "收入", "股票", "基金"),
            "健康": ("健康", "身体", "生病", "医院", "养生", "锻炼"),
            "学业": ("考试", "学习", "学业", "考研", "留学", "成绩"),
            "人际": ("人际", "朋友", "同事", "关系", "社交", "贵人"),
        }

        topic_counts: Counter[str] = Counter()
        topic_examples: dict[str, list[str]] = {}

        for mem in memories:
            content = mem.content.lower()
            for topic, keywords in topic_keywords.items():
                if any(kw in content for kw in keywords):
                    topic_counts[topic] += 1
                    if len(topic_examples.get(topic, [])) < 3:
                        topic_examples.setdefault(topic, []).append(
                            mem.content[:50]
                        )

        total = sum(topic_counts.values())
        if total < 3:
            return []

        patterns = []
        for topic, count in topic_counts.most_common(3):
            ratio = count / total
            if ratio > 0.2 and count >= 3:
                confidence = min(1.0, ratio / 0.4)
                examples = tuple(topic_examples.get(topic, []))
                patterns.append(
                    DetectedPattern(
                        category=PatternCategory.TOPIC_CLUSTER,
                        description=(
                            f"反复关注'{topic}'主题"
                            f"（{count}次，占比{ratio:.0%}）"
                        ),
                        confidence=round(confidence, 3),
                        frequency=count,
                        examples=examples,
                    )
                )

        return patterns

    @classmethod
    def detect_emotional_cycles(
        cls,
        memories: Sequence[UserMemory],
        config: ObservationConfig,
    ) -> list[DetectedPattern]:
        """检测情绪周期模式

        分析情绪标签的规律性变化。

        Args:
            memories: 用户记忆列表
            config: 观察配置

        Returns:
            情绪周期模式列表
        """
        from ai.memory.types import EmotionalState

        emotion_counts: Counter[str] = Counter()

        for mem in memories:
            if mem.memory_type == MemoryType.EMOTIONAL:
                # 从内容中提取情绪标签
                for state in EmotionalState:
                    if state.value in mem.content:
                        emotion_counts[state.value] += 1

        total = sum(emotion_counts.values())
        if total < config.min_sessions_for_pattern:
            return []

        patterns = []

        # 检测主导情绪
        for emotion, count in emotion_counts.most_common(2):
            ratio = count / total
            if ratio > 0.3 and count >= 3:
                confidence = min(1.0, ratio / 0.5)
                patterns.append(
                    DetectedPattern(
                        category=PatternCategory.EMOTIONAL_CYCLE,
                        description=(
                            f"主导情绪为'{emotion}'"
                            f"（{count}次，占比{ratio:.0%}）"
                        ),
                        confidence=round(confidence, 3),
                        frequency=count,
                        examples=(emotion,),
                    )
                )

        return patterns

    @classmethod
    def detect_change_sequences(
        cls,
        memories: Sequence[UserMemory],
        config: ObservationConfig,
    ) -> list[DetectedPattern]:
        """检测变化序列模式

        发现固定的卦象变化路径（A→B→C反复出现）。

        Args:
            memories: 用户记忆列表
            config: 观察配置

        Returns:
            变化序列模式列表
        """
        # 按时间排序，提取卦象序列
        hexagram_timeline = sorted(
            [
                (m.created_at, m.hexagram_name)
                for m in memories
                if m.hexagram_name
                and m.memory_type == MemoryType.EPISODIC
                and m.created_at > 0
            ],
            key=lambda x: x[0],
        )

        if len(hexagram_timeline) < 4:
            return []

        # 提取长度为2-3的子序列
        seq_counts: Counter[tuple[str, ...]] = Counter()

        for window_size in (2, 3):
            for i in range(len(hexagram_timeline) - window_size + 1):
                seq = tuple(
                    name for _, name in hexagram_timeline[i: i + window_size]
                )
                if all(seq):
                    seq_counts[seq] += 1

        patterns = []
        for seq, count in seq_counts.most_common(3):
            if count >= 2:
                seq_str = " → ".join(seq)
                confidence = min(1.0, count / 5)
                patterns.append(
                    DetectedPattern(
                        category=PatternCategory.CHANGE_SEQUENCE,
                        description=(
                            f"变化序列'{seq_str}'出现{count}次"
                        ),
                        confidence=round(confidence, 3),
                        frequency=count,
                        examples=seq,
                    )
                )

        return patterns
