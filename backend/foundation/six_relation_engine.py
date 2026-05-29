"""六亲引擎模块

实现六亲关系推导。
六亲关系：生我者为父母，克我者为官鬼，我克者为妻财，我生者为子孙，同我者为兄弟
"""

from __future__ import annotations

from foundation.types import Element, SixRelation


class SixRelationEngine:
    """六亲引擎

    根据卦的五行和各爻的五行，推导六亲关系。
    """

    # 五行生克关系表
    # key: (我, 对方) -> 六亲关系
    _RELATION_MAP: dict[tuple[Element, Element], SixRelation] = {}

    @classmethod
    def _build_relation_map(cls) -> None:
        """构建六亲关系映射表"""
        if cls._RELATION_MAP:
            return

        # 五行相生：木生火、火生土、土生金、金生水、水生木
        generates = {
            Element.WOOD: Element.FIRE,
            Element.FIRE: Element.EARTH,
            Element.EARTH: Element.METAL,
            Element.METAL: Element.WATER,
            Element.WATER: Element.WOOD,
        }

        # 五行相克：木克土、土克水、水克火、火克金、金克木
        overcomes = {
            Element.WOOD: Element.EARTH,
            Element.EARTH: Element.WATER,
            Element.WATER: Element.FIRE,
            Element.FIRE: Element.METAL,
            Element.METAL: Element.WOOD,
        }

        for me in Element:
            for other in Element:
                if me == other:
                    # 同我者为兄弟
                    cls._RELATION_MAP[(me, other)] = SixRelation.BROTHER
                elif generates.get(me) == other:
                    # 我生者为子孙
                    cls._RELATION_MAP[(me, other)] = SixRelation.CHILDREN
                elif generates.get(other) == me:
                    # 生我者为父母
                    cls._RELATION_MAP[(me, other)] = SixRelation.PARENT
                elif overcomes.get(me) == other:
                    # 我克者为妻财
                    cls._RELATION_MAP[(me, other)] = SixRelation.WEALTH
                elif overcomes.get(other) == me:
                    # 克我者为官鬼
                    cls._RELATION_MAP[(me, other)] = SixRelation.OFFICIAL

    @classmethod
    def assign(
        cls,
        hexagram_element: Element,
        line_elements: list[Element],
    ) -> list[SixRelation]:
        """为各爻分配六亲

        Args:
            hexagram_element: 卦的五行属性
            line_elements: 各爻的五行属性列表（6个）

        Returns:
            六亲关系列表（6个）

        Raises:
            ValueError: 如果爻的数量不是6个
        """
        if len(line_elements) != 6:
            raise ValueError(
                f"需要6个爻的五行属性，实际得到{len(line_elements)}个"
            )

        cls._build_relation_map()

        relations = []
        for elem in line_elements:
            relation = cls._RELATION_MAP.get((hexagram_element, elem))
            if relation is None:
                raise ValueError(
                    f"无法推导六亲关系：卦五行={hexagram_element}, 爻五行={elem}"
                )
            relations.append(relation)

        return relations

    @classmethod
    def get_relation(
        cls, source: Element, target: Element
    ) -> SixRelation:
        """获取两个五行之间的六亲关系

        Args:
            source: 源五行（我）
            target: 目标五行（对方）

        Returns:
            六亲关系

        Raises:
            ValueError: 如果无法推导关系
        """
        cls._build_relation_map()
        relation = cls._RELATION_MAP.get((source, target))
        if relation is None:
            raise ValueError(
                f"无法推导六亲关系：source={source}, target={target}"
            )
        return relation
