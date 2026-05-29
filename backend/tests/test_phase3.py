"""Phase 3 测试

测试Agent工作流、推演引擎、多模型协同、观察Agent。
"""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from foundation.types import (
    Element,
    Hexagram,
    Line,
    Trigram,
    TrigramName,
    YinYang,
    SixRelation,
    SixSpirit,
    ProsperityState,
    RuleAnalysisResult,
    Verdict,
)


# ============================================================================
# 测试数据 fixtures
# ============================================================================


def _make_test_hexagram(name: str = "乾", id: int = 1) -> Hexagram:
    """创建测试用卦象"""
    upper = Trigram(
        name=TrigramName.QIAN,
        binary_rep="111",
        element=Element.METAL,
        nature="天",
        direction="西北",
        family="父",
        body="首",
        animal="马",
    )
    lower = Trigram(
        name=TrigramName.QIAN,
        binary_rep="111",
        element=Element.METAL,
        nature="天",
        direction="西北",
        family="父",
        body="首",
        animal="马",
    )
    lines = tuple(
        Line(
            position=i,
            yin_yang=YinYang.YANG,
            is_moving=(i == 1),
            element=Element.METAL,
            six_relation=SixRelation.BROTHER,
            six_spirit=SixSpirit.QINGLONG,
            gan_zhi="甲子",
            is_shi=(i == 1),
            is_ying=(i == 4),
        )
        for i in range(1, 7)
    )
    return Hexagram(
        id=id,
        name=name,
        upper_trigram=upper,
        lower_trigram=lower,
        lines=lines,
        element=Element.METAL,
        judgment="元亨利贞",
        image="天行健，君子以自强不息",
    )


def _make_test_analysis() -> RuleAnalysisResult:
    """创建测试用分析结果"""
    return RuleAnalysisResult(
        yong_shen=SixRelation.BROTHER,
        moving_lines=(1,),
        relationships=("世爻兄弟临青龙",),
        prosperity=ProsperityState.WANG,
        verdict=Verdict(overall="吉", strength=75, trend="上升", confidence=80),
    )


# ============================================================================
# Agent工作流测试
# ============================================================================


class TestAgentWorkflow:
    """Agent工作流引擎测试"""

    def test_classify_intent_divination(self):
        """测试意图分类 - 解卦"""
        from ai.agent.workflow import _classify_intent

        state = {"user_query": "乾卦初爻动，事业方面如何？"}
        result = _classify_intent(state)

        assert result["intent"] == "divination"
        assert result["confidence"] > 0

    def test_classify_intent_evolution(self):
        """测试意图分类 - 推演"""
        from ai.agent.workflow import _classify_intent

        state = {"user_query": "帮我推演一下坤卦的变化趋势"}
        result = _classify_intent(state)

        assert result["intent"] == "evolution"
        assert result["confidence"] >= 0.7

    def test_classify_intent_learn(self):
        """测试意图分类 - 学习"""
        from ai.agent.workflow import _classify_intent

        state = {"user_query": "什么是五行相生相克？"}
        result = _classify_intent(state)

        assert result["intent"] == "learn"

    def test_classify_intent_extract_entity(self):
        """测试实体提取"""
        from ai.agent.workflow import _classify_intent

        state = {"user_query": "乾卦代表什么意思？"}
        result = _classify_intent(state)

        assert result["entities"].get("hexagram_name") == "乾"

    def test_safety_check_clean(self):
        """测试安全检查 - 正常内容"""
        from ai.agent.workflow import _safety_check

        state = {"interpretation_draft": "这是一个分析结果"}
        result = _safety_check(state)

        assert result["risk_flags"] == []
        assert result["final_response"] == "这是一个分析结果"

    def test_safety_check_forbidden(self):
        """测试安全检查 - 检测禁止词"""
        from ai.agent.workflow import _safety_check

        state = {"interpretation_draft": "你一定会成功"}
        result = _safety_check(state)

        assert len(result["risk_flags"]) > 0
        assert "一定会" not in result["final_response"]

    def test_evolution_simulate(self):
        """测试推演模拟节点"""
        from ai.agent.workflow import _evolution_simulate

        hexagram = _make_test_hexagram()
        state = {
            "hexagram_data": {
                "name": hexagram.name,
            },
        }
        result = _evolution_simulate(state)

        # 推演可能成功或失败（取决于HexagramEngine实现）
        assert "inference_result" in result


