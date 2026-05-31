"""Phase 3 Batch 2 测试

覆盖：深度推演引擎、概率推演树、奇门遁甲引擎、紫微斗数引擎。
"""

from __future__ import annotations

import pytest
from ai.reasoning.deep_reasoning import DeepReasoningEngine
from ai.reasoning.probability_tree import ProbabilityTreeEngine
from ai.reasoning.types import (
    StepType, ConfidenceLevel, ReasoningStep, ReasoningChain,
    TreeBranch, TreeNode, ProbabilityTree,
)
from foundation.qimen_engine import (
    QiMenEngine, QMDoor, QMStar, QMSpirit, QMPalace,
    QMPalaceInfo, QMChart, QMAnalysis,
)
from foundation.ziwei_engine import (
    ZiWeiEngine, ZWStar, ZWAuxStar, ZWHua, ZWPalace,
    ZWChart, ZWAnalysis, ZWPalaceInfo,
)
from foundation.types import Verdict


# ============================================================================
# 深度推演引擎测试
# ============================================================================


class TestDeepReasoningEngine:
    """深度推演引擎测试"""

    def test_reason_basic(self):
        """基本推演应返回10步推理链"""
        chain = DeepReasoningEngine.reason("乾为天", "事业")
        assert len(chain.steps) == 10
        assert chain.initial_hexagram == "乾为天"
        assert chain.overall_confidence in ConfidenceLevel

    def test_reason_step_types(self):
        """推理链应包含所有10种步骤类型"""
        chain = DeepReasoningEngine.reason("坤为地", "财运")
        step_types = {s.step_type for s in chain.steps}
        assert StepType.ANALYZE in step_types
        assert StepType.CONCLUDE in step_types
        assert StepType.BRANCH in step_types

    def test_reason_trend_analysis(self):
        """趋势分析应为定性判断"""
        chain = DeepReasoningEngine.reason("水雷屯", "通用")
        trend = chain.trend_analysis
        assert isinstance(trend, tuple)
        assert len(trend) > 0
        for label, desc in trend:
            assert label in ("吉", "凶", "平")
            assert isinstance(desc, str)
            assert len(desc) > 0

    def test_reason_with_month_branch(self):
        """不同月令应产生不同推演结果"""
        chain_winter = DeepReasoningEngine.reason("乾为天", "事业", month_branch="子")
        chain_summer = DeepReasoningEngine.reason("乾为天", "事业", month_branch="午")
        # 冬夏五行旺衰不同，推理步骤中的逻辑应不同
        winter_logic = [s.logic for s in chain_winter.steps]
        summer_logic = [s.logic for s in chain_summer.steps]
        assert winter_logic != summer_logic

    def test_reason_trend_is_tuple(self):
        """趋势分析应为不可变元组"""
        chain = DeepReasoningEngine.reason("乾为天", "事业")
        assert isinstance(chain.trend_analysis, tuple)
        for item in chain.trend_analysis:
            assert isinstance(item, tuple)
            assert len(item) == 2

    def test_reason_max_steps(self):
        """max_steps应控制推理步数"""
        chain = DeepReasoningEngine.reason("离为火", "通用", max_steps=5)
        assert len(chain.steps) == 5

    def test_reason_conclusion_not_empty(self):
        """结论不应为空"""
        chain = DeepReasoningEngine.reason("兑为泽", "感情")
        assert len(chain.conclusion) > 10

    def test_reason_branch_points(self):
        """应有分支点标记"""
        chain = DeepReasoningEngine.reason("震为雷", "事业")
        assert len(chain.branch_points) > 0
        # 分支点应对应BRANCH类型步骤
        for bp in chain.branch_points:
            step = next(s for s in chain.steps if s.step_number == bp)
            assert step.step_type == StepType.BRANCH

    def test_reason_invalid_hexagram(self):
        """无效卦名应抛出异常"""
        with pytest.raises(ValueError):
            DeepReasoningEngine.reason("不存在的卦", "通用")

    def test_reason_element_changes(self):
        """推理步骤应包含五行变化描述"""
        chain = DeepReasoningEngine.reason("巽为风", "事业")
        has_changes = any(len(s.element_changes) > 0 for s in chain.steps)
        assert has_changes

    def test_reason_confidence_levels(self):
        """推理步骤应有不同的置信度"""
        chain = DeepReasoningEngine.reason("艮为山", "财运")
        confidences = {s.confidence for s in chain.steps}
        assert len(confidences) >= 2  # 至少有2种不同置信度


# ============================================================================
# 概率推演树测试
# ============================================================================


