"""Agent对话API

提供Agent工作流的HTTP接口，支持：
- 普通请求/响应
- SSE流式输出
- 推演查询
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from typing import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["Agent"])


# ============================================================================
# 请求/响应模型
# ============================================================================


class AgentChatRequest(BaseModel):
    """Agent对话请求"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")
    hexagram_data: dict | None = Field(None, description="卦象数据（可选）")
    session_id: str = Field(default="", description="会话ID")


class AgentChatResponse(BaseModel):
    """Agent对话响应"""
    response: str = Field(..., description="Agent回复")
    intent: str = Field(..., description="识别的意图")
    confidence: float = Field(..., description="意图置信度")
    risk_flags: list[str] = Field(default_factory=list, description="风险标记")
    inference_result: dict | None = Field(None, description="推演结果")
    duration_ms: float = Field(..., description="处理耗时(ms)")


class EvolutionRequest(BaseModel):
    """推演请求"""
    hexagram_name: str = Field(..., description="卦名")
    max_depth: int = Field(default=5, ge=1, le=10, description="推演深度")
    branch_factor: int = Field(default=3, ge=1, le=5, description="分支因子")


class ObserverReportRequest(BaseModel):
    """观察报告请求"""
    period_days: int = Field(default=30, ge=7, le=365, description="分析周期天数")


# ============================================================================
# API端点
# ============================================================================


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    req: AgentChatRequest,
    user=Depends(get_current_user),
):
    """Agent对话（非流式）

    接收用户消息，通过Agent工作流处理，返回完整回复。
    """
    from ai.agent.orchestrator import AgentOrchestrator
    from ai.agent.state import AgentConfig

    config = AgentConfig(
        enable_evolution=True,
        safety_check=True,
    )
    orchestrator = AgentOrchestrator(config)

    result = await orchestrator.run(
        user_query=req.message,
        hexagram_data=req.hexagram_data,
        user_id=str(user.id) if user else "",
        session_id=req.session_id,
    )

    return AgentChatResponse(
        response=result.response,
        intent=result.intent,
        confidence=result.confidence,
        risk_flags=result.risk_flags,
        inference_result=result.inference_result,
        duration_ms=result.duration_ms,
    )


@router.post("/chat/stream")
async def agent_chat_stream(
    req: AgentChatRequest,
    user=Depends(get_current_user),
):
    """Agent对话（SSE流式）

    通过Server-Sent Events逐步返回Agent处理结果。
    """
    from ai.agent.orchestrator import AgentOrchestrator
    from ai.agent.state import AgentConfig

    config = AgentConfig(
        enable_evolution=True,
        safety_check=True,
    )
    orchestrator = AgentOrchestrator(config)

    async def event_generator() -> AsyncIterator[str]:
        async for event in orchestrator.run_stream(
            user_query=req.message,
            hexagram_data=req.hexagram_data,
            user_id=str(user.id) if user else "",
            session_id=req.session_id,
        ):
            data = {
                "type": event.event_type,
                "data": event.data,
            }
            if event.metadata:
                data["metadata"] = event.metadata
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/evolve")
async def evolve(
    req: EvolutionRequest,
    user=Depends(get_current_user),
):
    """执行深度推演

    对指定卦象进行多步推演，生成概率树。
    """
    from foundation.hexagram_engine import HexagramEngine
    from rule_engine.evolution_engine import EvolutionEngine

    try:
        hexagram = HexagramEngine.get_by_name(req.hexagram_name)
    except (ValueError, IndexError):
        return {"error": f"未找到卦象: {req.hexagram_name}"}

    result = EvolutionEngine.evolve(
        hexagram,
        max_depth=req.max_depth,
        branch_factor=req.branch_factor,
    )

    # 序列化为JSON
    tree_data = _serialize_node(result.tree.root)

    return {
        "source": result.source_hexagram,
        "tree": tree_data,
        "total_nodes": result.tree.total_nodes,
        "path_count": len(result.tree.paths),
        "recommended_path": list(result.recommended_path),
        "summary": result.summary,
    }


@router.get("/health")
async def agent_health():
    """Agent系统健康检查"""
    return {
        "status": "ok",
        "components": {
            "workflow": "ready",
            "evolution": "ready",
            "observer": "ready",
            "multi_model": "ready",
        },
    }


# ============================================================================
# 辅助函数
# ============================================================================


def _serialize_node(node) -> dict:
    """递归序列化演化树节点"""
    return {
        "name": node.hexagram_name,
        "depth": node.depth,
        "probability": node.probability,
        "trigger": node.transition_trigger,
        "relation": node.relation,
        "trend": node.trend,
        "element_strength": node.element_strength,
        "children": [_serialize_node(c) for c in node.children],
    }
