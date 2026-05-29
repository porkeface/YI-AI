"""Agent编排器

管理Agent工作流的执行，支持：
- 单次执行
- 流式执行（SSE）
- 并行子任务
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import AsyncIterator
from dataclasses import dataclass

from ai.agent.state import AgentState, AgentConfig
from ai.agent.workflow import AgentWorkflow

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AgentResponse:
    """Agent响应"""
    response: str
    intent: str
    confidence: float
    risk_flags: list[str]
    inference_result: dict | None
    metadata: dict
    duration_ms: float


@dataclass(frozen=True)
class StreamEvent:
    """流式事件"""
    event_type: str  # "status" | "content" | "tool_call" | "done" | "error"
    data: str
    metadata: dict | None = None


class AgentOrchestrator:
    """Agent编排器

    高层接口，管理Agent工作流的完整生命周期。
    """

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()
        self.workflow = AgentWorkflow.build_default(self.config)

    async def run(
        self,
        user_query: str,
        hexagram_data: dict | None = None,
        user_id: str = "",
        session_id: str = "",
    ) -> AgentResponse:
        """执行Agent工作流

        Args:
            user_query: 用户问题
            hexagram_data: 卦象数据（可选）
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            Agent响应
        """
        start = time.monotonic()

        initial_state: AgentState = {
            "user_query": user_query,
            "hexagram_data": hexagram_data,
            "user_id": user_id,
            "session_id": session_id,
            "errors": [],
            "retry_count": 0,
        }

        try:
            final_state = await self.workflow.execute(initial_state)
            elapsed = (time.monotonic() - start) * 1000

            return AgentResponse(
                response=final_state.get("final_response", ""),
                intent=final_state.get("intent", "divination"),
                confidence=final_state.get("confidence", 0.0),
                risk_flags=final_state.get("risk_flags", []),
                inference_result=final_state.get("inference_result"),
                metadata=final_state.get("response_metadata", {}),
                duration_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            logger.error(f"agent_workflow_failed: {e}")
            return AgentResponse(
                response=f"处理过程中出现错误：{str(e)}",
                intent="error",
                confidence=0.0,
                risk_flags=[],
                inference_result=None,
                metadata={"error": str(e)},
                duration_ms=elapsed,
            )

    async def run_stream(
        self,
        user_query: str,
        hexagram_data: dict | None = None,
        user_id: str = "",
        session_id: str = "",
    ) -> AsyncIterator[StreamEvent]:
        """流式执行Agent工作流

        Yields:
            流式事件
        """
        yield StreamEvent(event_type="status", data="正在分析问题...")

        initial_state: AgentState = {
            "user_query": user_query,
            "hexagram_data": hexagram_data,
            "user_id": user_id,
            "session_id": session_id,
            "errors": [],
            "retry_count": 0,
        }

        # 执行意图分类
        from ai.agent.workflow import _classify_intent
        intent_result = _classify_intent(initial_state)
        initial_state.update(intent_result)

        yield StreamEvent(
            event_type="status",
            data=f"意图识别：{initial_state['intent']}（置信度{initial_state['confidence']:.0%}）",
            metadata={"intent": initial_state["intent"]},
        )

        # 执行规则分析
        yield StreamEvent(event_type="status", data="正在执行规则分析...")
        from ai.agent.workflow import _rule_analyze
        rule_result = _rule_analyze(initial_state)
        initial_state.update(rule_result)

        # 如果是推演意图，执行推演
        if initial_state.get("intent") == "evolution" and self.config.enable_evolution:
            yield StreamEvent(event_type="status", data="正在执行推演模拟...")
            from ai.agent.workflow import _evolution_simulate
            evo_result = _evolution_simulate(initial_state)
            initial_state.update(evo_result)

            if initial_state.get("inference_result"):
                yield StreamEvent(
                    event_type="tool_call",
                    data="推演完成",
                    metadata={"inference": initial_state["inference_result"]},
                )

        # AI解释（这里返回占位，实际需要LLM调用）
        yield StreamEvent(event_type="status", data="正在生成解释...")

        # 安全检查
        from ai.agent.workflow import _safety_check
        safety_result = _safety_check(initial_state)
        initial_state.update(safety_result)

        yield StreamEvent(
            event_type="content",
            data=initial_state.get("final_response", ""),
        )

        yield StreamEvent(
            event_type="done",
            data="完成",
            metadata={
                "intent": initial_state.get("intent"),
                "risk_flags": initial_state.get("risk_flags", []),
                "inference_result": initial_state.get("inference_result"),
            },
        )
