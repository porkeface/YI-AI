"""Agent工作流引擎

LangGraph风格的状态图工作流引擎。
实现：意图分类 → 记忆召回 → 规则分析 → RAG检索 → AI解释 → 安全检查 → 记忆存储 → 输出
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Callable, Any

from ai.agent.state import AgentState, AgentConfig
from ai.agent.tools import AgentTools, ToolResult
from ai.knowledge_base import KnowledgeBase
from ai.knowledge_graph import KnowledgeGraph
from ai.llm_client import LLMClient, LLMConfig, LLMError
from ai.memory.engine import MemoryEngine
from ai.memory.types import MemoryType
from ai.rag_fusion import RAGFusion
from foundation.hexagram_engine import HexagramEngine

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

# 模块级单例（延迟初始化）
_kb = KnowledgeBase()
_rag: RAGFusion | None = None


def _get_rag() -> RAGFusion:
    """获取 RAGFusion 单例（延迟初始化，尝试接入向量后端）"""
    global _rag
    if _rag is None:
        vector_backend = None
        embedding_service = None
        try:
            from ai.adapters.qdrant_adapter import QdrantVectorBackend
            from ai.embedding import get_embedding_service

            vb = QdrantVectorBackend()
            if vb.is_available():
                vector_backend = vb
                embedding_service = get_embedding_service()
                logger.info("qdrant_vector_backend_enabled")
        except Exception as e:
            logger.debug(f"Vector backend not available: {e}")

        _rag = RAGFusion(
            vector_backend=vector_backend,
            embedding_service=embedding_service,
        )
    return _rag


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
        return {"rule_analysis": None, "rule_analysis_result": None}

    # 规则分析结果已经在hexagram_data中（由前端传入或API预计算）
    rule_analysis_dict = hexagram_data.get("analysis")

    # Also perform real analysis to get a proper RuleAnalysisResult object
    # This is needed for evolution simulation which requires the typed object
    rule_analysis_result = None
    hexagram_name = hexagram_data.get("name", "")
    if hexagram_name:
        try:
            from rule_engine.analyzer import Analyzer
            month_branch = state.get("month_branch", "子")
            hexagram = HexagramEngine.get_by_name(hexagram_name)
            rule_analysis_result = Analyzer.analyze(hexagram, "通用", month_branch)
        except Exception as e:
            logger.warning(f"Real rule analysis failed, using dict only: {e}")

    return {
        "rule_analysis": rule_analysis_dict,
        "rule_analysis_result": rule_analysis_result,
    }


def _rag_retrieve(state: AgentState) -> dict:
    """RAG检索节点 - 使用公共API进行检索

    通过知识库检索和知识图谱获取上下文，
    不调用任何私有方法。
    """
    hexagram_data = state.get("hexagram_data")
    user_query = state.get("user_query", "")

    if not hexagram_data:
        return {"rag_context": None}

    hexagram_name = hexagram_data.get("name", "")
    if not hexagram_name:
        return {"rag_context": None}

    # 从用户查询推断问题类型
    question_type = "通用"
    for keyword, qtype in [
        ("事业", "事业"), ("工作", "事业"),
        ("感情", "感情"), ("恋爱", "感情"), ("婚姻", "婚姻"),
        ("财运", "财运"), ("钱", "财运"), ("投资", "财运"),
        ("健康", "健康"), ("身体", "健康"),
    ]:
        if keyword in user_query:
            question_type = qtype
            break

    try:
        rag = _get_rag()

        # 使用知识库公共检索（内部会自动选择向量或关键词）
        entries = rag.knowledge_base.retrieve(hexagram_name, question_type, max_entries=5)

        # 获取图谱上下文
        graph_context = rag.knowledge_graph.get_hexagram_context(hexagram_name)

        results = list(entries)
        if graph_context:
            results.insert(0, f"【卦象关系】{graph_context}")

        return {"rag_context": results if results else None}
    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        # 降级到纯关键词匹配
        try:
            entries = _kb.retrieve(hexagram_name, question_type, max_entries=5)
            return {"rag_context": entries if entries else None}
        except Exception as e2:
            logger.error(f"Fallback retrieval also failed: {e2}")
            return {"rag_context": None}


def _create_llm_client() -> LLMClient | None:
    """创建LLM客户端（从环境变量读取配置）"""
    api_key = os.environ.get("YI_AI_LLM_API_KEY") or os.environ.get("DEEPSEEK_API_KEY", "")
    base_url = os.environ.get("YI_AI_LLM_BASE_URL", "https://api.deepseek.com")
    model = os.environ.get("YI_AI_LLM_MODEL", "deepseek-chat")

    if not api_key:
        logger.warning("No LLM API key configured, _interpret will return fallback")
        return None

    return LLMClient(LLMConfig(
        provider="deepseek",
        api_key=api_key,
        base_url=base_url,
        model=model,
        max_tokens=2000,
        temperature=0.7,
    ))


_SYSTEM_PROMPT = (
    "你是一位精通易学的AI助手。你的任务是将六爻排盘的规则分析结果"
    "翻译成通俗易懂的现代汉语解释。\n\n"
    "核心原则：\n"
    "1. 你只负责\"解释\"规则结果，不负责\"计算\"\n"
    "2. 解释要通俗易懂，避免专业术语堆砌\n"
    "3. 要结合用户的具体问题来解释\n"
    "4. 要给出实用的建议\n"
    "5. 不要做绝对化的预测，用\"趋势\"、\"可能性\"等词语\n"
    "6. 要有温度，不要冷冰冰的\n\n"
    "输出格式：\n"
    "1. 首先用一句话概括卦象的核心含义\n"
    "2. 然后详细解释各爻的关系和含义\n"
    "3. 最后给出实用建议\n\n"
    "注意：不要使用\"算命\"、\"注定\"等词语，"
    "用\"趋势\"、\"分析\"、\"参考\"等中性词。"
)


async def _interpret(state: AgentState) -> dict:
    """AI解释节点 -- 调用LLM生成解释"""
    hexagram_data = state.get("hexagram_data")
    user_query = state.get("user_query", "")
    rag_context = state.get("rag_context")
    rule_analysis = state.get("rule_analysis")

    # 如果没有卦象数据，返回降级解释
    if not hexagram_data:
        return {
            "interpretation_draft": "抱歉，未能获取到卦象数据，无法生成解释。",
            "current_step": "interpret_complete",
        }

    # 尝试调用LLM
    llm_client = _create_llm_client()
    if not llm_client:
        return {
            "interpretation_draft": _generate_fallback_interpretation(hexagram_data, user_query),
            "current_step": "interpret_complete",
        }

    try:
        user_prompt = _build_interpret_prompt(user_query, hexagram_data, rule_analysis, rag_context)

        async with llm_client:
            response = await llm_client.chat(_SYSTEM_PROMPT, user_prompt)

        return {
            "interpretation_draft": response,
            "current_step": "interpret_complete",
        }
    except LLMError as e:
        logger.error(f"LLM call failed: {e}")
        return {
            "interpretation_draft": _generate_fallback_interpretation(hexagram_data, user_query),
            "current_step": "interpret_complete",
        }
    except Exception as e:
        logger.error(f"Unexpected error in _interpret: {e}")
        return {
            "interpretation_draft": _generate_fallback_interpretation(hexagram_data, user_query),
            "current_step": "interpret_complete",
        }


def _build_interpret_prompt(
    user_query: str,
    hexagram_data: dict,
    rule_analysis: dict | None,
    rag_context: list[str] | None,
) -> str:
    """构建解释提示词（简化版，不依赖 Hexagram 对象）"""
    parts: list[str] = [f"【用户问题】{user_query}"]

    # 卦象信息
    name = hexagram_data.get("name", "未知")
    judgment = hexagram_data.get("judgment", "")
    image = hexagram_data.get("image", "")
    parts.append(f"【卦象信息】\n- 卦名：{name}\n- 卦辞：{judgment}\n- 象辞：{image}")

    # 规则分析
    if rule_analysis:
        yong_shen = rule_analysis.get("yong_shen", "")
        prosperity = rule_analysis.get("prosperity", "")
        verdict = rule_analysis.get("verdict", {})
        parts.append(f"【规则分析】\n- 用神：{yong_shen}\n- 旺衰：{prosperity}")
        if verdict:
            parts.append(
                f"- 综合判断：{verdict.get('overall', '')}\n- 趋势：{verdict.get('trend', '')}"
            )

    # RAG上下文
    if rag_context:
        rag_text = "\n".join(f"  · {entry}" for entry in rag_context)
        parts.append(f"【易经原文参考】\n{rag_text}")

    parts.append("请根据以上信息，为用户生成一段通俗易懂的卦象解释。要结合用户的具体问题，给出实用的建议。")

    return "\n\n".join(parts)


def _generate_fallback_interpretation(hexagram_data: dict, user_query: str) -> str:
    """降级解释（无LLM时使用）"""
    name = hexagram_data.get("name", "此卦")
    judgment = hexagram_data.get("judgment", "")

    if judgment:
        return (
            f"【{name}】{judgment}\n\n"
            "根据卦象分析，建议您审时度势，顺应变化。"
            "具体的AI深度解释需要配置LLM服务。"
        )
    return (
        f"卦象【{name}】已获取。"
        "详细的AI解释需要配置LLM API密钥（设置环境变量 DEEPSEEK_API_KEY）。"
    )


def _evolution_simulate(state: AgentState) -> dict:
    """推演模拟节点

    执行卦象推演。使用真实的规则分析结果而非硬编码假数据。
    """
    hexagram_data = state.get("hexagram_data")
    if not hexagram_data:
        return {"inference_result": None}

    hexagram_name = hexagram_data.get("name", "")
    if not hexagram_name:
        return {"inference_result": None}

    # Use real analysis from state instead of fake data
    analysis = state.get("rule_analysis_result")
    month_branch = state.get("month_branch", "子")

    try:
        result = AgentTools.simulate_evolution_chain(
            hexagram_name,
            analysis=analysis,
            month_branch=month_branch,
            steps=3,
        )
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