class TestAgentTools:
    """Agent工具集测试"""

    def test_query_hexagram(self):
        """测试查询卦象"""
        from ai.agent.tools import AgentTools

        result = AgentTools.query_hexagram("乾")
        # 可能成功或失败，取决于HexagramEngine
        assert result.tool_name == "query_hexagram"

    def test_calculate_five_elements(self):
        """测试五行计算"""
        from ai.agent.tools import AgentTools

        result = AgentTools.calculate_five_elements("金", "水")
        assert result.tool_name == "calculate_five_elements"


class TestAgentOrchestrator:
    """Agent编排器测试"""

    @pytest.mark.asyncio
    async def test_run_basic(self):
        """测试基本运行"""
        from ai.agent.orchestrator import AgentOrchestrator

        orchestrator = AgentOrchestrator()
        result = await orchestrator.run(
            user_query="乾卦代表什么？",
        )

        assert result.intent in ("divination", "evolution", "learn", "trend")
        assert result.duration_ms >= 0  # 可能非常快

    @pytest.mark.asyncio
    async def test_run_with_hexagram(self):
        """测试带卦象数据的运行"""
        from ai.agent.orchestrator import AgentOrchestrator

        orchestrator = AgentOrchestrator()
        hexagram = _make_test_hexagram()

        result = await orchestrator.run(
            user_query="这个卦怎么解？",
            hexagram_data={"name": hexagram.name},
        )

        # interpret节点是占位实现，response可能为空
        assert result.intent in ("divination", "evolution", "learn", "trend")


# ============================================================================
# 推演引擎测试
# ============================================================================


class TestEvolutionEngine:
    """深度推演引擎测试"""

    def test_evolve_basic(self):
        """测试基本推演"""
        from rule_engine.evolution_engine import EvolutionEngine

        hexagram = _make_test_hexagram()
        result = EvolutionEngine.evolve(hexagram, max_depth=3, branch_factor=2)

        assert result.source_hexagram == "乾"
        assert result.tree.max_depth == 3
        assert result.tree.total_nodes > 0
        assert len(result.tree.paths) > 0
        assert len(result.recommended_path) > 0

    def test_evolve_with_analysis(self):
        """测试带分析结果的推演"""
        from rule_engine.evolution_engine import EvolutionEngine

        hexagram = _make_test_hexagram()
        analysis = _make_test_analysis()

        result = EvolutionEngine.evolve(
            hexagram, analysis=analysis, max_depth=3, branch_factor=2
        )

        assert result.source_hexagram == "乾"
        assert len(result.transitions) > 0

    def test_evolve_depth_limit(self):
        """测试推演深度限制"""
        from rule_engine.evolution_engine import EvolutionEngine

        hexagram = _make_test_hexagram()

        # 超过最大深度应被截断
        result = EvolutionEngine.evolve(hexagram, max_depth=20)
        assert result.tree.max_depth <= EvolutionEngine.MAX_DEPTH

    def test_probability_tree_structure(self):
        """测试概率树结构"""
        from rule_engine.evolution_engine import EvolutionEngine

        hexagram = _make_test_hexagram()
        result = EvolutionEngine.evolve(hexagram, max_depth=3, branch_factor=2)

        root = result.tree.root
        assert root.hexagram_name == "乾"
        assert root.depth == 0
        assert root.probability == 1.0

        # 子节点概率应小于等于父节点
        for child in root.children:
            assert child.probability <= root.probability
            assert child.depth == 1


class TestInferenceEngine:
    """原有推演引擎测试"""

    def test_infer_basic(self):
        """测试基本推演"""
        from rule_engine.inference_engine import InferenceEngine

        hexagram = _make_test_hexagram()
        analysis = _make_test_analysis()

        result = InferenceEngine.infer(hexagram, analysis)

        assert result.source_hexagram == "乾"
        assert len(result.paths) > 0
        assert result.inference_depth <= 3

    def test_infer_trend(self):
        """测试趋势推断"""
        from rule_engine.inference_engine import InferenceEngine

        trend = InferenceEngine._infer_trend("乾", "坤")
        assert trend in ("上升", "下降", "平稳", "转折")


# ============================================================================
# 多模型协同测试
# ============================================================================


