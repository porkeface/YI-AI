"""分析数据API

连接 ai.analytics.tracker.EventTracker，
提供事件追踪、仪表盘、漏斗分析接口。
"""

from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ai.analytics.tracker import EventTracker
from ai.analytics.types import EventType

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# 事件类型字符串 -> 枚举映射
_EVENT_MAP = {
    "page_view": EventType.PAGE_VIEW,
    "divination": EventType.DIVINATION,
    "interpretation": EventType.INTERPRETATION,
    "history_view": EventType.HISTORY_VIEW,
    "hexagram_atlas": EventType.HEXAGRAM_ATLAS,
    "plugin_use": EventType.PLUGIN_USE,
    "api_call": EventType.API_CALL,
    "user_register": EventType.USER_REGISTER,
    "user_login": EventType.USER_LOGIN,
}


class TrackEventRequest(BaseModel):
    """事件追踪请求"""
    event_type: str = Field(..., description="事件类型")
    user_id: str = Field(..., description="用户ID")
    properties: dict[str, str] = Field(default_factory=dict, description="事件属性")


class FunnelRequest(BaseModel):
    """漏斗分析请求"""
    funnel_name: str = Field(..., description="漏斗名称")
    steps: list[dict[str, str]] = Field(
        ...,
        description='漏斗步骤列表，每项包含 step_name 和 event_type，如 [{"step_name": "访问", "event_type": "page_view"}]',
    )
    days: int = Field(7, description="分析时间窗口（天）")


@router.post("/events")
async def track_event(request: TrackEventRequest):
    """追踪事件"""
    event_type = _EVENT_MAP.get(request.event_type)
    if event_type is None:
        raise HTTPException(
            status_code=400,
            detail=f"无效的事件类型: {request.event_type}，可选值: {list(_EVENT_MAP.keys())}",
        )

    event = EventTracker.track(
        event_type=event_type,
        user_id=request.user_id,
        properties=request.properties,
    )

    return {
        "status": "tracked",
        "event_id": event.event_id,
        "event_type": event.event_type.value,
    }


@router.get("/events")
async def list_events(
    event_type: str | None = None,
    user_id: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
):
    """查询事件列表"""
    etype = None
    if event_type:
        etype = _EVENT_MAP.get(event_type)
        if etype is None:
            raise HTTPException(
                status_code=400,
                detail=f"无效的事件类型: {event_type}，可选值: {list(_EVENT_MAP.keys())}",
            )

    events = EventTracker.query(
        event_type=etype,
        user_id=user_id,
        limit=limit,
    )

    return {
        "events": [
            {
                "event_id": e.event_id,
                "event_type": e.event_type.value,
                "user_id": e.user_id,
                "timestamp": e.timestamp,
                "properties": dict(e.properties),
            }
            for e in events
        ],
        "total": len(events),
    }


@router.get("/event-types")
async def list_event_types():
    """列出所有支持的事件类型"""
    return {
        "event_types": [
            {"key": key, "label": etype.value}
            for key, etype in _EVENT_MAP.items()
        ]
    }


@router.get("/dashboard")
async def get_dashboard(days: int = Query(7, ge=1, le=90)):
    """获取仪表盘数据"""
    since = time.time() - days * 86400
    dashboard = EventTracker.build_dashboard(since=since)

    return {
        "dashboard": {
            "total_users": dashboard.total_users,
            "active_users": dashboard.active_users,
            "total_sessions": dashboard.total_sessions,
            "avg_session_duration": dashboard.avg_session_duration,
            "top_hexagrams": [
                {"name": name, "count": count}
                for name, count in dashboard.top_hexagrams
            ],
            "top_topics": [
                {"name": name, "count": count}
                for name, count in dashboard.top_topics
            ],
            "metrics": [
                {
                    "name": m.metric_name,
                    "type": m.metric_type.value,
                    "value": m.value,
                }
                for m in dashboard.metrics
            ],
        }
    }


@router.post("/funnel")
async def get_funnel(request: FunnelRequest):
    """获取漏斗分析"""
    # 解析步骤
    steps = []
    for step in request.steps:
        step_name = step.get("step_name")
        event_type_str = step.get("event_type")
        if not step_name or not event_type_str:
            raise HTTPException(
                status_code=400,
                detail="每个步骤必须包含 step_name 和 event_type",
            )
        etype = _EVENT_MAP.get(event_type_str)
        if etype is None:
            raise HTTPException(
                status_code=400,
                detail=f"无效的事件类型: {event_type_str}，可选值: {list(_EVENT_MAP.keys())}",
            )
        steps.append((step_name, etype))

    since = time.time() - request.days * 86400
    report = EventTracker.build_funnel(
        funnel_name=request.funnel_name,
        steps=tuple(steps),
        since=since,
    )

    return {
        "funnel": {
            "funnel_name": report.funnel_name,
            "steps": [
                {
                    "step_name": s.step_name,
                    "event_type": s.event_type.value,
                    "count": s.count,
                    "conversion_rate": s.conversion_rate,
                }
                for s in report.steps
            ],
            "overall_conversion": report.overall_conversion,
            "period_start": report.period_start,
            "period_end": report.period_end,
        }
    }


@router.get("/stats")
async def get_stats(
    event_type: str | None = None,
    days: int = Query(7, ge=1, le=90),
):
    """获取事件统计"""
    etype = None
    if event_type:
        etype = _EVENT_MAP.get(event_type)
        if etype is None:
            raise HTTPException(
                status_code=400,
                detail=f"无效的事件类型: {event_type}，可选值: {list(_EVENT_MAP.keys())}",
            )

    since = time.time() - days * 86400
    total = EventTracker.count_events(event_type=etype, since=since)
    unique_users = EventTracker.get_unique_users(since=since)

    return {
        "total_events": total,
        "unique_users": unique_users,
        "days": days,
    }


@router.get("/health")
async def analytics_health():
    """分析模块健康检查"""
    return {"status": "ok", "module": "analytics", "total_events": EventTracker.total_events()}
