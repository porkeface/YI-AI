"""数据分析模块测试"""

from __future__ import annotations

import time
import pytest
from ai.analytics.types import (
    EventType,
    MetricType,
    AnalyticsEvent,
    MetricValue,
    FunnelStep,
    FunnelReport,
    DashboardData,
)
from ai.analytics.tracker import EventTracker


class TestEventTracker:
    """事件追踪器测试"""

    def setup_method(self):
        EventTracker.clear()

    def test_track_event(self):
        """记录事件"""
        event = EventTracker.track(
            EventType.DIVINATION, "user_1"
        )
        assert event.event_type == EventType.DIVINATION
        assert event.user_id == "user_1"
        assert EventTracker.total_events() == 1

    def test_track_with_properties(self):
        """带属性的事件"""
        event = EventTracker.track(
            EventType.DIVINATION, "user_1",
            properties={"hexagram": "乾为天", "topic": "事业"},
        )
        props = dict(event.properties)
        assert props["hexagram"] == "乾为天"

    def test_query_by_type(self):
        """按类型查询"""
        EventTracker.track(EventType.DIVINATION, "user_1")
        EventTracker.track(EventType.PAGE_VIEW, "user_1")
        EventTracker.track(EventType.DIVINATION, "user_2")

        results = EventTracker.query(event_type=EventType.DIVINATION)
        assert len(results) == 2

    def test_query_by_user(self):
        """按用户查询"""
        EventTracker.track(EventType.DIVINATION, "user_1")
        EventTracker.track(EventType.DIVINATION, "user_2")

        results = EventTracker.query(user_id="user_1")
        assert len(results) == 1

    def test_count_events(self):
        """统计事件数"""
        for _ in range(5):
            EventTracker.track(EventType.DIVINATION, "user_1")
        EventTracker.track(EventType.PAGE_VIEW, "user_1")

        assert EventTracker.count_events() == 6
        assert EventTracker.count_events(EventType.DIVINATION) == 5

    def test_get_unique_users(self):
        """独立用户数"""
        EventTracker.track(EventType.DIVINATION, "user_1")
        EventTracker.track(EventType.DIVINATION, "user_2")
        EventTracker.track(EventType.DIVINATION, "user_1")

        assert EventTracker.get_unique_users() == 2

    def test_build_dashboard(self):
        """构建仪表盘"""
        EventTracker.track(
            EventType.DIVINATION, "user_1",
            properties={"hexagram": "乾为天"},
        )
        EventTracker.track(
            EventType.DIVINATION, "user_2",
            properties={"hexagram": "乾为天"},
        )
        EventTracker.track(EventType.PAGE_VIEW, "user_1")

        dashboard = EventTracker.build_dashboard()
        assert dashboard.total_users == 2
        assert dashboard.total_sessions == 3

    def test_build_funnel(self):
        """构建漏斗"""
        # 3个用户访问，2个起卦，1个看历史
        for uid in ["u1", "u2", "u3"]:
            EventTracker.track(EventType.PAGE_VIEW, uid)
        for uid in ["u1", "u2"]:
            EventTracker.track(EventType.DIVINATION, uid)
        EventTracker.track(EventType.HISTORY_VIEW, "u1")

        funnel = EventTracker.build_funnel(
            "核心漏斗",
            (
                ("访问", EventType.PAGE_VIEW),
                ("起卦", EventType.DIVINATION),
                ("查看历史", EventType.HISTORY_VIEW),
            ),
        )
        assert funnel.funnel_name == "核心漏斗"
        assert len(funnel.steps) == 3
        assert funnel.steps[0].count == 3
        assert funnel.steps[1].count == 2
        assert funnel.steps[2].count == 1

    def test_clear(self):
        """清空事件"""
        EventTracker.track(EventType.DIVINATION, "user_1")
        assert EventTracker.total_events() == 1
        EventTracker.clear()
        assert EventTracker.total_events() == 0


class TestAnalyticsTypes:
    """分析类型测试"""

    def test_analytics_event_frozen(self):
        """AnalyticsEvent 不可变"""
        event = AnalyticsEvent(
            event_id="test",
            event_type=EventType.DIVINATION,
            user_id="user_1",
            timestamp=time.time(),
        )
        with pytest.raises(AttributeError):
            event.user_id = "user_2"  # type: ignore

    def test_metric_value_frozen(self):
        """MetricValue 不可变"""
        metric = MetricValue("test", MetricType.COUNT, 10.0)
        with pytest.raises(AttributeError):
            metric.value = 20.0  # type: ignore

    def test_funnel_step_frozen(self):
        """FunnelStep 不可变"""
        step = FunnelStep("test", EventType.DIVINATION, 10)
        with pytest.raises(AttributeError):
            step.count = 20  # type: ignore

    def test_event_type_enum(self):
        """事件类型枚举"""
        assert EventType.DIVINATION.value == "起卦"
        assert EventType.PAGE_VIEW.value == "页面访问"
