"""自动观察Agent

整合模式检测、趋势报告、异常检测，提供统一的观察接口。
与 MemoryEngine 集成，自动分析用户历史数据。
"""

from __future__ import annotations

import logging
import time
from typing import Sequence

from ai.observation.types import (
    AnomalyAlert,
    DetectedPattern,
    ObservationConfig,
    ObservationType,
    ReportPeriod,
    TrendIndicator,
    TrendReport,
    UserObservation,
)
from ai.observation.pattern_detector import PatternDetector
from ai.observation.anomaly_detector import AnomalyDetector
from ai.observation.trend_reporter import TrendReporter
from ai.memory.types import UserMemory

logger = logging.getLogger(__name__)


class ObservationAgent:
    """自动观察Agent

    classmethod-only API — 不可实例化。
    整合三个子模块，提供统一的用户观察接口。
    """

    @classmethod
    def observe(
        cls,
        user_id: str,
        memories: Sequence[UserMemory],
        config: ObservationConfig | None = None,
    ) -> UserObservation:
        """执行完整观察分析

        同时运行模式检测、趋势分析、异常检测。

        Args:
            user_id: 用户ID
            memories: 用户记忆列表
            config: 观察配置

        Returns:
            用户观察结果
        """
        if config is None:
            config = ObservationConfig()

        now = time.time()

        # 模式检测
        patterns = PatternDetector.detect_all(memories, config)

        # 异常检测
        anomalies = AnomalyDetector.detect_all(memories, config)

        # 趋势指标（从周报中提取）
        weekly_report = TrendReporter.generate_report(
            user_id, memories, ReportPeriod.WEEKLY, config
        )
        trends = weekly_report.indicators

        # 生成总结
        summary = cls._build_observation_summary(
            user_id, patterns, trends, anomalies
        )

        logger.info(
            "observation_complete: user=%s patterns=%d anomalies=%d",
            user_id, len(patterns), len(anomalies),
        )

        return UserObservation(
            user_id=user_id,
            observation_type=ObservationType.PATTERN,
            patterns=patterns,
            trends=trends,
            anomalies=anomalies,
            summary=summary,
            generated_at=now,
        )

    @classmethod
    def get_trend_report(
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
        return TrendReporter.generate_report(
            user_id, memories, period, config
        )

    @classmethod
    def check_anomalies(
        cls,
        memories: Sequence[UserMemory],
        config: ObservationConfig | None = None,
    ) -> tuple[AnomalyAlert, ...]:
        """仅执行异常检测

        Args:
            memories: 用户记忆列表
            config: 观察配置

        Returns:
            异常警报列表
        """
        return AnomalyDetector.detect_all(memories, config)

    @classmethod
    def detect_patterns(
        cls,
        memories: Sequence[UserMemory],
        config: ObservationConfig | None = None,
    ) -> tuple[DetectedPattern, ...]:
        """仅执行模式检测

        Args:
            memories: 用户记忆列表
            config: 观察配置

        Returns:
            检测到的模式列表
        """
        return PatternDetector.detect_all(memories, config)

    @classmethod
    def _build_observation_summary(
        cls,
        user_id: str,
        patterns: Sequence[DetectedPattern],
        trends: Sequence[TrendIndicator],
        anomalies: Sequence[AnomalyAlert],
    ) -> str:
        """构建观察总结"""
        parts: list[str] = []

        parts.append(f"用户{user_id}观察报告：")

        if patterns:
            parts.append(f"发现{len(patterns)}个行为模式。")
            for p in patterns[:3]:
                parts.append(f"- {p.description}")
        else:
            parts.append("未发现显著行为模式。")

        if anomalies:
            warning_count = sum(
                1 for a in anomalies
                if a.severity.value in ("警告", "严重")
            )
            if warning_count > 0:
                parts.append(
                    f"检测到{warning_count}个需要注意的异常。"
                )

        for t in trends:
            parts.append(f"{t.metric}：{t.direction.value}")

        return "\n".join(parts)
