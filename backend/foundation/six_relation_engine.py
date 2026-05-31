"""六亲引擎模块

实现六亲关系推导。
六亲关系：生我者为父母，克我者为官鬼，我克者为妻财，我生者为子孙，同我者为兄弟
"""

from __future__ import annotations

from foundation.types import Element, Hexagram, SixRelation


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

    # 地支顺序（用于计算卦身）
    _BRANCH_ORDER: list[str] = [
        "子", "丑", "寅", "卯", "辰", "巳",
        "午", "未", "申", "酉", "戌", "亥",
    ]

    @staticmethod
    def find_gua_shen(hexagram: Hexagram, month_branch: str) -> int | None:
        """计算卦身位置

        依据《火珠林》：
        "阳世则从子月起，阴世还当午月生，此即卦身也。"

        - 世爻为阳：从子起，数到月支，所得序数即为卦身爻位
        - 世爻为阴：从午起，数到月支，所得序数即为卦身爻位

        Args:
            hexagram: 卦对象
            month_branch: 月支（如"子"、"丑"等）

        Returns:
            卦身所在爻位（1-6），若无法确定则返回 None
        """
        branch_order = SixRelationEngine._BRANCH_ORDER

        if month_branch not in branch_order:
            return None

        # 找到世爻
        shi_line = None
        for line in hexagram.lines:
            if line.is_shi:
                shi_line = line
                break
        if shi_line is None:
            return None

        # 根据世爻阴阳确定起始地支
        from foundation.types import YinYang
        start_branch = "子" if shi_line.yin_yang == YinYang.YANG else "午"
        start_idx = branch_order.index(start_branch)
        month_idx = branch_order.index(month_branch)

        # 从起始地支数到月支，步数即为卦身爻位
        count = (month_idx - start_idx) % 12
        if count == 0:
            # 起始支与月支相同，卦身在第12位，取模后为0，映射到第6爻
            count = 12

        # 卦身爻位 = count，但爻位范围 1-6，超出则取模
        gua_shen_pos = count if count <= 6 else count % 6
        if gua_shen_pos == 0:
            gua_shen_pos = 6
        return gua_shen_pos