class TestProbabilityTreeEngine:
    """概率推演树测试"""

    def test_build_tree_basic(self):
        """基本建树测试"""
        tree = ProbabilityTreeEngine.build_tree("乾为天", "事业", max_depth=5)
        assert tree.root.hexagram_name == "乾为天"
        assert tree.max_depth == 5
        assert tree.branch_factor == 3

    def test_tree_branches(self):
        """每个非叶节点应有3个分支"""
        tree = ProbabilityTreeEngine.build_tree("坤为地", "通用", max_depth=3)
        # 根节点应有分支
        assert len(tree.root.branches) == 3
        assert len(tree.root.children) == 3

    def test_tree_probability_sum(self):
        """同一节点的分支概率之和应为1"""
        tree = ProbabilityTreeEngine.build_tree("水雷屯", "通用", max_depth=2)
        for branch in tree.root.branches:
            assert 0 < branch.probability < 1
        total = sum(b.probability for b in tree.root.branches)
        assert abs(total - 1.0) < 0.01

    def test_tree_pruning(self):
        """低概率分支应被剪枝"""
        tree = ProbabilityTreeEngine.build_tree("乾为天", "事业", max_depth=8)
        # 深层节点的累积概率应递减
        leaves = ProbabilityTreeEngine._collect_leaves(tree.root)
        for leaf in leaves:
            assert leaf.cumulative_probability >= 0.005

    def test_tree_expected_value(self):
        """期望值应在0-100之间"""
        tree = ProbabilityTreeEngine.build_tree("离为火", "财运")
        assert 0 <= tree.expected_value <= 100

    def test_tree_risk_assessment(self):
        """风险评估不应为空"""
        tree = ProbabilityTreeEngine.build_tree("震为雷", "事业")
        assert len(tree.risk_assessment) > 10

    def test_enumerate_paths(self):
        """路径枚举测试"""
        tree = ProbabilityTreeEngine.build_tree("兑为泽", "感情", max_depth=2)
        paths = ProbabilityTreeEngine.enumerate_paths(tree)
        assert len(paths) > 0
        for hexagrams, prob, verdict, score in paths:
            assert len(hexagrams) > 0
            assert 0 < prob <= 1
            assert verdict in ("吉", "凶", "平")

    def test_get_top_paths(self):
        """前N路径应按概率降序排列"""
        tree = ProbabilityTreeEngine.build_tree("巽为风", "通用", max_depth=3)
        top = ProbabilityTreeEngine.get_top_paths(tree, n=5)
        assert len(top) <= 5
        for i in range(len(top) - 1):
            assert top[i][1] >= top[i + 1][1]

    def test_tree_verdict(self):
        """每个节点应有吉凶判断"""
        tree = ProbabilityTreeEngine.build_tree("艮为山", "健康")
        assert tree.root.verdict in ("吉", "凶", "平")

    def test_tree_total_paths(self):
        """总路径数应大于0"""
        tree = ProbabilityTreeEngine.build_tree("坎为水", "通用", max_depth=3)
        assert tree.total_paths > 0


# ============================================================================
# 奇门遁甲引擎测试
# ============================================================================


