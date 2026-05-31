"""模式分析器

基于五行旺衰理论，对检测到的模式进行定性分析。
不使用数值打分，而是输出旺相休囚死等定性判断。

核心分析维度：
- 五行旺衰：根据月令判断用神旺衰状态
- 趋势判断：基于模式频率变化判断上升/平稳/下降
- 生克关系：分析卦象五行之间的生克关系
- 综合建议：基于卦象给出定性建议
"""

from __future__ import annotations

import logging
from typing import Any, Sequence

from ai.observation.types import (
    DetectedPattern,
    PatternCategory,
    TrendDirection,
    TrendIndicator,
)
from foundation.element_engine import ElementEngine
from foundation.types import Element, ProsperityState, TrigramName

logger = logging.getLogger(__name__)

# 八卦对应的五行属性
_TRIGRAM_ELEMENT: dict[TrigramName, Element] = {
    TrigramName.QIAN: Element.METAL,
    TrigramName.DUI: Element.METAL,
    TrigramName.LI: Element.FIRE,
    TrigramName.ZHEN: Element.WOOD,
    TrigramName.XUN: Element.WOOD,
    TrigramName.KAN: Element.WATER,
    TrigramName.GEN: Element.EARTH,
    TrigramName.KUN: Element.EARTH,
}

# 五行旺衰的定性描述（用于输出文字）
_PROSPERITY_DESC: dict[ProsperityState, str] = {
    ProsperityState.WANG: "当令而旺，气势充沛",
    ProsperityState.XIANG: "得令之生，力量较强",
    ProsperityState.XIU: "休息状态，力量平平",
    ProsperityState.QIU: "受制被克，力量较弱",
    ProsperityState.SI: "死绝无力，力量最弱",
}

# 趋势方向的定性描述
_TREND_DESC: dict[TrendDirection, str] = {
    TrendDirection.IMPROVING: "近期卦象频率上升，事态有积极发展的迹象",
    TrendDirection.STABLE: "近期卦象平稳，事态处于相对稳定的状态",
    TrendDirection.DECLINING: "近期卦象频率下降，需关注事态是否趋于消退",
    TrendDirection.VOLATILE: "近期卦象波动较大，事态变化频繁",
    TrendDirection.TRANSITIONAL: "近期卦象处于转折期，事态可能面临变化",
}

# 五行生克关系的定性描述
_RELATION_DESC: dict[str, str] = {
    "生": "相生相助，有推动促进之力",
    "克": "相克制约，有压制阻碍之力",
    "被生": "受生得助，有外力扶持",
    "被克": "受克被制，需防外力干扰",
    "同": "比和同气，力量相当",
}


