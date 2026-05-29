"""自动观察Agent类型定义

观察系统使用的所有数据类型。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ObservationType(str, Enum):
    """观察类型"""
    PATTERN = "模式发现"
    TREND = "趋势分析"
    ANOMALY = "异常检测"


class PatternCategory(str, Enum):
    """模式类别"""
    HEXAGRAM_FREQUENCY = "卦象频率"
    TIME_PATTERN = "时间规律"
    TOPIC_CLUSTER = "主题聚类"
    EMOTIONAL_CYCLE = "情绪周期"
    CHANGE_SEQUENCE = "变化序列"


class TrendDirection(str, Enum):
    """趋势方向"""
    IMPROVING = "上升"
    STABLE = "平稳"
    DECLINING = "下降"
    VOLATILE = "波动"
    TRANSITIONAL = "转折"


class AnomalySeverity(str, Enum):
    """异常严重程度"""
    INFO = "信息"
    WARNING = "警告"
    CRITICAL = "严重"


class ReportPeriod(str, Enum):
    """报告周期"""
    DAILY = "每日"
    WEEKLY = "每周"
    MONTHLY = "每月"
    QUARTERLY = "每季"


@dataclass(frozen=True)
class DetectedPattern:
    """检测到的模式

    Attributes:
        category: 模式类别
        description: 模式描述
        confidence: 置信度 (0.0-1.0)
        frequency: 出现频次
        examples: 相关卦象示例
        first_seen: 首次发现时间戳
        last_seen: 最近一次时间戳
    """
    category: PatternCategory
    description: str
    confidence: float
    frequency: int
    examples: tuple[str, ...] = ()
    first_seen: float = 0.0
    last_seen: float = 0.0


@dataclass(frozen=True)
class TrendIndicator:
    """趋势指标

    Attributes:
        metric: 指标名称
        current_value: 当前值
        previous_value: 之前值
        change_rate: 变化率
        direction: 趋势方向
    """
    metric: str
    current_value: float
    previous_value: float
    change_rate: float
    direction: TrendDirection


@dataclass(frozen=True)
class TrendReport:
    """趋势报告

    Attributes:
        user_id: 用户ID
        period: 报告周期
        period_start: 周期开始时间戳
        period_end: 周期结束时间戳
        total_sessions: 总会话数
        dominant_hexagrams: 主要卦象
        dominant_topics: 主要主题
        indicators: 趋势指标列表
        summary: 总结
    """
    user_id: str
    period: ReportPeriod
    period_start: float
    period_end: float
    total_sessions: int
    dominant_hexagrams: tuple[str, ...] = ()
    dominant_topics: tuple[str, ...] = ()
    indicators: tuple[TrendIndicator, ...] = ()
    summary: str = ""


@dataclass(frozen=True)
class AnomalyAlert:
    """异常警报

    Attributes:
        severity: 严重程度
        anomaly_type: 异常类型
        description: 异常描述
        detected_at: 检测时间戳
        related_data: 相关数据
        recommendation: 建议
    """
    severity: AnomalySeverity
    anomaly_type: str
    description: str
    detected_at: float
    related_data: tuple[str, ...] = ()
    recommendation: str = ""


@dataclass(frozen=True)
class UserObservation:
    """用户观察结果

    Attributes:
        user_id: 用户ID
        observation_type: 观察类型
        patterns: 检测到的模式
        trends: 趋势指标
        anomalies: 异常警报
        summary: 总结
        generated_at: 生成时间戳
    """
    user_id: str
    observation_type: ObservationType
    patterns: tuple[DetectedPattern, ...] = ()
    trends: tuple[TrendIndicator, ...] = ()
    anomalies: tuple[AnomalyAlert, ...] = ()
    summary: str = ""
    generated_at: float = 0.0


@dataclass(frozen=True)
class ObservationConfig:
    """观察配置

    Attributes:
        min_sessions_for_pattern: 检测模式所需最少会话数
        anomaly_z_score: 异常检测Z-score阈值
        trend_window_days: 趋势分析窗口天数
        max_patterns: 最大返回模式数
    """
    min_sessions_for_pattern: int = 5
    anomaly_z_score: float = 2.0
    trend_window_days: int = 30
    max_patterns: int = 10
