"""五行引擎模块

实现五行相生相克关系和旺衰判断。
五行相生：木生火、火生土、土生金、金生水、水生木
五行相克：木克土、土克水、水克火、火克金、金克木
"""

from __future__ import annotations

from foundation.types import Element, ProsperityState


# 六冲配对：月支冲爻支即为月破
CLASH_PAIRS: dict[str, str] = {
    "子": "午", "午": "子",
    "丑": "未", "未": "丑",
    "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰",
    "巳": "亥", "亥": "巳",
}


class ElementEngine:
    """五行引擎

    提供五行生克关系查询和旺衰判断功能。
    """

    _DATA_LOADED: bool = False

    # 五行相生关系：key生value
    _GENERATES: dict[Element, Element] = {
        Element.WOOD: Element.FIRE,     # 木生火
        Element.FIRE: Element.EARTH,    # 火生土
        Element.EARTH: Element.METAL,   # 土生金
        Element.METAL: Element.WATER,   # 金生水
        Element.WATER: Element.WOOD,    # 水生木
    }

    # 五行相克关系：key克value
    _OVERCOMES: dict[Element, Element] = {
        Element.WOOD: Element.EARTH,    # 木克土
        Element.EARTH: Element.WATER,   # 土克水
        Element.WATER: Element.FIRE,    # 水克火
        Element.FIRE: Element.METAL,    # 火克金
        Element.METAL: Element.WOOD,    # 金克木
    }

    # 地支对应的五行
    _BRANCH_ELEMENT: dict[str, Element] = {
        "子": Element.WATER,
        "丑": Element.EARTH,
        "寅": Element.WOOD,
        "卯": Element.WOOD,
        "辰": Element.EARTH,
        "巳": Element.FIRE,
        "午": Element.FIRE,
        "未": Element.EARTH,
        "申": Element.METAL,
        "酉": Element.METAL,
        "戌": Element.EARTH,
        "亥": Element.WATER,
    }

    # 月份地支对应的旺相休囚死
    # 格式：month_element -> {element: prosperity_state}
    _PROSPERITY_TABLE: dict[Element, dict[Element, ProsperityState]] = {
        Element.WOOD: {
            Element.WOOD: ProsperityState.WANG,
            Element.FIRE: ProsperityState.XIANG,
            Element.EARTH: ProsperityState.SI,
            Element.METAL: ProsperityState.QIU,
            Element.WATER: ProsperityState.XIU,
        },
        Element.FIRE: {
            Element.WOOD: ProsperityState.XIU,
            Element.FIRE: ProsperityState.WANG,
            Element.EARTH: ProsperityState.XIANG,
            Element.METAL: ProsperityState.SI,
            Element.WATER: ProsperityState.QIU,
        },
        Element.EARTH: {
            Element.WOOD: ProsperityState.QIU,
            Element.FIRE: ProsperityState.XIU,
            Element.EARTH: ProsperityState.WANG,
            Element.METAL: ProsperityState.XIANG,
            Element.WATER: ProsperityState.SI,
        },
        Element.METAL: {
            Element.WOOD: ProsperityState.SI,
            Element.FIRE: ProsperityState.QIU,
            Element.EARTH: ProsperityState.XIU,
            Element.METAL: ProsperityState.WANG,
            Element.WATER: ProsperityState.XIANG,
        },
        Element.WATER: {
            Element.WOOD: ProsperityState.XIANG,
            Element.FIRE: ProsperityState.SI,
            Element.EARTH: ProsperityState.QIU,
            Element.METAL: ProsperityState.XIU,
            Element.WATER: ProsperityState.WANG,
        },
    }

    @classmethod
    def _ensure_data_loaded(cls) -> None:
        """从JSON数据文件加载五行旺衰表（懒加载）

        成功加载后覆盖硬编码的 _PROSPERITY_TABLE，失败时保留硬编码数据。
        """
        if cls._DATA_LOADED:
            return
        try:
            from foundation.reference_data import get_element_prosperity

            prosperity_list = get_element_prosperity()
            if prosperity_list:
                table: dict[Element, dict[Element, ProsperityState]] = {}
                for entry in prosperity_list:
                    month_elem = Element(entry["month_element"])
                    target_elem = Element(entry["target_element"])
                    state = ProsperityState(entry["state"])
                    if month_elem not in table:
                        table[month_elem] = {}
                    table[month_elem][target_elem] = state
                if table:
                    cls._PROSPERITY_TABLE = table
        except Exception:
            pass  # fall back to hardcoded
        cls._DATA_LOADED = True

    @classmethod
    def generates(cls, source: Element, target: Element) -> bool:
        """判断source是否生target

        Args:
            source: 源五行
            target: 目标五行

        Returns:
            是否相生
        """
        return cls._GENERATES.get(source) == target

    @classmethod
    def overcomes(cls, source: Element, target: Element) -> bool:
        """判断source是否克target

        Args:
            source: 源五行
            target: 目标五行

        Returns:
            是否相克
        """
        return cls._OVERCOMES.get(source) == target

    @classmethod
    def get_relation(cls, source: Element, target: Element) -> str:
        """获取两个五行之间的关系

        Args:
            source: 源五行
            target: 目标五行

        Returns:
            关系描述："生"/"克"/"被生"/"被克"/"同"
        """
        if source == target:
            return "同"
        if cls.generates(source, target):
            return "生"
        if cls.overcomes(source, target):
            return "克"
        if cls.generates(target, source):
            return "被生"
        if cls.overcomes(target, source):
            return "被克"
        return "无"

    @classmethod
    def judge_prosperity(
        cls, element: Element, month_branch: str
    ) -> ProsperityState:
        """根据月令判断五行旺衰

        Args:
            element: 要判断的五行
            month_branch: 月份地支（如"子"、"丑"等）

        Returns:
            旺衰状态

        Raises:
            ValueError: 如果地支无效
        """
        cls._ensure_data_loaded()
        month_element = cls._BRANCH_ELEMENT.get(month_branch)
        if month_element is None:
            raise ValueError(f"无效的地支：{month_branch}")
        return cls._PROSPERITY_TABLE[month_element][element]

    @classmethod
    def get_element_by_branch(cls, branch: str) -> Element:
        """根据地支获取五行

        Args:
            branch: 地支

        Returns:
            五行属性

        Raises:
            ValueError: 如果地支无效
        """
        element = cls._BRANCH_ELEMENT.get(branch)
        if element is None:
            raise ValueError(f"无效的地支：{branch}")
        return element

    @staticmethod
    def is_month_break(yao_branch: str, month_branch: str) -> bool:
        """判断是否月破

        月破 = 月支冲爻支（六冲关系）。
        子午冲、丑未冲、寅申冲、卯酉冲、辰戌冲、巳亥冲。

        Args:
            yao_branch: 爻的地支（如"子"、"丑"等）
            month_branch: 月支（如"子"、"丑"等）

        Returns:
            True 表示月破
        """
        return CLASH_PAIRS.get(yao_branch) == month_branch