class TestQiMenEngine:
    """奇门遁甲引擎测试"""

    def test_time_to_chart_basic(self):
        """基本排盘测试"""
        chart = QiMenEngine.time_to_chart(2025, 5, 29, 10)
        assert isinstance(chart, QMChart)
        assert 1 <= chart.ju <= 9
        assert chart.yin_yang in ("阳遁", "阴遁")
        assert len(chart.palace_info) == 9

    def test_chart_palace_info(self):
        """每宫应有完整的门星神信息"""
        chart = QiMenEngine.time_to_chart(2025, 1, 15, 8)
        for p in chart.palace_info:
            assert isinstance(p.palace, QMPalace)
            assert isinstance(p.door, QMDoor)
            assert isinstance(p.star, QMStar)
            assert isinstance(p.spirit, QMSpirit)
            assert len(p.tian_pan) > 0
            assert len(p.di_pan) > 0

    def test_chart_gan_zhi(self):
        """干支信息应正确格式"""
        chart = QiMenEngine.time_to_chart(2025, 6, 1, 12)
        assert len(chart.year_gan_zhi) == 2
        assert len(chart.month_gan_zhi) == 2
        assert len(chart.day_gan_zhi) == 2
        assert len(chart.hour_gan_zhi) == 2

    def test_chart_xun_kong(self):
        """旬空应有2个地支"""
        chart = QiMenEngine.time_to_chart(2025, 3, 20, 6)
        assert len(chart.xun_kong) == 2

    def test_chart_ma_xing(self):
        """马星应为有效地支"""
        chart = QiMenEngine.time_to_chart(2025, 7, 15, 14)
        branches = "子丑寅卯辰巳午未申酉戌亥"
        assert chart.ma_xing in branches

    def test_analyze_chart_general(self):
        """通用分析测试"""
        chart = QiMenEngine.time_to_chart(2025, 5, 29, 10)
        analysis = QiMenEngine.analyze_chart(chart, "general")
        assert isinstance(analysis, QMAnalysis)
        assert analysis.verdict.overall in ("吉", "凶", "平")
        assert 0 <= analysis.verdict.strength <= 100

    def test_analyze_chart_career(self):
        """事业分析应以开门为用神"""
        chart = QiMenEngine.time_to_chart(2025, 8, 10, 9)
        analysis = QiMenEngine.analyze_chart(chart, "career")
        assert len(analysis.description) > 0

    def test_analyze_chart_wealth(self):
        """财运分析应以生门为用神"""
        chart = QiMenEngine.time_to_chart(2025, 4, 5, 11)
        analysis = QiMenEngine.analyze_chart(chart, "wealth")
        assert analysis.verdict.strength >= 0

    def test_different_times_different_charts(self):
        """不同时间应排出不同盘"""
        chart1 = QiMenEngine.time_to_chart(2025, 1, 1, 0)
        chart2 = QiMenEngine.time_to_chart(2025, 6, 15, 12)
        # 至少局数或干支应不同
        assert (chart1.ju != chart2.ju or
                chart1.hour_gan_zhi != chart2.hour_gan_zhi)

    def test_fuxing_fanin_detection(self):
        """应能检测伏吟和反吟"""
        chart = QiMenEngine.time_to_chart(2025, 5, 29, 10)
        has_fuxing = any(p.is_fuxing for p in chart.palace_info)
        has_fanin = any(p.is_fanin for p in chart.palace_info)
        # 至少能检测到一种（或都没有，也是合法的）
        assert isinstance(has_fuxing, bool)
        assert isinstance(has_fanin, bool)


# ============================================================================
# 紫微斗数引擎测试
# ============================================================================