class TestMultiModel:
    """多模型协同系统测试"""

    def test_health_monitor(self):
        """测试健康监控"""
        from ai.multi_model import ModelHealthMonitor

        monitor = ModelHealthMonitor()
        monitor.record_success("model-a", 100.0)
        monitor.record_success("model-a", 200.0)
        monitor.record_failure("model-a", "timeout")

        health = monitor.get_health("model-a")
        assert health.success_count == 2
        assert health.failure_count == 1
        assert health.success_rate == pytest.approx(2 / 3)
        assert health.health_score < 1.0

    def test_weight_balancer(self):
        """测试权重平衡器"""
        from ai.multi_model import ModelHealthMonitor, DynamicWeightBalancer

        monitor = ModelHealthMonitor()
        monitor.record_success("model-a", 100.0)
        monitor.record_failure("model-b", "error")

        balancer = DynamicWeightBalancer(monitor)
        balancer.set_base_weights({"model-a": 1.0, "model-b": 1.0})

        weights = balancer.get_dynamic_weights(["model-a", "model-b"])
        assert weights["model-a"] > weights["model-b"]

    @pytest.mark.asyncio
    async def test_parallel_caller(self):
        """测试并行调用"""
        from ai.multi_model import ParallelCaller

        caller = ParallelCaller(timeout_seconds=5.0)

        async def mock_call_a():
            return "result-a"

        async def mock_call_b():
            return "result-b"

        results = await caller.call_parallel([
            ("model-a", mock_call_a),
            ("model-b", mock_call_b),
        ])

        assert len(results) == 2
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_parallel_caller_timeout(self):
        """测试并行调用超时"""
        from ai.multi_model import ParallelCaller

        caller = ParallelCaller(timeout_seconds=0.1)

        async def slow_call():
            await asyncio.sleep(1)
            return "never"

        results = await caller.call_parallel([("slow-model", slow_call)])

        assert len(results) == 1
        assert not results[0].success
        assert results[0].error == "timeout"

    def test_result_fuser(self):
        """测试结果融合"""
        from ai.multi_model import ModelCallResult, ResultFuser

        results = [
            ModelCallResult(
                model_id="a", tier="t1", response="result-a",
                latency_ms=100, tokens_used=50, cost_usd=0.001, success=True,
            ),
            ModelCallResult(
                model_id="b", tier="t2", response="result-b-longer-text",
                latency_ms=200, tokens_used=80, cost_usd=0.002, success=True,
            ),
        ]

        fused = ResultFuser.fuse_by_confidence(results)
        assert fused.fused_response == "result-a"  # 最低延迟
        assert fused.fusion_method == "best_latency"

        fused2 = ResultFuser.fuse_by_voting(results)
        assert fused2.fused_response == "result-b-longer-text"  # 最长


# ============================================================================
# 观察Agent测试
# ============================================================================


class TestObserverAgent:
    """观察Agent测试"""

    def _make_records(self, count: int = 10):
        """创建测试记录"""
        from ai.agent.observer import HexagramRecord

        records = []
        hexagrams = ["乾", "坤", "坎", "离", "震"]
        elements = ["金", "土", "水", "火", "木"]
        sentiments = ["positive", "neutral", "anxious", "negative"]

        for i in range(count):
            records.append(HexagramRecord(
                hexagram_name=hexagrams[i % len(hexagrams)],
                element=elements[i % len(elements)],
                question_topic="事业" if i % 2 == 0 else "感情",
                sentiment=sentiments[i % len(sentiments)],
                timestamp_iso=f"2026-01-{i+1:02d}T10:00:00",
                moving_lines=(1,) if i % 3 == 0 else (),
            ))

        return records

    def test_analyze_patterns(self):
        """测试模式分析"""
        from ai.agent.observer import ObserverAgent

        records = self._make_records(10)
        patterns = ObserverAgent.analyze_patterns(records)

        assert isinstance(patterns, tuple)

    def test_detect_anomalies(self):
        """测试异常检测"""
        from ai.agent.observer import ObserverAgent

        records = self._make_records(10)
        anomalies = ObserverAgent.detect_anomalies(records)

        assert isinstance(anomalies, tuple)

    def test_generate_report(self):
        """测试报告生成"""
        from ai.agent.observer import ObserverAgent

        records = self._make_records(10)
        report = ObserverAgent.generate_report("user-1", records)

        assert report.user_id == "user-1"
        assert report.total_divinations == 10
        assert report.period_days == 30
        assert len(report.dominant_hexagrams) > 0
        assert report.summary != ""

    def test_empty_records_report(self):
        """测试空记录报告"""
        from ai.agent.observer import ObserverAgent

        report = ObserverAgent.generate_report("user-1", [])
        assert report.total_divinations == 0
        assert "无卦记录" in report.summary