class PatternAnalyzer:
    """模式分析器

    基于五行旺衰理论对检测到的模式进行定性分析。
    纯函数式设计 — 所有方法为 classmethod，不维护状态。

    不输出数值分数，而是输出：
    - strength: 旺/相/休/囚/死（五行旺衰）
    - trend: 上升/平稳/下降
    - relationships: 五行生克关系的文字描述
    - advice: 基于卦象的建议
    """

    @classmethod
    def analyze(
        cls,
        patterns: Sequence[DetectedPattern],
        trend_indicators: Sequence[TrendIndicator] | None = None,
        month_branch: str = "子",
    ) -> dict[str, Any]:
        """执行模式定性分析

        Args:
            patterns: 检测到的模式列表
            trend_indicators: 趋势指标列表（可选）
            month_branch: 月支（默认"子"，用于旺衰判断）

        Returns:
            定性分析结果字典，包含 strength, trend, relationships, advice
        """
        if not patterns:
            return cls._empty_result()

        return cls._assess_patterns(patterns, trend_indicators, month_branch)

    @classmethod
    def _assess_patterns(
        cls,
        patterns: Sequence[DetectedPattern],
        trend_indicators: Sequence[TrendIndicator] | None,
        month_branch: str,
    ) -> dict[str, Any]:
        """对模式进行定性评估

        基于五行旺衰理论，不使用数值打分，输出定性判断。

        Args:
            patterns: 检测到的模式列表
            trend_indicators: 趋势指标列表
            month_branch: 月支

        Returns:
            定性评估结果
        """
        # 1. 提取主要卦象，判断五行旺衰
        hexagram_names = cls._extract_hexagram_names(patterns)
        element_assessment = cls._assess_elements(hexagram_names, month_branch)

        # 2. 判断趋势方向
        trend = cls._assess_trend(patterns, trend_indicators)

        # 3. 分析五行生克关系
        relationships = cls._assess_relationships(hexagram_names, month_branch)

        # 4. 生成综合建议
        advice = cls._generate_advice(
            element_assessment, trend, relationships, patterns
        )

        return {
            "strength": element_assessment["strength"],
            "trend": trend,
            "relationships": relationships,
            "advice": advice,
        }

    @classmethod
    def _extract_hexagram_names(
        cls, patterns: Sequence[DetectedPattern]
    ) -> list[str]:
        """从模式中提取卦象名称

        Args:
            patterns: 检测到的模式列表

        Returns:
            卦象名称列表
        """
        names: list[str] = []
        for p in patterns:
            if p.category == PatternCategory.HEXAGRAM_FREQUENCY:
                names.extend(p.examples)
            elif p.category == PatternCategory.CHANGE_SEQUENCE:
                names.extend(p.examples)
        # 去重保持顺序
        seen: set[str] = set()
        unique: list[str] = []
        for n in names:
            if n not in seen:
                seen.add(n)
                unique.append(n)
        return unique

    @classmethod
    def _assess_elements(
        cls, hexagram_names: Sequence[str], month_branch: str
    ) -> dict[str, str]:
        """判断卦象五行的旺衰状态

        Args:
            hexagram_names: 卦象名称列表
            month_branch: 月支

        Returns:
            包含 strength 和 description 的字典
        """
        if not hexagram_names:
            return {
                "strength": ProsperityState.XIU.value,
                "description": "无明显卦象特征，力量平平",
            }

        # 统计各旺衰状态出现次数
        state_counts: dict[ProsperityState, int] = {
            s: 0 for s in ProsperityState
        }

        for name in hexagram_names:
            element = cls._get_trigram_element(name)
            if element is not None:
                try:
                    state = ElementEngine.judge_prosperity(
                        element, month_branch
                    )
                    state_counts[state] += 1
                except ValueError:
                    logger.debug("无法判断卦象 %s 的旺衰", name)

        # 取出现最多的旺衰状态作为整体判断
        dominant_state = max(state_counts, key=lambda s: state_counts[s])

        # 如果全部为0（无法判断），默认为"休"
        if state_counts[dominant_state] == 0:
            dominant_state = ProsperityState.XIU

        description = _PROSPERITY_DESC.get(dominant_state, "力量状态不明")

        return {
            "strength": dominant_state.value,
            "description": description,
        }

    @classmethod
    def _get_trigram_element(cls, hexagram_name: str) -> Element | None:
        """获取卦象对应的五行属性

        通过卦象名称查找对应的八卦，再获取其五行属性。

        Args:
            hexagram_name: 卦象名称（如"乾"、"坤"等）

        Returns:
            五行属性，如果找不到则返回 None
        """
        # 直接匹配八卦名称
        for trigram, element in _TRIGRAM_ELEMENT.items():
            if trigram.value == hexagram_name:
                return element

        # 尝试从六十四卦名称中提取上卦
        # 六十四卦名称格式通常为"XX卦"或直接是卦名
        # 这里做简单的前缀匹配
        for trigram, element in _TRIGRAM_ELEMENT.items():
            if hexagram_name.startswith(trigram.value):
                return element

        return None

    @classmethod
    def _assess_trend(
        cls,
        patterns: Sequence[DetectedPattern],
        trend_indicators: Sequence[TrendIndicator] | None,
    ) -> str:
        """判断趋势方向

        优先使用趋势指标，否则根据模式频率变化推断。

        Args:
            patterns: 检测到的模式列表
            trend_indicators: 趋势指标列表

        Returns:
            趋势描述文字
        """
        # 优先使用已有趋势指标
        if trend_indicators:
            # 找活动频率指标
            for indicator in trend_indicators:
                if indicator.metric == "活动频率":
                    return _TREND_DESC.get(
                        indicator.direction, "趋势不明"
                    )
            # 没有频率指标，取第一个
            return _TREND_DESC.get(
                trend_indicators[0].direction, "趋势不明"
            )

        # 无趋势指标时，根据模式频率推断
        freq_pattern = cls._find_dominant_frequency_pattern(patterns)
        if freq_pattern is None:
            return "数据不足，趋势暂不明确"

        # 频率高且置信度高，视为上升
        if freq_pattern.frequency >= 5 and freq_pattern.confidence > 0.5:
            return _TREND_DESC[TrendDirection.IMPROVING]
        elif freq_pattern.frequency >= 3:
            return _TREND_DESC[TrendDirection.STABLE]
        else:
            return _TREND_DESC[TrendDirection.DECLINING]

    @classmethod
    def _find_dominant_frequency_pattern(
        cls, patterns: Sequence[DetectedPattern]
    ) -> DetectedPattern | None:
        """查找主导的频率模式

        Args:
            patterns: 检测到的模式列表

        Returns:
            频率最高的卦象频率模式，如果没有则返回 None
        """
        freq_patterns = [
            p for p in patterns
            if p.category == PatternCategory.HEXAGRAM_FREQUENCY
        ]
        if not freq_patterns:
            return None
        return max(freq_patterns, key=lambda p: p.frequency)

    @classmethod
    def _assess_relationships(
        cls, hexagram_names: Sequence[str], month_branch: str
    ) -> str:
        """分析五行生克关系

        Args:
            hexagram_names: 卦象名称列表
            month_branch: 月支

        Returns:
            五行生克关系的文字描述
        """
        if not hexagram_names:
            return "无明显卦象，五行关系不显著"

        elements = [
            cls._get_trigram_element(name)
            for name in hexagram_names
        ]
        elements = [e for e in elements if e is not None]

        if len(elements) < 2:
            if elements:
                elem = elements[0]
                try:
                    state = ElementEngine.judge_prosperity(
                        elem, month_branch
                    )
                    return (
                        f"主卦五行属{elem.value}，"
                        f"月令下为{state.value}状态"
                    )
                except ValueError:
                    return f"主卦五行属{elem.value}"
            return "五行关系不显著"

        # 分析相邻卦象之间的生克关系
        relation_parts: list[str] = []
        for i in range(len(elements) - 1):
            source = elements[i]
            target = elements[i + 1]
            relation = ElementEngine.get_relation(source, target)
            if relation in _RELATION_DESC:
                relation_parts.append(
                    f"{source.value}{relation}{target.value}"
                    f"（{_RELATION_DESC[relation]}）"
                )

        if not relation_parts:
            return "卦象五行之间无显著生克关系"

        return "；".join(relation_parts)

    @classmethod
    def _generate_advice(
        cls,
        element_assessment: dict[str, str],
        trend: str,
        relationships: str,
        patterns: Sequence[DetectedPattern],
    ) -> str:
        """生成综合建议

        基于旺衰状态、趋势和生克关系，给出定性建议。

        Args:
            element_assessment: 五行旺衰评估结果
            trend: 趋势描述
            relationships: 五行生克关系描述
            patterns: 检测到的模式列表

        Returns:
            综合建议文字
        """
        parts: list[str] = []

        strength = element_assessment.get("strength", "休")

        # 基于旺衰状态的建议
        if strength == ProsperityState.WANG.value:
            parts.append("当前五行当令而旺，气势充沛，宜主动出击、把握时机")
        elif strength == ProsperityState.XIANG.value:
            parts.append("当前五行得生相助，力量较强，可积极推进事务")
        elif strength == ProsperityState.XIU.value:
            parts.append("当前五行处于休息状态，宜守不宜攻，静观其变为佳")
        elif strength == ProsperityState.QIU.value:
            parts.append("当前五行受制被克，力量较弱，宜韬光养晦、等待时机")
        elif strength == ProsperityState.SI.value:
            parts.append("当前五行死绝无力，力量最弱，宜暂缓行动、积蓄力量")

        # 基于趋势的建议
        if "上升" in trend:
            parts.append("趋势向好，可顺势而为")
        elif "下降" in trend:
            parts.append("趋势下行，需谨慎应对")
        elif "转折" in trend:
            parts.append("处于转折点，需审时度势")

        # 基于模式类别的补充建议
        categories = {p.category for p in patterns}
        if PatternCategory.EMOTIONAL_CYCLE in categories:
            parts.append("近期情绪波动较大，建议保持心态平和")
        if PatternCategory.TOPIC_CLUSTER in categories:
            parts.append("关注主题集中，可深入思考相关问题的本质")

        if not parts:
            parts.append("当前无显著趋势，保持平常心即可")

        return "。".join(parts) + "。"

    @classmethod
    def _empty_result(cls) -> dict[str, Any]:
        """返回空的分析结果

        Returns:
            默认的空分析结果
        """
        return {
            "strength": ProsperityState.XIU.value,
            "trend": "数据不足，暂无法判断趋势",
            "relationships": "无模式数据，五行关系不显著",
            "advice": "暂无足够数据进行分析，建议多积累卦象记录后再做判断。",
        }
