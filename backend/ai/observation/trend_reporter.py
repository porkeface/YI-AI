"""趋势报告生成器

生成用户变化趋势报告：
- 活动频率趋势
- 主题分布变化
- 情绪走向
- 卦象分布变化
"""

from __future__ import annotations

import logging
import time
from collections import Counter
from typing import Sequence

from ai.observation.types import (
    ObservationConfig,
    ReportPeriod,
    TrendDirection,
    TrendIndicator,
    TrendReport,
)
from ai.memory.types import UserMemory, MemoryType, EmotionalState

logger = logging.getLogger(__name__)


class TrendReporter:
    """趋势报告生成器

    纯函数式设计 — 所有方法为 classmethod。
    根据时间窗口生成趋势报告。
    """

    @classmethod
    def generate_report(
        cls,
        user_id: str,
        memories: Sequence[UserMemory],
        period: ReportPeriod = ReportPeriod.WEEKLY,
        config: ObservationConfig | None = None,
    ) -> TrendReport:
        """生成趋势报告

        Args:
            user_id: 用户ID
            memories: 用户记忆列表
            period: 报告周期
            config: 观察配置

        Returns:
            趋势报告
        """
        if config is None:
            config = ObservationConfig()

        now = time.time()
        period_seconds = cls._get_period_seconds(period)
        period_start = now - period_seconds

        # 筛选时间窗口内的记忆
        period_memories = [
            m for m in memories
            if m.created_at >= period_start
        ]
        prev_memories = [
            m for m in memories
            if period_start > m.created_at >= period_start - period_seconds
        ]

        # 生成各维度指标
        indicators: list[TrendIndicator] = []

        # 活动频率
        freq_indicator = cls._compute_frequency_trend(
            len(period_memories), len(prev_memories)
        )
        indicators.append(freq_indicator)

        # 情绪趋势
        emotion_indicator = cls._compute_emotion_trend(
            period_memories, prev_memories
        )
        if emotion_indicator:
            indicators.append(emotion_indicator)

        # 主题多样性
        diversity_indicator = cls._compute_diversity_trend(
            period_memories, prev_memories
        )
        if diversity_indicator:
            indicators.append(diversity_indicator)

        # 主要卦象
        dominant_hexagrams = cls._get_dominant_hexagrams(period_memories)

        # 主要主题
        dominant_topics = cls._get_dominant_topics(period_memories)

        # 生成总结
        summary = cls._build_summary(
            period, len(period_memories), indicators,
            dominant_hexagrams, dominant_topics,
        )

        return TrendReport(
            user_id=user_id,
            period=period,
            period_start=period_start,
            period_end=now,
            total_sessions=len(period_memories),
            dominant_hexagrams=dominant_hexagrams,
            dominant_topics=dominant_topics,
            indicators=tuple(indicators),
            summary=summary,
        )

    @classmethod
    def _get_period_seconds(cls, period: ReportPeriod) -> float:
        """获取周期秒数"""
        day = 86400
        mapping = {
            ReportPeriod.DAILY: day,
            ReportPeriod.WEEKLY: 7 * day,
            ReportPeriod.MONTHLY: 30 * day,
            ReportPeriod.QUARTERLY: 90 * day,
        }
        return mapping.get(period, 7 * day)

    @classmethod
    def _compute_frequency_trend(
        cls,
        current_count: int,
        previous_count: int,
    ) -> TrendIndicator:
        """计算活动频率趋势"""
        if previous_count > 0:
            change_rate = (current_count - previous_count) / previous_count
        else:
            change_rate = 1.0 if current_count > 0 else 0.0

        direction = cls._classify_direction(change_rate)

        return TrendIndicator(
            metric="活动频率",
            current_value=float(current_count),
            previous_value=float(previous_count),
            change_rate=round(change_rate, 3),
            direction=direction,
        )

    @classmethod
    def _compute_emotion_trend(
        cls,
        current: Sequence[UserMemory],
        previous: Sequence[UserMemory],
    ) -> TrendIndicator | None:
        """计算情绪趋势

        情绪得分：积极=1, 期待=0.8, 中性=0.5, 困惑=0.3, 担忧=0.2, 焦虑=0.1
        """
        emotion_scores: dict[str, float] = {
            EmotionalState.POSITIVE.value: 1.0,
            EmotionalState.HOPEFUL.value: 0.8,
            EmotionalState.NEUTRAL.value: 0.5,
            EmotionalState.CONFUSED.value: 0.3,
            EmotionalState.WORRIED.value: 0.2,
            EmotionalState.ANXIOUS.value: 0.1,
        }

        def avg_emotion_score(
            mems: Sequence[UserMemory],
        ) -> float:
            scores = []
            for m in mems:
                if m.memory_type == MemoryType.EMOTIONAL:
                    for state_name, score in emotion_scores.items():
                        if state_name in m.content:
                            scores.append(score)
                            break
            return sum(scores) / len(scores) if scores else 0.5

        current_score = avg_emotion_score(current)
        previous_score = avg_emotion_score(previous)

        if current_score == 0.5 and previous_score == 0.5:
            return None

        change_rate = current_score - previous_score
        direction = cls._classify_direction(change_rate)

        return TrendIndicator(
            metric="情绪状态",
            current_value=round(current_score, 3),
            previous_value=round(previous_score, 3),
            change_rate=round(change_rate, 3),
            direction=direction,
        )

    @classmethod
    def _compute_diversity_trend(
        cls,
        current: Sequence[UserMemory],
        previous: Sequence[UserMemory],
    ) -> TrendIndicator | None:
        """计算主题多样性趋势"""
        def count_unique_topics(
            mems: Sequence[UserMemory],
        ) -> int:
            topics = set()
            topic_keywords = {
                "事业": ("工作", "事业", "职业"),
                "感情": ("感情", "爱情", "婚姻"),
                "财运": ("财运", "投资", "理财"),
                "健康": ("健康", "身体", "生病"),
                "学业": ("考试", "学习", "学业"),
            }
            for m in mems:
                content = m.content.lower()
                for topic, keywords in topic_keywords.items():
                    if any(kw in content for kw in keywords):
                        topics.add(topic)
            return len(topics)

        current_diversity = count_unique_topics(current)
        previous_diversity = count_unique_topics(previous)

        if current_diversity == 0 and previous_diversity == 0:
            return None

        change_rate = (
            (current_diversity - previous_diversity) / max(previous_diversity, 1)
        )

        return TrendIndicator(
            metric="主题多样性",
            current_value=float(current_diversity),
            previous_value=float(previous_diversity),
            change_rate=round(change_rate, 3),
            direction=cls._classify_direction(change_rate),
        )

    @classmethod
    def _get_dominant_hexagrams(
        cls,
        memories: Sequence[UserMemory],
        top_n: int = 3,
    ) -> tuple[str, ...]:
        """获取主要卦象"""
        counts: Counter[str] = Counter()
        for m in memories:
            if m.hexagram_name:
                counts[m.hexagram_name] += 1
        return tuple(name for name, _ in counts.most_common(top_n))

    @classmethod
    def _get_dominant_topics(
        cls,
        memories: Sequence[UserMemory],
        top_n: int = 3,
    ) -> tuple[str, ...]:
        """获取主要主题"""
        topic_keywords: dict[str, tuple[str, ...]] = {
            "事业": ("工作", "事业", "职业", "升职", "跳槽"),
            "感情": ("感情", "爱情", "婚姻", "恋爱", "对象"),
            "财运": ("财运", "投资", "理财", "赚钱"),
            "健康": ("健康", "身体", "生病", "医院"),
            "学业": ("考试", "学习", "学业", "考研"),
        }
        counts: Counter[str] = Counter()
        for m in memories:
            content = m.content.lower()
            for topic, keywords in topic_keywords.items():
                if any(kw in content for kw in keywords):
                    counts[topic] += 1
        return tuple(topic for topic, _ in counts.most_common(top_n))

    @classmethod
    def _classify_direction(
        cls,
        change_rate: float,
    ) -> TrendDirection:
        """分类趋势方向"""
        if change_rate > 0.3:
            return TrendDirection.IMPROVING
        elif change_rate < -0.3:
            return TrendDirection.DECLINING
        elif abs(change_rate) < 0.1:
            return TrendDirection.STABLE
        else:
            return TrendDirection.TRANSITIONAL

    @classmethod
    def _build_summary(
        cls,
        period: ReportPeriod,
        total_sessions: int,
        indicators: Sequence[TrendIndicator],
        dominant_hexagrams: tuple[str, ...],
        dominant_topics: tuple[str, ...],
    ) -> str:
        """构建报告总结"""
        parts: list[str] = []

        period_names = {
            ReportPeriod.DAILY: "今日",
            ReportPeriod.WEEKLY: "本周",
            ReportPeriod.MONTHLY: "本月",
            ReportPeriod.QUARTERLY: "本季度",
        }
        period_name = period_names.get(period, "本期")

        parts.append(f"{period_name}共进行{total_sessions}次占卜。")

        if dominant_hexagrams:
            hex_str = "、".join(dominant_hexagrams[:3])
            parts.append(f"主要卦象：{hex_str}。")

        if dominant_topics:
            topic_str = "、".join(dominant_topics[:3])
            parts.append(f"关注主题：{topic_str}。")

        for ind in indicators:
            direction_desc = {
                TrendDirection.IMPROVING: "呈上升趋势",
                TrendDirection.DECLINING: "呈下降趋势",
                TrendDirection.STABLE: "保持平稳",
                TrendDirection.VOLATILE: "波动较大",
                TrendDirection.TRANSITIONAL: "处于转折期",
            }
            desc = direction_desc.get(ind.direction, "")
            parts.append(f"{ind.metric}{desc}。")

        return "".join(parts)
