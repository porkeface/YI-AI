"""生克关系分析模块

分析卦中各爻之间的五行生克关系，包括：
- 用神与世爻的关系
- 用神与动爻的关系
- 用神的旺衰
- 动爻对用神的影响
"""

from __future__ import annotations

from dataclasses import dataclass

from foundation.types import Element, Hexagram, SixRelation
from foundation.element_engine import ElementEngine


@dataclass(frozen=True)
class RelationshipAnalysis:
    """生克关系分析结果

    Attributes:
        yong_shen_element: 用神的五行
        shi_element: 世爻的五行
        yong_shen_to_shi: 用神对世爻的关系
        moving_line_effects: 各动爻对用神的影响描述
        overall_support: 用神是否得力（生扶多于克制）
    """

    yong_shen_element: Element
    shi_element: Element
    yong_shen_to_shi: str
    moving_line_effects: tuple[str, ...]
    overall_support: bool


class ShengKeAnalyzer:
    """生克关系分析器

    分析卦中用神与其他爻之间的五行生克关系。
    """

    @classmethod
    def analyze(
        cls, hexagram: Hexagram, yong_shen: SixRelation
    ) -> RelationshipAnalysis:
        """分析生克关系

        分析维度：
        1. 用神与世爻的生克关系
        2. 各动爻对用神的生克影响
        3. 综合判断用神是否得力

        Args:
            hexagram: 卦对象
            yong_shen: 用神六亲

        Returns:
            生克关系分析结果
        """
        # 找到用神爻和世爻
        yong_shen_line = None
        shi_line = None
        moving_lines: list[tuple[int, Element]] = []

        for line in hexagram.lines:
            if line.six_relation == yong_shen and yong_shen_line is None:
                yong_shen_line = line
            if line.is_shi:
                shi_line = line
            if line.is_moving:
                moving_lines.append((line.position, line.element))

        # 用神与世爻的关系
        if yong_shen_line is not None and shi_line is not None:
            yong_shen_to_shi = ElementEngine.get_relation(
                yong_shen_line.element, shi_line.element
            )
            ys_element = yong_shen_line.element
            shi_element = shi_line.element
        else:
            yong_shen_to_shi = "无"
            ys_element = Element.EARTH
            shi_element = Element.EARTH

        # 分析各动爻对用神的影响
        effects: list[str] = []
        support_count = 0
        hinder_count = 0

        for pos, moving_elem in moving_lines:
            if yong_shen_line is not None:
                relation = ElementEngine.get_relation(
                    moving_elem, yong_shen_line.element
                )
                if relation == "生":
                    effects.append(
                        f"{pos}爻({moving_elem.value})生用神"
                    )
                    support_count += 1
                elif relation == "克":
                    effects.append(
                        f"{pos}爻({moving_elem.value})克用神"
                    )
                    hinder_count += 1
                elif relation == "被生":
                    effects.append(
                        f"{pos}爻({moving_elem.value})被用神生"
                    )
                    hinder_count += 1
                elif relation == "被克":
                    effects.append(
                        f"{pos}爻({moving_elem.value})被用神克"
                    )
                    support_count += 1
                else:
                    effects.append(
                        f"{pos}爻({moving_elem.value})与用神同"
                    )

        # 综合判断：生扶多于克制则得力
        overall_support = support_count >= hinder_count

        return RelationshipAnalysis(
            yong_shen_element=ys_element,
            shi_element=shi_element,
            yong_shen_to_shi=yong_shen_to_shi,
            moving_line_effects=tuple(effects),
            overall_support=overall_support,
        )
