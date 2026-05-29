"""Agent工作流引擎

LangGraph风格的状态图工作流引擎。
实现：意图分类 → 记忆召回 → 规则分析 → RAG检索 → AI解释 → 安全检查 → 记忆存储 → 输出
"""
from __future__ import annotations

import asyncio
import logging
from typing import Callable, Any

from ai.agent.state import AgentState, AgentConfig
from ai.agent.tools import AgentTools, ToolResult
from ai.memory.engine import MemoryEngine
from ai.memory.types import MemoryType

logger = logging.getLogger(__name__)


class WorkflowNode:
    """工作流节点基类"""

    def __init__(self, name: str, handler: Callable[[AgentState], dict]):
        self.name = name
        self._handler = handler

    async def execute(self, state: AgentState) -> dict:
        """执行节点"""
        import time
        start = time.monotonic()
        try:
            result = await self._handler(state) if asyncio.iscoroutinefunction(self._handler) else self._handler(state)
            elapsed = (time.monotonic() - start) * 1000
            logger.info(f"node_executed: {self.name} ({elapsed:.0f}ms)")
            return result
        except Exception as e:
            logger.error(f"node_failed: {self.name} - {e}")
            return {"errors": state.get("errors", []) + [f"{self.name}: {str(e)}"]}


class ConditionalEdge:
    """条件边"""

    def __init__(self, condition: Callable[[AgentState], str], routes: dict[str, str]):
        self.condition = condition
        self.routes = routes

    def resolve(self, state: AgentState) -> str:
        """解析路由"""
        decision = self.condition(state)
        return self.routes.get(decision, "end")


class AgentWorkflow:
    """Agent工作流引擎

    LangGraph风格的有向图工作流。
    支持：顺序执行、条件路由、并行节点、错误处理。
    """

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()
        self._nodes: dict[str, WorkflowNode] = {}
        self._edges: dict[str, str | ConditionalEdge] = {}
        self._entry_point: str = "start"
        self._tools = AgentTools()

    def add_node(self, name: str, handler: Callable[[AgentState], dict]) -> None:
        """添加节点"""
        self._nodes[name] = WorkflowNode(name, handler)

    def add_edge(self, from_node: str, to_node: str) -> None:
        """添加普通边"""
        self._edges[from_node] = to_node

    def add_conditional_edge(
        self,
        from_node: str,
        condition: Callable[[AgentState], str],
        routes: dict[str, str],
    ) -> None:
        """添加条件边"""
        self._edges[from_node] = ConditionalEdge(condition, routes)

    def set_entry_point(self, node_name: str) -> None:
        """设置入口节点"""
        self._entry_point = node_name

    async def execute(self, initial_state: AgentState) -> AgentState:
        """执行工作流

        Args:
            initial_state: 初始状态

        Returns:
            最终状态
        """
        state = dict(initial_state)
        state.setdefault("errors", [])
        state.setdefault("retry_count", 0)
        state.setdefault("current_step", self._entry_point)

        current_node = self._entry_point
        max_steps = 20  # 防止无限循环
        step_count = 0

        while current_node and current_node != "end" and step_count < max_steps:
            step_count += 1

            if current_node not in self._nodes:
                logger.error(f"unknown_node: {current_node}")
                state["errors"].append(f"Unknown node: {current_node}")
                break

            node = self._nodes[current_node]
            state["current_step"] = current_node

            # 执行节点
            updates = await node.execute(state)
            state.update(updates)

            # 解析下一条边
            edge = self._edges.get(current_node)
            if edge is None:
                break
            elif isinstance(edge, ConditionalEdge):
                current_node = edge.resolve(state)
            else:
                current_node = edge

        if step_count >= max_steps:
            state["errors"].append("Workflow exceeded maximum steps")

        return state

    @staticmethod
    def build_default(config: AgentConfig | None = None) -> AgentWorkflow:
        """构建默认的Agent工作流

        流程：
        start → classify_intent → [retrieve_memory] → rule_analyze → rag_retrieve
        → interpret → [evolution_simulate] → safety_check → [store_memory] → end

        条件分支：
        - 如果意图是evolution，插入evolution_simulate节点
        - 如果 enable_memory，插入记忆召回/存储节点
        """
        workflow = AgentWorkflow(config)
        cfg = config or AgentConfig()

        # 添加节点
        workflow.add_node("classify_intent", _classify_intent)
        workflow.add_node("rule_analyze", _rule_analyze)
        workflow.add_node("rag_retrieve", _rag_retrieve)
        workflow.add_node("interpret", _interpret)
        workflow.add_node("evolution_simulate", _evolution_simulate)
        workflow.add_node("safety_check", _safety_check)

        # [H3] 根据 enable_memory 配置决定是否添加记忆节点
        if cfg.enable_memory:
            workflow.add_node("retrieve_memory", _retrieve_memory)
            workflow.add_node("store_memory", _store_memory)

        # 设置入口
        workflow.set_entry_point("classify_intent")

        # 添加边
        if cfg.enable_memory:
            workflow.add_edge("classify_intent", "retrieve_memory")
            workflow.add_edge("retrieve_memory", "rule_analyze")
        else:
            workflow.add_edge("classify_intent", "rule_analyze")

        workflow.add_edge("rule_analyze", "rag_retrieve")
        workflow.add_edge("rag_retrieve", "interpret")

        # 条件边：如果需要推演
        workflow.add_conditional_edge(
            "interpret",
            lambda s: "evolution" if s.get("intent") == "evolution" and cfg.enable_evolution else "direct",
            {
                "evolution": "evolution_simulate",
                "direct": "safety_check",
            },
        )

        workflow.add_edge("evolution_simulate", "safety_check")

        if cfg.enable_memory:
            workflow.add_edge("safety_check", "store_memory")
            workflow.add_edge("store_memory", "end")
        else:
            workflow.add_edge("safety_check", "end")

        return workflow


