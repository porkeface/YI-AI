"""八卦引擎模块

实现八卦基础数据和查询功能。
八卦：乾、兑、离、震、巽、坎、艮、坤
"""

from __future__ import annotations

from foundation.types import Element, Trigram, TrigramName


class TrigramEngine:
    """八卦引擎

    提供八卦数据查询功能，包括名称、二进制、五行、自然象等。
    """

    # 八卦完整数据
    _TRIGRAMS: dict[TrigramName, Trigram] = {
        TrigramName.QIAN: Trigram(
            name=TrigramName.QIAN,
            binary_rep="111",
            element=Element.METAL,
            nature="天",
            direction="西北",
            family="父",
            body="头",
            animal="马",
        ),
        TrigramName.DUI: Trigram(
            name=TrigramName.DUI,
            binary_rep="110",
            element=Element.METAL,
            nature="泽",
            direction="西",
            family="少女",
            body="口",
            animal="羊",
        ),
        TrigramName.LI: Trigram(
            name=TrigramName.LI,
            binary_rep="101",
            element=Element.FIRE,
            nature="火",
            direction="南",
            family="中女",
            body="目",
            animal="雉",
        ),
        TrigramName.ZHEN: Trigram(
            name=TrigramName.ZHEN,
            binary_rep="100",
            element=Element.WOOD,
            nature="雷",
            direction="东",
            family="长男",
            body="足",
            animal="龙",
        ),
        TrigramName.XUN: Trigram(
            name=TrigramName.XUN,
            binary_rep="011",
            element=Element.WOOD,
            nature="风",
            direction="东南",
            family="长女",
            body="股",
            animal="鸡",
        ),
        TrigramName.KAN: Trigram(
            name=TrigramName.KAN,
            binary_rep="010",
            element=Element.WATER,
            nature="水",
            direction="北",
            family="中男",
            body="耳",
            animal="豕",
        ),
        TrigramName.GEN: Trigram(
            name=TrigramName.GEN,
            binary_rep="001",
            element=Element.EARTH,
            nature="山",
            direction="东北",
            family="少男",
            body="手",
            animal="狗",
        ),
        TrigramName.KUN: Trigram(
            name=TrigramName.KUN,
            binary_rep="000",
            element=Element.EARTH,
            nature="地",
            direction="西南",
            family="母",
            body="腹",
            animal="牛",
        ),
    }

    # 二进制到卦名的映射
    _BINARY_MAP: dict[str, TrigramName] = {
        trigram.binary_rep: name
        for name, trigram in _TRIGRAMS.items()
    }

    @classmethod
    def get_by_name(cls, name: str | TrigramName) -> Trigram:
        """根据卦名获取八卦数据

        Args:
            name: 卦名（字符串或TrigramName枚举）

        Returns:
            八卦数据

        Raises:
            ValueError: 如果卦名无效
        """
        if isinstance(name, str):
            # 尝试从字符串查找对应的TrigramName
            for trigram_name in TrigramName:
                if trigram_name.value == name:
                    name = trigram_name
                    break
            else:
                raise ValueError(f"无效的卦名：{name}")

        trigram = cls._TRIGRAMS.get(name)
        if trigram is None:
            raise ValueError(f"未找到卦：{name}")
        return trigram

    @classmethod
    def get_by_binary(cls, binary: str) -> Trigram:
        """根据二进制表示获取八卦数据

        Args:
            binary: 3位二进制字符串（从下到上），如"111"

        Returns:
            八卦数据

        Raises:
            ValueError: 如果二进制表示无效
        """
        name = cls._BINARY_MAP.get(binary)
        if name is None:
            raise ValueError(f"无效的二进制表示：{binary}")
        return cls._TRIGRAMS[name]

    @classmethod
    def get_element(cls, name: str | TrigramName) -> Element:
        """获取八卦的五行属性

        Args:
            name: 卦名

        Returns:
            五行属性
        """
        trigram = cls.get_by_name(name)
        return trigram.element

    @classmethod
    def get_all_trigrams(cls) -> list[Trigram]:
        """获取所有八卦数据

        Returns:
            八卦数据列表
        """
        return list(cls._TRIGRAMS.values())
