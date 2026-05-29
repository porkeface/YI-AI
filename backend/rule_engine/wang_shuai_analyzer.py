"""旺衰分析模块

根据月令（地支）判断用神的旺衰状态。

五行旺衰状态：
- 旺：五行当令（与月令同五行）
- 相：五行得生（月令生该五行）
- 休：五行休息（该五行生月令）
- 囚：五行被克（该五行克月令）
- 死：五行死绝（月令克该五行）
"""

from __future__ import annotations

from dataclasses import dataclass

from foundation.types import Element, Hexagram, ProsperityState, SixRelation
from foundation.element_engine import ElementEngine


# 旺衰状态的描述文本
_PROSPERITY_DESCRIPTIONS: dict[ProsperityState, str] = {
    ProsperityState.WANG: "当令旺相，力量最强",
    ProsperityState.XIANG: "得月令生扶，力量较强",
    ProsperityState.XIU: "休息状态，力量一般",
    ProsperityState.QIU: "受月令克制，力量较弱",
    ProsperityState.SI: "死绝无气，力量最弱",
}


@dataclass(frozen=True)
class ProsperityAnalysis:
    """旺衰分析结果

    Attributes:
        month_element: 月令的五行
        yong_shen_element: 用神的五行
        prosperity_state: 用神的旺衰状态
        description: 旺衰状态的文字描述
    """

    month_element: Element
    yong_shen_element: Element
    prosperity_state: ProsperityState
    description: str


class WangShuaiAnalyzer:
    """旺衰分析器

    根据月令判断用神的旺衰状态。
    """

    @classmethod
    def analyze(
        cls,
        hexagram: Hexagram,
        yong_shen: SixRelation,
        month_branch: str,
    ) -> ProsperityAnalysis:
        """分析用神旺衰

        Args:
            hexagram: 卦对象
            yong_shen: 用神六亲
            month_branch: 月份地支（如"子"、"丑"等）

        Returns:
            旺衰分析结果

        Raises:
            ValueError: 如果地支无效或卦中未找到用神
        """
        # 获取月令五行
        month_element = ElementEngine.get_element_by_branch(month_branch)

        # 找到用神爻的五行
        yong_shen_element = cls._find_yong_shen_element(hexagram, yong_shen)

        # 判断旺衰
        prosperity_state = ElementEngine.judge_prosperity(
            yong_shen_element, month_branch
        )

        # 获取描述
        description = _PROSPERITY_DESCRIPTIONS[prosperity_state]

        return ProsperityAnalysis(
            month_element=month_element,
            yong_shen_element=yong_shen_element,
            prosperity_state=prosperity_state,
            description=description,
        )

    @classmethod
    def _find_yong_shen_element(
        cls, hexagram: Hexagram, yong_shen: SixRelation
    ) -> Element:
        """找到用神爻的五行属性

        Args:
            hexagram: 卦对象
            yong_shen: 用神六亲

        Returns:
            用神的五行属性

        Raises:
            ValueError: 如果卦中未找到用神
        """
        for line in hexagram.lines:
            if line.six_relation == yong_shen:
                return line.element
        raise ValueError(f"卦中未找到用神 {yong_shen.value} 对应的爻")