# ============================================================================
# 默认节点实现
# ============================================================================

# [H6] 卦名列表按长度降序，避免子串误匹配
_HEXAGRAM_NAMES_SORTED = sorted(
    [
        "乾", "坤", "屯", "蒙", "需", "讼", "师", "比",
        "小畜", "履", "泰", "否", "同人", "大有", "谦", "豫",
        "随", "蛊", "临", "观", "噬嗑", "贲", "剥", "复",
        "无妄", "大畜", "颐", "大过", "坎", "离", "咸", "恒",
        "遁", "大壮", "晋", "明夷", "家人", "睽", "蹇", "解",
        "损", "益", "夬", "姤", "萃", "升", "困", "井",
        "革", "鼎", "震", "艮", "渐", "归妹", "丰", "旅",
        "巽", "兑", "涣", "节", "中孚", "小过", "既济", "未济",
    ],
    key=len,
    reverse=True,
)


def _classify_intent(state: AgentState) -> dict:
    """意图分类节点

    分析用户问题，判断意图类型。
    使用关键词匹配（Tier 1级别），不调用LLM。
    """
    query = state.get("user_query", "")

    # 关键词匹配意图分类
    evolution_keywords = ["推演", "变化", "趋势", "未来", "演化", "发展"]
    trend_keywords = ["分析", "长期", "周期", "规律", "模式"]
    learn_keywords = ["什么是", "怎么理解", "解释", "学习", "含义"]

    intent = "divination"  # 默认
    confidence = 0.6

    for kw in evolution_keywords:
        if kw in query:
            intent = "evolution"
            confidence = 0.8
            break

    if intent == "divination":
        for kw in trend_keywords:
            if kw in query:
                intent = "trend"
                confidence = 0.7
                break

    if intent == "divination":
        for kw in learn_keywords:
            if kw in query:
                intent = "learn"
                confidence = 0.7
                break

    # [H6] 最长匹配优先，避免子串误匹配
    entities: dict = {}
    for name in _HEXAGRAM_NAMES_SORTED:
        if name in query:
            entities["hexagram_name"] = name
            break

    return {
        "intent": intent,
        "confidence": confidence,
        "entities": entities,
    }


def _rule_analyze(state: AgentState) -> dict:
    """规则分析节点

    调用规则引擎进行确定性分析。
    """
    hexagram_data = state.get("hexagram_data")
    if not hexagram_data:
        return {"rule_analysis": None}

    # 规则分析结果已经在hexagram_data中（由前端传入或API预计算）
    return {"rule_analysis": hexagram_data.get("analysis")}


def _rag_retrieve(state: AgentState) -> dict:
    """RAG检索节点

    检索相关知识上下文。
    """
    # RAG检索需要外部依赖（Qdrant/Neo4j），这里返回占位
    # 实际实现在集成阶段完成
    return {"rag_context": None}


def _interpret(state: AgentState) -> dict:
    """AI解释节点

    生成AI解释。实际调用LLM。
    """
    # 这个节点在实际运行时会被注入LLM调用逻辑
    # 这里返回占位
    return {
        "interpretation_draft": "",
        "current_step": "interpret_complete",
    }


