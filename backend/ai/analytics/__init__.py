"""数据分析模块

用户行为分析平台，包括：
- EventTracker: 事件追踪器
- 类型定义: 事件、指标、漏斗、仪表盘
"""

from ai.analytics.tracker import EventTracker
from ai.analytics.types import (
    EventType,
    MetricType,
    AnalyticsEvent,
    MetricValue,
    FunnelStep,
    FunnelReport,
    DashboardData,
)

__all__ = [
    # 核心
    "EventTracker",
    # 类型
    "EventType",
    "MetricType",
    "AnalyticsEvent",
    "MetricValue",
    "FunnelStep",
    "FunnelReport",
    "DashboardData",
]
