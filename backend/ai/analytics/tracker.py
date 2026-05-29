"""事件追踪器

记录和查询用户行为事件。
线程安全 — 使用锁保护共享状态。
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import Counter
from typing import Sequence

from ai.analytics.types import (
    AnalyticsEvent,
    DashboardData,
    EventType,
    FunnelReport,
    FunnelStep,
    MetricType,
    MetricValue,
)

logger = logging.getLogger(__name__)


class EventTracker:
    """事件追踪器

    classmethod-only API — 所有事件存储在模块级变量中。
    """

    # 模块级状态
    _events: list[AnalyticsEvent] = []
    _lock = threading.Lock()
    _max_events: int = 100_000

    @classmethod
    def track(
        cls,
        event_type: EventType,
        user_id: str,
        properties: dict[str, str] | None = None,
        timestamp: float | None = None,
    ) -> AnalyticsEvent:
        """记录事件

        Args:
            event_type: 事件类型
            user_id: 用户ID
            properties: 事件属性
            timestamp: 时间戳（默认当前时间）

        Returns:
            创建的事件
        """
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            user_id=user_id,
            timestamp=timestamp or time.time(),
            properties=tuple((properties or {}).items()),
        )

        with cls._lock:
            cls._events.append(event)
            # 超限时清理旧事件
            if len(cls._events) > cls._max_events:
                cls._events = cls._events[-cls._max_events:]

        return event

    @classmethod
    def query(
        cls,
        event_type: EventType | None = None,
        user_id: str | None = None,
        since: float | None = None,
        until: float | None = None,
        limit: int = 100,
    ) -> tuple[AnalyticsEvent, ...]:
        """查询事件

        Args:
            event_type: 按类型筛选
            user_id: 按用户筛选
            since: 起始时间
            until: 结束时间
            limit: 最大返回数

        Returns:
            符合条件的事件列表
        """
        with cls._lock:
            results = []
            for event in reversed(cls._events):
                if event_type and event.event_type != event_type:
                    continue
                if user_id and event.user_id != user_id:
                    continue
                if since and event.timestamp < since:
                    continue
                if until and event.timestamp > until:
                    continue
                results.append(event)
                if len(results) >= limit:
                    break
            return tuple(results)

    @classmethod
    def count_events(
        cls,
        event_type: EventType | None = None,
        since: float | None = None,
    ) -> int:
        """统计事件数

        Args:
            event_type: 按类型筛选
            since: 起始时间

        Returns:
            事件数量
        """
        with cls._lock:
            count = 0
            for event in cls._events:
                if event_type and event.event_type != event_type:
                    continue
                if since and event.timestamp < since:
                    continue
                count += 1
            return count

    @classmethod
    def get_unique_users(cls, since: float | None = None) -> int:
        """获取独立用户数

        Args:
            since: 起始时间

        Returns:
            独立用户数
        """
        with cls._lock:
            users = set()
            for event in cls._events:
                if since and event.timestamp < since:
                    continue
                users.add(event.user_id)
            return len(users)

    @classmethod
    def build_dashboard(
        cls,
        since: float | None = None,
    ) -> DashboardData:
        """构建仪表盘数据

        Args:
            since: 起始时间

        Returns:
            仪表盘数据
        """
        now = time.time()
        if since is None:
            since = now - 7 * 86400  # 默认7天

        with cls._lock:
            events = [
                e for e in cls._events if e.timestamp >= since
            ]

        if not events:
            return DashboardData()

        # 统计
        users = {e.user_id for e in events}
        hex_counts: Counter[str] = Counter()
        topic_counts: Counter[str] = Counter()
        divination_count = 0

        for event in events:
            if event.event_type == EventType.DIVINATION:
                divination_count += 1
            props = dict(event.properties)
            if "hexagram" in props:
                hex_counts[props["hexagram"]] += 1
            if "topic" in props:
                topic_counts[props["topic"]] += 1

        # 会话时长估算（基于事件间隔）
        durations = []
        user_events: dict[str, list[float]] = {}
        for event in events:
            user_events.setdefault(event.user_id, []).append(
                event.timestamp
            )
        for timestamps in user_events.values():
            if len(timestamps) >= 2:
                timestamps.sort()
                duration = timestamps[-1] - timestamps[0]
                durations.append(duration)

        avg_duration = (
            sum(durations) / len(durations) if durations else 0.0
        )

        # 指标
        metrics = (
            MetricValue(
                "总事件数", MetricType.COUNT, float(len(events)),
                since, now,
            ),
            MetricValue(
                "独立用户", MetricType.COUNT, float(len(users)),
                since, now,
            ),
            MetricValue(
                "起卦次数", MetricType.COUNT, float(divination_count),
                since, now,
            ),
        )

        return DashboardData(
            total_users=len(users),
            active_users=len(users),
            total_sessions=len(events),
            avg_session_duration=avg_duration,
            top_hexagrams=tuple(hex_counts.most_common(5)),
            top_topics=tuple(topic_counts.most_common(5)),
            metrics=metrics,
        )

    @classmethod
    def build_funnel(
        cls,
        funnel_name: str,
        steps: tuple[tuple[str, EventType], ...],
        since: float | None = None,
    ) -> FunnelReport:
        """构建漏斗报告

        Args:
            funnel_name: 漏斗名称
            steps: 步骤定义 [(步骤名, 事件类型), ...]
            since: 起始时间

        Returns:
            漏斗报告
        """
        now = time.time()
        if since is None:
            since = now - 7 * 86400

        funnel_steps: list[FunnelStep] = []
        prev_count = 0

        for step_name, event_type in steps:
            # 统计该步骤的独立用户数
            with cls._lock:
                users = {
                    e.user_id for e in cls._events
                    if e.event_type == event_type
                    and e.timestamp >= since
                }

            count = len(users)
            if prev_count > 0:
                rate = count / prev_count
            else:
                rate = 1.0

            funnel_steps.append(
                FunnelStep(
                    step_name=step_name,
                    event_type=event_type,
                    count=count,
                    conversion_rate=round(rate, 3),
                )
            )
            prev_count = count

        overall = 0.0
        if funnel_steps and funnel_steps[0].count > 0:
            overall = (
                funnel_steps[-1].count / funnel_steps[0].count
            )

        return FunnelReport(
            funnel_name=funnel_name,
            steps=tuple(funnel_steps),
            overall_conversion=round(overall, 3),
            period_start=since,
            period_end=now,
        )

    @classmethod
    def clear(cls) -> None:
        """清空所有事件（用于测试）"""
        with cls._lock:
            cls._events.clear()

    @classmethod
    def total_events(cls) -> int:
        """获取事件总数"""
        with cls._lock:
            return len(cls._events)
