"""综合分析器模块

整合用神选取、生克分析、旺衰分析，生成最终的规则推演结果。

综合判断规则：
- 用神旺相且得生扶 -> 吉
- 用神休囚且受克 -> 凶
- 用神动化回头生 -> 吉
- 用神动化回头克 -> 凶
- 世爻旺相 -> 事可成
- 世爻休囚 -> 事难成
"""

from __future__ import annotations

from foundation.types import (
    Element,
    Hexagram,
    ProsperityState,
    RuleAnalysisResult,
    SixRelation,
    Verdict,
)
from foundation.element_engine import ElementEngine
from rule_engine.yong_shen import YongShenEngine
from rule_engine.sheng_ke_analyzer import RelationshipAnalysis, ShengKeAnalyzer
from rule_engine.wang_shuai_analyzer import ProsperityAnalysis, WangShuaiAnalyzer


class Analyzer:
    """综合分析器

    整合用神选取、生克分析、旺衰分析，生成最终的规则推演结果。
    """

    @classmethod
    def analyze(
        cls,
        hexagram: Hexagram,
        question_type: str,
        month_branch: str = "子",
    ) -> RuleAnalysisResult:
        """综合分析

        分析流程：
        1. 选取用神
        2. 分析生克关系
        3. 判断旺衰
        4. 综合推断吉凶
        5. 生成结论

        Args:
            hexagram: 卦对象
            question_type: 问题类型（如"事业"、"财运"等）
            month_branch: 月份地支，默认"子"月

        Returns:
            规则分析结果
        """
        # 1. 选取用神
        yong_shen = YongShenEngine.find_yong_shen(hexagram, question_type)

        # 2. 分析生克关系
        sheng_ke = ShengKeAnalyzer.analyze(hexagram, yong_shen)

        # 3. 判断旺衰
        wang_shuai = WangShuaiAnalyzer.analyze(
            hexagram, yong_shen, month_branch
        )

        # 4. 综合推断吉凶
        verdict = cls._judge_verdict(
            hexagram, yong_shen, sheng_ke, wang_shuai, month_branch
        )

        # 5. 收集动爻位置
        moving_positions = tuple(
            line.position for line in hexagram.lines if line.is_moving
        )

        # 6. 组装关系描述
        relationships = cls._build_relationships(sheng_ke, wang_shuai)

        return RuleAnalysisResult(
            yong_shen=yong_shen,
            moving_lines=moving_positions,
            relationships=relationships,
            prosperity=wang_shuai.prosperity_state,
            verdict=verdict,
        )

    @classmethod
    def _judge_verdict(
        cls,
        hexagram: Hexagram,
        yong_shen: SixRelation,
        sheng_ke: RelationshipAnalysis,
        wang_shuai: ProsperityAnalysis,
        month_branch: str,
    ) -> Verdict:
        """综合推断吉凶

        判断逻辑：
        - 用神旺相且得生扶 -> 吉
        - 用神休囚且受克 -> 凶
        - 世爻旺相 -> 事可成
        - 世爻休囚 -> 事难成

        Args:
            hexagram: 卦对象
            yong_shen: 用神六亲
            sheng_ke: 生克分析结果
            wang_shuai: 旺衰分析结果
            month_branch: 月份地支（如"子"、"寅"等）

        Returns:
            占卜结论
        """
        # 计算综合得分
        score = 50  # 基础分

        # 用神旺衰加减分
        prosperity = wang_shuai.prosperity_state
        if prosperity == ProsperityState.WANG:
            score += 25
        elif prosperity == ProsperityState.XIANG:
            score += 15
        elif prosperity == ProsperityState.XIU:
            score += 0
        elif prosperity == ProsperityState.QIU:
            score -= 15
        elif prosperity == ProsperityState.SI:
            score -= 25

        # 生克关系加减分
        if sheng_ke.overall_support:
            score += 15
        else:
            score -= 15

        # 用神与世爻的关系
        relation = sheng_ke.yong_shen_to_shi
        if relation == "生":
            score += 10  # 用神生世爻，有利
        elif relation == "克":
            score -= 10  # 用神克世爻，不利
        elif relation == "被生":
            score += 5   # 世爻生用神，小有利
        elif relation == "被克":
            score -= 5   # 世爻克用神，小不利

        # 世爻旺衰（通过月令判断世爻五行）
        shi_element = sheng_ke.shi_element
        shi_prosperity = ElementEngine.judge_prosperity(shi_element, month_branch)
        if shi_prosperity == ProsperityState.WANG:
            score += 10
        elif shi_prosperity == ProsperityState.XIANG:
            score += 5
        elif shi_prosperity == ProsperityState.QIU:
            score -= 5
        elif shi_prosperity == ProsperityState.SI:
            score -= 10

        # 限制在0-100范围
        score = max(0, min(100, score))

        # 判断吉凶
        if score >= 60:
            overall: "str" = "吉"
            trend: "str" = "上升"
        elif score <= 40:
            overall = "凶"
            trend = "下降"
        else:
            overall = "平"
            trend = "平稳"

        # 置信度：旺衰越明显，置信度越高
        confidence = abs(score - 50) * 2
        confidence = max(30, min(95, confidence))

        return Verdict(
            overall=overall,  # type: ignore[arg-type]
            strength=score,
            trend=trend,  # type: ignore[arg-type]
            confidence=confidence,
        )

    @classmethod
    def _get_month_branch_from_element(cls, element: Element) -> str:
        """从月令五行推断一个代表性的地支

        .. deprecated::
            此方法存在信息丢失问题（一个五行对应多地支，只能返回其中一个）。
            请直接传入 ``month_branch`` 参数。将在未来版本移除。

        Args:
            element: 五行属性

        Returns:
            代表性地支
        """
        import warnings

        warnings.warn(
            "_get_month_branch_from_element() is deprecated: "
            "it loses information because an element maps to 2-3 branches. "
            "Pass the original month_branch instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        element_to_branch = {
            Element.WATER: "子",
            Element.EARTH: "丑",
            Element.WOOD: "寅",
            Element.FIRE: "午",
            Element.METAL: "申",
        }
        return element_to_branch.get(element, "子")

    @classmethod
    def _build_relationships(
        cls,
        sheng_ke: RelationshipAnalysis,
        wang_shuai: ProsperityAnalysis,
    ) -> tuple[str, ...]:
        """构建关系描述列表

        Args:
            sheng_ke: 生克分析结果
            wang_shuai: 旺衰分析结果

        Returns:
            关系描述元组
        """
        parts: list[str] = []

        # 用神旺衰描述
        parts.append(
            f"用神({wang_shuai.yong_shen_element.value})"
            f"月令{wang_shuai.prosperity_state.value}："
            f"{wang_shuai.description}"
        )

        # 用神与世爻关系
        parts.append(
            f"用神对世爻：{sheng_ke.yong_shen_to_shi}"
        )

        # 动爻影响
        for effect in sheng_ke.moving_line_effects:
            parts.append(effect)

        return tuple(parts)