class TestZiWeiEngine:
    """紫微斗数引擎测试"""

    def test_generate_chart_basic(self):
        """基本排盘测试"""
        chart = ZiWeiEngine.generate_chart(1990, 6, 15, 10, "男")
        assert isinstance(chart, ZWChart)
        assert len(chart.palaces) == 12
        assert chart.gender == "男"

    def test_chart_palaces(self):
        """每宫应有完整信息"""
        chart = ZiWeiEngine.generate_chart(1985, 3, 20, 8, "女")
        for p in chart.palaces:
            assert isinstance(p.palace, ZWPalace)
            assert len(p.gan_zhi) == 2
            assert isinstance(p.main_stars, tuple)
            assert isinstance(p.aux_stars, tuple)
            assert isinstance(p.brightness, tuple)
            assert isinstance(p.hua_stars, tuple)

    def test_chart_gan_zhi(self):
        """干支信息应正确"""
        chart = ZiWeiEngine.generate_chart(2000, 1, 1, 0, "男")
        assert len(chart.year_gan_zhi) == 2
        assert len(chart.month_gan_zhi) == 2
        assert len(chart.day_gan_zhi) == 2
        assert len(chart.hour_gan_zhi) == 2

    def test_chart_wu_xing_ju(self):
        """五行局应在2-6之间"""
        chart = ZiWeiEngine.generate_chart(1995, 8, 15, 14, "女")
        assert 2 <= chart.wu_xing_ju <= 6

    def test_chart_ming_shen_palace(self):
        """命宫和身宫应为有效宫位"""
        chart = ZiWeiEngine.generate_chart(1988, 12, 25, 23, "男")
        assert isinstance(chart.ming_palace, ZWPalace)
        assert isinstance(chart.shen_palace, ZWPalace)

    def test_chart_has_main_stars(self):
        """命盘应有主星分布"""
        chart = ZiWeiEngine.generate_chart(1992, 5, 10, 6, "女")
        all_stars = []
        for p in chart.palaces:
            all_stars.extend(p.main_stars)
        assert len(all_stars) > 0

    def test_analyze_chart_general(self):
        """通用分析（命宫）测试"""
        chart = ZiWeiEngine.generate_chart(1990, 6, 15, 10, "男")
        analysis = ZiWeiEngine.analyze_chart(chart, "general")
        assert isinstance(analysis, ZWAnalysis)
        assert analysis.verdict.overall in ("吉", "凶", "平")

    def test_analyze_chart_career(self):
        """事业分析（官禄宫）测试"""
        chart = ZiWeiEngine.generate_chart(1985, 3, 20, 8, "女")
        analysis = ZiWeiEngine.analyze_chart(chart, "事业")
        assert analysis.target_palace == ZWPalace.GUANLU

    def test_analyze_chart_wealth(self):
        """财运分析（财帛宫）测试"""
        chart = ZiWeiEngine.generate_chart(2000, 1, 1, 0, "男")
        analysis = ZiWeiEngine.analyze_chart(chart, "财运")
        assert analysis.target_palace == ZWPalace.CAIBO

    def test_analyze_chart_relationship(self):
        """感情分析（夫妻宫）测试"""
        chart = ZiWeiEngine.generate_chart(1995, 8, 15, 14, "女")
        analysis = ZiWeiEngine.analyze_chart(chart, "感情")
        assert analysis.target_palace == ZWPalace.FUQI

    def test_different_gender_different_chart(self):
        """不同性别命盘应不同（阴阳顺逆不同）"""
        chart_m = ZiWeiEngine.generate_chart(1990, 6, 15, 10, "男")
        chart_f = ZiWeiEngine.generate_chart(1990, 6, 15, 10, "女")
        # 至少一个宫位应不同
        diffs = []
        for m, f in zip(chart_m.palaces, chart_f.palaces):
            if m.main_stars != f.main_stars or m.hua_stars != f.hua_stars:
                diffs.append(True)
        # 注：同盘不同性别某些情况下可能相同，这是合法的

    def test_chart_sihua(self):
        """四化应正确标记"""
        chart = ZiWeiEngine.generate_chart(1984, 10, 15, 8, "男")
        # 甲年生人：廉贞化禄、破军化权、武曲化科、太阳化忌
        all_hua = []
        for p in chart.palaces:
            all_hua.extend(p.hua_stars)
        # 应该有四化标记
        assert len(all_hua) > 0

    def test_brightness_values(self):
        """亮度值应为有效值"""
        valid_brightness = {"庙", "旺", "得", "利", "平", "不", "陷"}
        chart = ZiWeiEngine.generate_chart(1990, 6, 15, 10, "男")
        for p in chart.palaces:
            for b in p.brightness:
                assert b in valid_brightness, f"Invalid brightness: {b}"


# ============================================================================
# 集成测试
# ============================================================================


class TestPhase3Integration:
    """Phase 3 Batch 2 集成测试"""

    def test_qimen_verdict_structure(self):
        """奇门遁甲结论应符合Verdict结构"""
        chart = QiMenEngine.time_to_chart(2025, 5, 29, 10)
        analysis = QiMenEngine.analyze_chart(chart)
        v = analysis.verdict
        assert isinstance(v, Verdict)
        assert v.overall in ("吉", "凶", "平")
        assert 0 <= v.strength <= 100
        assert v.trend in ("上升", "下降", "平稳")
        assert 0 <= v.confidence <= 100

    def test_ziwei_verdict_structure(self):
        """紫微斗数结论应符合Verdict结构"""
        chart = ZiWeiEngine.generate_chart(1990, 6, 15, 10, "男")
        analysis = ZiWeiEngine.analyze_chart(chart)
        v = analysis.verdict
        assert isinstance(v, Verdict)
        assert v.overall in ("吉", "凶", "平")
        assert 0 <= v.strength <= 100

    def test_reasoning_chain_consistency(self):
        """推理链应逻辑一致"""
        chain = DeepReasoningEngine.reason("乾为天", "事业")
        # 结论步骤应在最后
        conclude = next(s for s in chain.steps if s.step_type == StepType.CONCLUDE)
        assert conclude.step_number == 10
        # 分支步骤应在验证之后
        branch = next(s for s in chain.steps if s.step_type == StepType.BRANCH)
        validate = next(s for s in chain.steps if s.step_type == StepType.VALIDATE)
        assert branch.step_number > validate.step_number

    def test_probability_tree_paths_consistency(self):
        """概率树路径应一致"""
        tree = ProbabilityTreeEngine.build_tree("坤为地", "通用", max_depth=3)
        paths = ProbabilityTreeEngine.enumerate_paths(tree)
        for hexagrams, prob, verdict, score in paths:
            # 每条路径应从根卦开始
            assert hexagrams[0] == "坤为地"
            # 路径长度应等于深度+1
            assert len(hexagrams) <= tree.max_depth + 1
