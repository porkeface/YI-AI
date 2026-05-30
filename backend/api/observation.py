"""观察报告API

连接 ai.observation.agent.ObservationAgent，
提供模式检测、趋势报告、异常检测接口。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ai.observation.agent import ObservationAgent
from ai.observation.types import ReportPeriod
from api.security import get_current_user
from db.models import User

router = APIRouter(prefix="/api/observation", tags=["observation"])

# 周期字符串 -> 枚举映射
_PERIOD_MAP = {
    "daily": ReportPeriod.DAILY,
    "weekly": ReportPeriod.WEEKLY,
    "monthly": ReportPeriod.MONTHLY,
    "quarterly": ReportPeriod.QUARTERLY,
}


class TrendReportRequest(BaseModel):
    """趋势报告请求"""
    user_id: str
    period: str = Field("weekly", description="报告周期: daily / weekly / monthly / quarterly")


class AnomalyCheckRequest(BaseModel):
    """异常检测请求"""
    user_id: str
    recent_records: list[dict] = Field(default_factory=list, description="最近记录")


@router.get("/patterns/{user_id}")
async def get_patterns(user_id: str):
    """获取用户的行为模式

    MVP阶段：需要用户历史记忆数据才能检测模式。
    后续接入 MemoryEngine 后自动获取。
    """
    # TODO: 从 MemoryEngine 获取用户记忆
    # memories = memory_engine.get_memories(user_id)
    # patterns = ObservationAgent.detect_patterns(memories)
    return {
        "user_id": user_id,
        "patterns": [],
        "message": "模式检测需要用户历史数据，等待 MemoryEngine 接入",
    }


@router.post("/anomaly")
async def check_anomaly(request: AnomalyCheckRequest):
    """检查异常

    MVP阶段：返回提示信息，后续接入记忆数据后启用。
    """
    # TODO: 从 MemoryEngine 获取用户记忆
    # memories = memory_engine.get_memories(request.user_id)
    # anomalies = ObservationAgent.check_anomalies(memories)
    return {
        "user_id": request.user_id,
        "anomalies": [],
        "message": "异常检测需要用户历史数据，等待 MemoryEngine 接入",
    }


@router.post("/trend")
async def generate_trend_report(request: TrendReportRequest):
    """生成趋势报告

    MVP阶段：返回提示信息，后续接入记忆数据后启用。
    """
    period = _PERIOD_MAP.get(request.period)
    if period is None:
        raise HTTPException(
            status_code=400,
            detail=f"无效的报告周期: {request.period}，可选值: {list(_PERIOD_MAP.keys())}",
        )

    # TODO: 从 MemoryEngine 获取用户记忆
    # memories = memory_engine.get_memories(request.user_id)
    # report = ObservationAgent.get_trend_report(request.user_id, memories, period)
    return {
        "user_id": request.user_id,
        "period": request.period,
        "report": None,
        "message": "趋势报告需要用户历史数据，等待 MemoryEngine 接入",
    }


@router.post("/observe")
async def full_observe(current_user: User = Depends(get_current_user)):
    """执行完整观察分析（模式+趋势+异常）

    MVP阶段：返回提示信息，后续接入记忆数据后启用。
    """
    # TODO: 从 MemoryEngine 获取用户记忆
    # memories = memory_engine.get_memories(current_user.id)
    # observation = ObservationAgent.observe(current_user.id, memories)
    return {
        "user_id": current_user.id,
        "observation": None,
        "message": "完整观察需要用户历史数据，等待 MemoryEngine 接入",
    }


@router.get("/health")
async def observation_health():
    """观察模块健康检查"""
    return {"status": "ok", "module": "observation"}
