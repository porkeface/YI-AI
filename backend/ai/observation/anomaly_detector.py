"""异常检测器

检测用户行为中的异常模式：
- 频率异常（突然大量占卜或长期沉默）
- 卦象异常（突然出现罕见卦象）
- 情绪异常（情绪剧烈波动）
- 主题异常（突然转向完全不同的主题）
"""

from __future__ import annotations

import logging
import math
import time
from collections import Counter
from typing import Sequence

from ai.observation.types import (
    AnomalyAlert,
    AnomalySeverity,
    ObservationConfig,
)
from ai.memory.types import UserMemory, MemoryType, EmotionalState

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """异常检测器

    纯函数式设计 — 所有方法为 classmethod。
    使用统计方法（Z-score）检测异常。
    """

    @classmethod
    def detect_all(
        cls,
        memories: Sequence[UserMemory],
        config: ObservationConfig | None = None,
    ) -> tuple[AnomalyAlert, ...]:
        """执行全部异常检测

        Args:
            memories: 用户记忆列表
            config: 观察配置

        Returns:
            异常警报列表（按严重程度降序）
        """
        if config is None:
            config = ObservationConfig()

        if len(memories) < 3:
            return ()

        alerts: list[AnomalyAlert] = []

        # 频率异常
        freq_alerts = cls.detect_frequency_anomalies(memories, config)
        alerts.extend(freq_alerts)

        # 情绪异常
        emotion_alerts = cls.detect_emotional_anomalies(memories, config)
        alerts.extend(emotion_alerts)

        # 主题突变
        topic_alerts = cls.detect_topic_shifts(memories, config)
        alerts.extend(topic_alerts)

        # 按严重程度排序
        severity_order = {
            AnomalySeverity.CRITICAL: 0,
            AnomalySeverity.WARNING: 1,
            AnomalySeverity.INFO: 2,
        }
        alerts.sort(key=lambda a: severity_order.get(a.severity, 99))

        return tuple(alerts)

    @classmethod
    def detect_frequency_anomalies(
        cls,
        memories: Sequence[UserMemory],
        config: ObservationConfig,
    ) -> list[AnomalyAlert]:
        """检测频率异常

        使用 Z-score 检测占卜频率的突然变化。

        Args:
            memories: 用户记忆列表
            config: 观察配置

        Returns:
            频率异常警报列表
        """
        now = time.time()
        day_seconds = 86400

        # 按天统计频率
        daily_counts: Counter[int] = Counter()
        for mem in memories:
            if mem.created_at > 0:
                day_offset = int((now - mem.created_at) / day_seconds)
                daily_counts[day_offset] += 1

        alerts = []

        # 检测长期沉默（最近7天无活动）— 独立于统计检测
        recent_count = sum(
            daily_counts.get(d, 0) for d in range(7)
        )
        if recent_count == 0 and len(memories) >= 10:
            alerts.append(
                AnomalyAlert(
                    severity=AnomalySeverity.INFO,
                    anomaly_type="长期沉默",
                    description="用户近7天无占卜活动",
                    detected_at=now,
                    related_data=("沉默天数:7",),
                    recommendation="可考虑发送关怀提醒",
                )
            )

        if len(daily_counts) < 3:
            return alerts

        counts = list(daily_counts.values())
        mean = sum(counts) / len(counts)
        variance = sum((c - mean) ** 2 for c in counts) / len(counts)
        std = math.sqrt(variance) if variance > 0 else 0

        if std == 0:
            return alerts

        z_threshold = config.anomaly_z_score

        # 检测近3天的异常
        for day_offset in range(3):
            count = daily_counts.get(day_offset, 0)
            z_score = (count - mean) / std

            if z_score > z_threshold and count >= 5:
                alerts.append(
                    AnomalyAlert(
                        severity=AnomalySeverity.WARNING,
                        anomaly_type="频率激增",
                        description=(
                            f"近{day_offset + 1}天内占卜{count}次，"
                            f"远超日常均值{mean:.1f}次"
                        ),
                        detected_at=now,
                        related_data=(
                            f"当日次数:{count}",
                            f"均值:{mean:.1f}",
                            f"Z-score:{z_score:.1f}",
                        ),
                        recommendation="关注用户是否有紧急决策需求",
                    )
                )

        return alerts

    @classmethod
    def detect_emotional_anomalies(
        cls,
        memories: Sequence[UserMemory],
        config: ObservationConfig,
    ) -> list[AnomalyAlert]:
        """检测情绪异常

        检测情绪剧烈波动或持续消极状态。

        Args:
            memories: 用户记忆列表
            config: 观察配置

        Returns:
            情绪异常警报列表
        """
        now = time.time()
        alerts = []

        # 提取近期情绪记录（按时间排序）
        emotional_memories = sorted(
            [
                m for m in memories
                if m.memory_type == MemoryType.EMOTIONAL
                and m.created_at > 0
            ],
            key=lambda m: m.created_at,
            reverse=True,
        )

        # 检测持续消极情绪（需要>=3条记录）
        negative_states = {
            EmotionalState.ANXIOUS.value,
            EmotionalState.WORRIED.value,
            EmotionalState.CONFUSED.value,
        }

        if len(emotional_memories) >= 3:
            recent = emotional_memories[:5]
            negative_count = sum(
                1 for m in recent
                if any(ns in m.content for ns in negative_states)
            )

            if negative_count >= 4:
                alerts.append(
                    AnomalyAlert(
                        severity=AnomalySeverity.WARNING,
                        anomaly_type="持续消极情绪",
                        description=(
                            f"近{len(recent)}次记录中{negative_count}次"
                            f"为消极情绪（焦虑/担忧/困惑）"
                        ),
                        detected_at=now,
                        related_data=(
                            f"消极次数:{negative_count}",
                            f"总记录:{len(recent)}",
                        ),
                        recommendation="关注用户心理状态，建议正面引导",
                    )
                )

        # 检测情绪突变（从积极突然转为消极，需要>=2条记录）
        if len(emotional_memories) >= 2:
            positive_states = {
                EmotionalState.POSITIVE.value,
                EmotionalState.HOPEFUL.value,
            }
            prev = emotional_memories[1]
            curr = emotional_memories[0]

            prev_positive = any(ps in prev.content for ps in positive_states)
            curr_negative = any(ns in curr.content for ns in negative_states)

            if prev_positive and curr_negative:
                time_diff_hours = (
                    (curr.created_at - prev.created_at) / 3600
                )
                if time_diff_hours < 48:
                    alerts.append(
                        AnomalyAlert(
                            severity=AnomalySeverity.INFO,
                            anomaly_type="情绪突变",
                            description=(
                                f"用户情绪从积极突变为消极"
                                f"（{time_diff_hours:.0f}小时内）"
                            ),
                            detected_at=now,
                            related_data=(
                                f"前次情绪:{prev.content[:30]}",
                                f"当前情绪:{curr.content[:30]}",
                            ),
                            recommendation="关注近期是否有重大变故",
                        )
                    )

        return alerts

    @classmethod
    def detect_topic_shifts(
        cls,
        memories: Sequence[UserMemory],
        config: ObservationConfig,
    ) -> list[AnomalyAlert]:
        """检测主题突变

        检测用户关注主题的突然大幅转变。

        Args:
            memories: 用户记忆列表
            config: 观察配置

        Returns:
            主题突变警报列表
        """
        topic_keywords: dict[str, tuple[str, ...]] = {
            "事业": ("工作", "事业", "职业", "升职", "跳槽", "创业"),
            "感情": ("感情", "爱情", "婚姻", "恋爱", "对象", "分手"),
            "财运": ("财运", "投资", "理财", "赚钱", "收入"),
            "健康": ("健康", "身体", "生病", "医院"),
            "学业": ("考试", "学习", "学业", "考研"),
        }

        # 按时间排序
        sorted_memories = sorted(
            [m for m in memories if m.created_at > 0],
            key=lambda m: m.created_at,
        )

        if len(sorted_memories) < 6:
            return []

        # 将记忆分为前半和后半
        mid = len(sorted_memories) // 2
        first_half = sorted_memories[:mid]
        second_half = sorted_memories[mid:]

        def get_topics(mems: Sequence[UserMemory]) -> Counter[str]:
            topics: Counter[str] = Counter()
            for m in mems:
                content = m.content.lower()
                for topic, keywords in topic_keywords.items():
                    if any(kw in content for kw in keywords):
                        topics[topic] += 1
            return topics

        first_topics = get_topics(first_half)
        second_topics = get_topics(second_half)

        if not first_topics or not second_topics:
            return []

        # 找出前半的主要主题
        first_main = first_topics.most_common(1)[0]
        first_topic, first_count = first_main
        first_total = sum(first_topics.values())

        # 找出后半的主要主题
        second_main = second_topics.most_common(1)[0]
        second_topic, second_count = second_main
        second_total = sum(second_topics.values())

        alerts = []

        # 如果前后主题完全不同，且各自占比>50%
        if (
            first_topic != second_topic
            and first_count / first_total > 0.5
            and second_count / second_total > 0.5
        ):
            alerts.append(
                AnomalyAlert(
                    severity=AnomalySeverity.INFO,
                    anomaly_type="主题突变",
                    description=(
                        f"用户关注主题从'{first_topic}'转向"
                        f"'{second_topic}'"
                    ),
                    detected_at=time.time(),
                    related_data=(
                        f"前期主题:{first_topic}({first_count}次)",
                        f"近期主题:{second_topic}({second_count}次)",
                    ),
                    recommendation="可能有新的重大生活变化",
                )
            )

        return alerts
