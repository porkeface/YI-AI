"""自动观察Agent

持续监控用户变化模式，自动发现：
- 周期性模式（某些卦反复出现）
- 趋势变化（情绪/主题的长期变化）
- 异常检测（突然的卦象转变）
- 趋势报告生成
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from collections import Counter
from typing import Literal

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PatternDetection:
    """模式检测结果"""
    pattern_type: Literal["周期性", "渐变", "突变", "稳定"]
    description: str
    confidence: float  # 0-1
    hexagrams_involved: tuple[str, ...]
    time_span_days: int


@dataclass(frozen=True)
class AnomalyDetection:
    """异常检测结果"""
    anomaly_type: Literal["卦象突变", "情绪波动", "主题转变", "频率异常"]
    description: str
    severity: Literal["低", "中", "高"]
    current_hexagram: str
    previous_hexagrams: tuple[str, ...]


@dataclass(frozen=True)
class TrendReport:
    """趋势报告"""
    user_id: str
    period_days: int
    total_divinations: int
    dominant_hexagrams: tuple[tuple[str, int], ...]  # (卦名, 次数)
    dominant_elements: tuple[tuple[str, float], ...]  # (五行, 占比)
    topic_distribution: tuple[tuple[str, int], ...]   # (主题, 次数)
    patterns: tuple[PatternDetection, ...]
    anomalies: tuple[AnomalyDetection, ...]
    emotional_trend: str
    summary: str


@dataclass(frozen=True)
class HexagramRecord:
    """卦记录（简化版，用于观察分析）"""
    hexagram_name: str
    element: str
    question_topic: str
    sentiment: str
    timestamp_iso: str
    moving_lines: tuple[int, ...]


class ObserverAgent:
    """自动观察Agent

    分析用户历史卦记录，发现模式和趋势。
    """

    @staticmethod
    def analyze_patterns(
        records: list[HexagramRecord],
        min_pattern_count: int = 3,
    ) -> tuple[PatternDetection, ...]:
        """分析用户变化模式

        Args:
            records: 用户历史卦记录（按时间排序）
            min_pattern_count: 最小模式出现次数

        Returns:
            检测到的模式列表
        """
        if len(records) < 3:
            return ()

        patterns: list[PatternDetection] = []

        # 1. 周期性模式检测
        cycle_pattern = ObserverAgent._detect_cycle_pattern(records, min_pattern_count)
        if cycle_pattern:
            patterns.append(cycle_pattern)

        # 2. 渐变模式检测
        gradual_pattern = ObserverAgent._detect_gradual_pattern(records)
        if gradual_pattern:
            patterns.append(gradual_pattern)

        # 3. 稳定性检测
        stability_pattern = ObserverAgent._detect_stability_pattern(records)
        if stability_pattern:
            patterns.append(stability_pattern)

        return tuple(patterns)

    @staticmethod
    def detect_anomalies(
        records: list[HexagramRecord],
        window_size: int = 5,
    ) -> tuple[AnomalyDetection, ...]:
        """检测异常

        Args:
            records: 用户历史卦记录
            window_size: 滑动窗口大小

        Returns:
            检测到的异常列表
        """
        if len(records) < window_size + 1:
            return ()

        anomalies: list[AnomalyDetection] = []

        # 1. 卦象突变检测
        recent = records[-window_size:]
        previous = records[-(window_size * 2):-window_size] if len(records) >= window_size * 2 else records[:window_size]

        recent_elements = Counter(r.element for r in recent)
        prev_elements = Counter(r.element for r in previous)

        # 检查五行分布是否发生显著变化
        for elem in set(recent_elements.keys()) | set(prev_elements.keys()):
            recent_ratio = recent_elements.get(elem, 0) / len(recent)
            prev_ratio = prev_elements.get(elem, 0) / len(previous) if previous else 0

            if abs(recent_ratio - prev_ratio) > 0.4:
                anomalies.append(AnomalyDetection(
                    anomaly_type="卦象突变",
                    description=f"五行'{elem}'占比从{prev_ratio:.0%}突变到{recent_ratio:.0%}",
                    severity="中",
                    current_hexagram=records[-1].hexagram_name,
                    previous_hexagrams=tuple(r.hexagram_name for r in previous[-3:]),
                ))

        # 2. 情绪波动检测
        recent_sentiments = [r.sentiment for r in recent]
        prev_sentiments = [r.sentiment for r in previous]

        negative_recent = sum(1 for s in recent_sentiments if s in ("anxious", "negative"))
        negative_prev = sum(1 for s in prev_sentiments if s in ("anxious", "negative"))

        if negative_recent >= 3 and negative_prev <= 1:
            anomalies.append(AnomalyDetection(
                anomaly_type="情绪波动",
                description=f"近期负面情绪显著增加（{negative_recent}/{len(recent)}）",
                severity="高",
                current_hexagram=records[-1].hexagram_name,
                previous_hexagrams=tuple(r.hexagram_name for r in previous[-3:]),
            ))

        # 3. 主题转变检测
        recent_topics = Counter(r.question_topic for r in recent if r.question_topic)
        prev_topics = Counter(r.question_topic for r in previous if r.question_topic)

        if recent_topics and prev_topics:
            top_recent = recent_topics.most_common(1)[0][0]
            top_prev = prev_topics.most_common(1)[0][0]

            if top_recent != top_prev:
                anomalies.append(AnomalyDetection(
                    anomaly_type="主题转变",
                    description=f"关注主题从'{top_prev}'转向'{top_recent}'",
                    severity="低",
                    current_hexagram=records[-1].hexagram_name,
                    previous_hexagrams=tuple(r.hexagram_name for r in previous[-3:]),
                ))

        return tuple(anomalies)

    @staticmethod
    def generate_report(
        user_id: str,
        records: list[HexagramRecord],
        period_days: int = 30,
    ) -> TrendReport:
        """生成趋势报告

        Args:
            user_id: 用户ID
            records: 该时间段内的卦记录
            period_days: 报告周期天数

        Returns:
            趋势报告
        """
        if not records:
            return TrendReport(
                user_id=user_id,
                period_days=period_days,
                total_divinations=0,
                dominant_hexagrams=(),
                dominant_elements=(),
                topic_distribution=(),
                patterns=(),
                anomalies=(),
                emotional_trend="数据不足",
                summary="该时间段内无卦记录。",
            )

        # 统计卦象频率
        hex_counter = Counter(r.hexagram_name for r in records)
        dominant_hexagrams = tuple(hex_counter.most_common(5))

        # 统计五行分布
        elem_counter = Counter(r.element for r in records)
        total = len(records)
        dominant_elements = tuple(
            (elem, count / total)
            for elem, count in elem_counter.most_common(5)
        )

        # 统计主题分布
        topic_counter = Counter(r.question_topic for r in records if r.question_topic)
        topic_distribution = tuple(topic_counter.most_common(5))

        # 检测模式
        patterns = ObserverAgent.analyze_patterns(records)

        # 检测异常
        anomalies = ObserverAgent.detect_anomalies(records)

        # 情绪趋势
        sentiments = [r.sentiment for r in records]
        positive = sum(1 for s in sentiments if s == "positive")
        negative = sum(1 for s in sentiments if s in ("anxious", "negative"))

        if positive > negative * 2:
            emotional_trend = "积极向上"
        elif negative > positive * 2:
            emotional_trend = "需要关注"
        else:
            emotional_trend = "平稳"

        # 生成总结
        summary = ObserverAgent._build_summary(
            user_id, records, dominant_hexagrams,
            dominant_elements, patterns, anomalies, emotional_trend
        )

        return TrendReport(
            user_id=user_id,
            period_days=period_days,
            total_divinations=len(records),
            dominant_hexagrams=dominant_hexagrams,
            dominant_elements=dominant_elements,
            topic_distribution=topic_distribution,
            patterns=patterns,
            anomalies=anomalies,
            emotional_trend=emotional_trend,
            summary=summary,
        )

    # ==== 内部方法 ====

    @staticmethod
    def _detect_cycle_pattern(
        records: list[HexagramRecord],
        min_count: int,
    ) -> PatternDetection | None:
        """检测周期性模式"""
        hex_counter = Counter(r.hexagram_name for r in records)

        # 找出频繁出现的卦
        frequent = [
            (name, count) for name, count in hex_counter.items()
            if count >= min_count
        ]

        if not frequent:
            return None

        frequent.sort(key=lambda x: x[1], reverse=True)
        top_names = [name for name, _ in frequent[:3]]

        return PatternDetection(
            pattern_type="周期性",
            description=f"卦象{', '.join(top_names)}反复出现（{frequent[0][1]}次）",
            confidence=min(0.9, frequent[0][1] / len(records)),
            hexagrams_involved=tuple(top_names),
            time_span_days=len(records),
        )

    @staticmethod
    def _detect_gradual_pattern(
        records: list[HexagramRecord],
    ) -> PatternDetection | None:
        """检测渐变模式"""
        if len(records) < 5:
            return None

        # 分析前半段和后半段的五行变化
        mid = len(records) // 2
        first_half = records[:mid]
        second_half = records[mid:]

        first_elem = Counter(r.element for r in first_half).most_common(1)[0][0]
        second_elem = Counter(r.element for r in second_half).most_common(1)[0][0]

        if first_elem != second_elem:
            return PatternDetection(
                pattern_type="渐变",
                description=f"五行从'{first_elem}'主导向'{second_elem}'主导渐变",
                confidence=0.6,
                hexagrams_involved=(
                    first_half[0].hexagram_name,
                    second_half[-1].hexagram_name,
                ),
                time_span_days=len(records),
            )

        return None

    @staticmethod
    def _detect_stability_pattern(
        records: list[HexagramRecord],
    ) -> PatternDetection | None:
        """检测稳定性模式"""
        hex_counter = Counter(r.hexagram_name for r in records)

        # 如果最频繁的卦占比超过50%，说明很稳定
        most_common_count = hex_counter.most_common(1)[0][1]
        ratio = most_common_count / len(records)

        if ratio > 0.5:
            return PatternDetection(
                pattern_type="稳定",
                description=f"持续围绕'{hex_counter.most_common(1)[0][0]}'卦（占比{ratio:.0%}）",
                confidence=ratio,
                hexagrams_involved=(hex_counter.most_common(1)[0][0],),
                time_span_days=len(records),
            )

        return None

    @staticmethod
    def _build_summary(
        user_id: str,
        records: list[HexagramRecord],
        dominant_hexagrams: tuple[tuple[str, int], ...],
        dominant_elements: tuple[tuple[str, float], ...],
        patterns: tuple[PatternDetection, ...],
        anomalies: tuple[AnomalyDetection, ...],
        emotional_trend: str,
    ) -> str:
        """构建报告摘要"""
        parts = []

        parts.append(f"用户{user_id}近{len(records)}次卦象分析：")

        if dominant_hexagrams:
            top = dominant_hexagrams[0]
            parts.append(f"最常出现：{top[0]}（{top[1]}次）")

        if dominant_elements:
            top_elem = dominant_elements[0]
            parts.append(f"主导五行：{top_elem[0]}（{top_elem[1]:.0%}）")

        parts.append(f"情绪趋势：{emotional_trend}")

        if patterns:
            parts.append(f"发现{len(patterns)}个模式：")
            for p in patterns:
                parts.append(f"  - {p.description}")

        if anomalies:
            parts.append(f"发现{len(anomalies)}个异常：")
            for a in anomalies:
                parts.append(f"  - [{a.severity}] {a.description}")

        return "\n".join(parts)
