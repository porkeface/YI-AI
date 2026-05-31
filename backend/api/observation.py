"""观察报告API

连接 ai.observation.agent.ObservationAgent，
提供模式检测、趋势报告、异常检测接口。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ai.observation.agent import ObservationAgent
from ai.observation.types import ReportPeriod
from ai.memory.engine import MemoryEngine
from api.security import get_current_user
from db.models import User

logger = logging.getLogger(__name__)

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

    从 MemoryEngine 召回用户记忆，运行模式检测。
    """
    try:
        recall_result = MemoryEngine.recall(user_id, query="", limit=50)
        memories = recall_result.memories
    except Exception:
        logger.debug("memory_recall_failed", user_id=user_id, exc_info=True)
        memories = ()

    if not memories:
        return {
            "user_id": user_id,
            "patterns": [],
            "message": "暂无足够历史数据进行模式检测",
        }

    patterns = ObservationAgent.detect_patterns(memories)
    return {
        "user_id": user_id,
        "patterns": [
            {
                "category": p.category.value,
                "description": p.description,
                "confidence": p.confidence,
                "frequency": p.frequency,
            }
            for p in patterns
        ],
    }


@router.post("/anomaly")
async def check_anomaly(request: AnomalyCheckRequest):
    """检查异常

    从 MemoryEngine 召回用户记忆，运行异常检测。
    也可直接传入 recent_records 进行即时检测。
    """
    from ai.memory.types import UserMemory, MemoryType
    import time
    import uuid

    memories: list[UserMemory] = []

    # 优先使用请求中传入的记录
    if request.recent_records:
        for record in request.recent_records:
            memories.append(UserMemory(
                memory_id=str(uuid.uuid4()),
                user_id=request.user_id,
                memory_type=MemoryType.EPISODIC,
                content=record.get("content", ""),
                hexagram_name=record.get("hexagram_name"),
                importance=record.get("importance", 0.5),
                access_count=0,
                last_accessed=time.time(),
                created_at=record.get("created_at", time.time()),
                decay_factor=1.0,
            ))

    # 从 MemoryEngine 补充历史记忆
    if not memories:
        try:
            recall_result = MemoryEngine.recall(request.user_id, query="", limit=50)
            memories = list(recall_result.memories)
        except Exception:
            logger.debug("memory_recall_failed", user_id=request.user_id, exc_info=True)

    if not memories:
        return {
            "user_id": request.user_id,
            "anomalies": [],
            "message": "暂无足够历史数据进行异常检测",
        }

    anomalies = ObservationAgent.check_anomalies(memories)
    return {
        "user_id": request.user_id,
        "anomalies": [
            {
                "severity": a.severity.value,
                "anomaly_type": a.anomaly_type,
                "description": a.description,
                "recommendation": a.recommendation,
            }
            for a in anomalies
        ],
    }


@router.post("/trend")
async def generate_trend_report(request: TrendReportRequest):
    """生成趋势报告

    从 MemoryEngine 召回用户记忆，生成趋势报告。
    """
    period = _PERIOD_MAP.get(request.period)
    if period is None:
        raise HTTPException(
            status_code=400,
            detail=f"无效的报告周期: {request.period}，可选值: {list(_PERIOD_MAP.keys())}",
        )

    try:
        recall_result = MemoryEngine.recall(request.user_id, query="", limit=100)
        memories = recall_result.memories
    except Exception:
        logger.debug("memory_recall_failed", user_id=request.user_id, exc_info=True)
        memories = ()

    if not memories:
        return {
            "user_id": request.user_id,
            "period": request.period,
            "report": None,
            "message": "暂无足够历史数据生成趋势报告",
        }

    report = ObservationAgent.get_trend_report(request.user_id, memories, period)
    return {
        "user_id": request.user_id,
        "period": request.period,
        "report": {
            "total_sessions": report.total_sessions,
            "dominant_hexagrams": report.dominant_hexagrams,
            "dominant_topics": report.dominant_topics,
            "indicators": [
                {
                    "metric": ind.metric,
                    "current_value": ind.current_value,
                    "previous_value": ind.previous_value,
                    "change_rate": ind.change_rate,
                    "direction": ind.direction.value,
                }
                for ind in report.indicators
            ],
            "summary": report.summary,
        },
    }


@router.post("/observe")
async def full_observe(current_user: User = Depends(get_current_user)):
    """执行完整观察分析（模式+趋势+异常）

    从 MemoryEngine 召回用户记忆，执行完整的观察分析。
    """
    try:
        recall_result = MemoryEngine.recall(current_user.id, query="", limit=100)
        memories = recall_result.memories
    except Exception:
        logger.debug("memory_recall_failed", user_id=current_user.id, exc_info=True)
        memories = ()

    if not memories:
        return {
            "user_id": current_user.id,
            "observation": None,
            "message": "暂无足够历史数据进行完整观察分析",
        }

    observation = ObservationAgent.observe(current_user.id, memories)
    return {
        "user_id": current_user.id,
        "observation": {
            "patterns": [
                {
                    "category": p.category.value,
                    "description": p.description,
                    "confidence": p.confidence,
                }
                for p in observation.patterns
            ],
            "trends": [
                {
                    "metric": t.metric,
                    "direction": t.direction.value,
                    "change_rate": t.change_rate,
                }
                for t in observation.trends
            ],
            "anomalies": [
                {
                    "severity": a.severity.value,
                    "description": a.description,
                    "recommendation": a.recommendation,
                }
                for a in observation.anomalies
            ],
            "summary": observation.summary,
        },
    }


@router.get("/health")
async def observation_health():
    """观察模块健康检查"""
    return {"status": "ok", "module": "observation"}