def _evolution_simulate(state: AgentState) -> dict:
    """推演模拟节点

    执行卦象推演。
    """
    hexagram_data = state.get("hexagram_data")
    if not hexagram_data:
        return {"inference_result": None}

    hexagram_name = hexagram_data.get("name", "")
    if not hexagram_name:
        return {"inference_result": None}

    try:
        result = AgentTools.simulate_evolution_chain(hexagram_name, steps=3)
        if result.success:
            return {"inference_result": result.data}
        return {"inference_result": None}
    except Exception as e:
        logger.error(f"evolution_simulate failed: {e}")
        return {"inference_result": None}


def _safety_check(state: AgentState) -> dict:
    """安全检查节点

    检查输出是否包含不安全内容。
    [M10 修复] 只在发现禁止词时修改 final_response，否则保留原值。
    """
    response = state.get("interpretation_draft", "")

    forbidden = ["一定会", "必然", "保证", "绝对", "百分之百"]
    risk_flags = []

    for phrase in forbidden:
        if phrase in response:
            risk_flags.append(f"禁止性承诺: {phrase}")

    if risk_flags:
        # 替换不安全内容
        safe_response = response
        for phrase in forbidden:
            safe_response = safe_response.replace(phrase, "可能会")
        return {
            "risk_flags": risk_flags,
            "final_response": safe_response,
        }

    # [M10] 无风险时保留原始 response
    return {
        "risk_flags": [],
        "final_response": response,
    }


def _retrieve_memory(state: AgentState) -> dict:
    """记忆召回节点

    从长期记忆中召回与当前查询相关的内容。
    在意图分类之后、规则分析之前执行。
    """
    user_id = state.get("user_id", "")
    query = state.get("user_query", "")
    session_id = state.get("session_id", "")

    if not user_id or not query:
        return {"user_memory": None}

    try:
        recall_result = MemoryEngine.recall(
            user_id=user_id,
            query=query,
            session_id=session_id if session_id else None,
            limit=8,
        )

        if recall_result.total_count == 0:
            return {"user_memory": None}

        return {
            "user_memory": {
                "context_text": recall_result.context_text,
                "memory_count": recall_result.total_count,
                "memories": [
                    {
                        "type": m.memory_type.value,
                        "content": m.content,
                        "hexagram": m.hexagram_name,
                        "importance": m.importance,
                    }
                    for m in recall_result.memories
                ],
            },
        }
    except Exception as e:
        logger.error(f"记忆召回失败: {e}")
        return {"user_memory": None}


def _store_memory(state: AgentState) -> dict:
    """记忆存储节点

    将本次交互的结果存入长期记忆。
    在安全检查之后、结束之前执行。
    """
    user_id = state.get("user_id", "")
    if not user_id:
        return {}

    query = state.get("user_query", "")
    response = state.get("final_response", "")
    hexagram_data = state.get("hexagram_data")
    hexagram_name = hexagram_data.get("name") if hexagram_data else None
    session_id = state.get("session_id", "")

    # 只在有实质内容时存储
    if not query and not response:
        return {}

    try:
        # 构建记忆内容
        content = query
        if response:
            # [L6] 安全截断：在标点处截断而非硬切
            truncated = _safe_truncate(response, 100)
            content = f"问题: {query} | 回答摘要: {truncated}"

        # 根据风险标记调整重要度
        risk_flags = state.get("risk_flags", [])
        importance = 0.7 if risk_flags else 0.5

        MemoryEngine.store(
            user_id=user_id,
            content=content,
            hexagram_name=hexagram_name,
            importance=importance,
            session_id=session_id if session_id else None,
        )
    except Exception as e:
        logger.error(f"记忆存储失败: {e}")

    return {}


def _safe_truncate(text: str, max_len: int) -> str:
    """安全截断文本

    优先在标点处截断，避免截断中文词组。

    Args:
        text: 原始文本
        max_len: 最大长度

    Returns:
        截断后的文本
    """
    if len(text) <= max_len:
        return text
    # 在 max_len 范围内找最后一个标点
    punctuation = "。！？，；：、"
    best_pos = -1
    for i in range(min(max_len, len(text)) - 1, max_len // 2, -1):
        if text[i] in punctuation:
            best_pos = i + 1
            break
    if best_pos > 0:
        return text[:best_pos]
    return text[:max_len]
