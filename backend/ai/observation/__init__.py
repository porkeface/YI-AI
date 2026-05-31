"""自动观察Agent模块

自动发现用户变化模式、生成趋势报告、异常检测预警。

核心组件：
- ObservationAgent: 统一观察接口
- PatternDetector: 模式检测器
- AnomalyDetector: 异常检测器
- TrendReporter: 趋势报告生成器
"""

from ai.observation.agent import ObservationAgent
from ai.observation.pattern_detector import PatternDetector
from ai.observation.pattern_analyzer import PatternAnalyzer
from ai.observation.anomaly_detector import AnomalyDetector
from ai.observation.trend_reporter import TrendReporter
from ai.observation.types import (
    ObservationType,
    PatternCategory,
    TrendDirection,
    AnomalySeverity,
    ReportPeriod,
    DetectedPattern,
    TrendIndicator,
    TrendReport,
    AnomalyAlert,
    UserObservation,
    ObservationConfig,
)

__all__ = [
    # 核心
    "ObservationAgent",
    "PatternDetector",
    "PatternAnalyzer",
    "AnomalyDetector",
    "TrendReporter",
    # 类型
    "ObservationType",
    "PatternCategory",
    "TrendDirection",
    "AnomalySeverity",
    "ReportPeriod",
    "DetectedPattern",
    "TrendIndicator",
    "TrendReport",
    "AnomalyAlert",
    "UserObservation",
    "ObservationConfig",
]
