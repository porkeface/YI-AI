"""数据分析类型定义"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """事件类型"""
    PAGE_VIEW = "页面访问"
    DIVINATION = "起卦"
    INTERPRETATION = "解读"
    HISTORY_VIEW = "查看历史"
    HEXAGRAM_ATLAS = "卦象图谱"
    PLUGIN_USE = "插件使用"
    API_CALL = "API调用"
    USER_REGISTER = "用户注册"
    USER_LOGIN = "用户登录"


class MetricType(str, Enum):
    """指标类型"""
    COUNT = "计数"
    SUM = "求和"
    AVERAGE = "平均"
    RATE = "比率"
    PERCENTILE = "百分位"


@dataclass(frozen=True)
class AnalyticsEvent:
    """分析事件

    Attributes:
        event_id: 事件ID
        event_type: 事件类型
        user_id: 用户ID
        timestamp: 时间戳
        properties: 事件属性
    """
    event_id: str
    event_type: EventType
    user_id: str
    timestamp: float
    properties: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class MetricValue:
    """指标值

    Attributes:
        metric_name: 指标名称
        metric_type: 指标类型
        value: 指标值
        period_start: 周期开始
        period_end: 周期结束
    """
    metric_name: str
    metric_type: MetricType
    value: float
    period_start: float = 0.0
    period_end: float = 0.0


@dataclass(frozen=True)
class FunnelStep:
    """漏斗步骤

    Attributes:
        step_name: 步骤名称
        event_type: 对应事件类型
        count: 用户数
        conversion_rate: 转化率
    """
    step_name: str
    event_type: EventType
    count: int
    conversion_rate: float = 0.0


@dataclass(frozen=True)
class FunnelReport:
    """漏斗报告

    Attributes:
        funnel_name: 漏斗名称
        steps: 步骤列表
        overall_conversion: 总体转化率
        period_start: 周期开始
        period_end: 周期结束
    """
    funnel_name: str
    steps: tuple[FunnelStep, ...]
    overall_conversion: float = 0.0
    period_start: float = 0.0
    period_end: float = 0.0


@dataclass(frozen=True)
class DashboardData:
    """仪表盘数据

    Attributes:
        total_users: 总用户数
        active_users: 活跃用户数
        total_sessions: 总会话数
        avg_session_duration: 平均会话时长(秒)
        top_hexagrams: 热门卦象
        top_topics: 热门主题
        metrics: 指标列表
    """
    total_users: int = 0
    active_users: int = 0
    total_sessions: int = 0
    avg_session_duration: float = 0.0
    top_hexagrams: tuple[tuple[str, int], ...] = ()
    top_topics: tuple[tuple[str, int], ...] = ()
    metrics: tuple[MetricValue, ...] = ()
