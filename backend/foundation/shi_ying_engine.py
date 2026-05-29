"""世应引擎模块

实现根据卦宫确定世爻和应爻位置的功能。
基于京房易八宫卦序。
"""

from __future__ import annotations


class ShiYingEngine:
    """世应引擎

    根据卦宫确定世爻和应爻位置。
    八宫卦序（京房易）：
    - 本宫卦：世在六爻
    - 一世卦：世在初爻
    - 二世卦：世在二爻
    - 三世卦：世在三爻
    - 四世卦：世在四爻
    - 五世卦：世在五爻
    - 游魂卦：世在四爻
    - 归魂卦：世在三爻
    应爻位置 = 世爻位置 + 3（超过6则减6）
    """

    # 八宫卦序表
    # 格式：宫名 -> [本宫卦, 一世卦, 二世卦, 三世卦, 四世卦, 五世卦, 游魂卦, 归魂卦]
    PALACE_ORDER: dict[str, list[str]] = {
        "乾宫": [
            "乾为天", "天风姤", "天山遁", "天地否",
            "风地观", "山地剥", "火地晋", "火天大有",
        ],
        "坤宫": [
            "坤为地", "地雷复", "地泽临", "地天泰",
            "雷天大壮", "泽天夬", "水天需", "水地比",
        ],
        "震宫": [
            "震为雷", "雷地豫", "雷水解", "雷风恒",
            "地风升", "水风井", "泽风大过", "泽雷随",
        ],
        "巽宫": [
            "巽为风", "风天小畜", "风火家人", "风雷益",
            "天雷无妄", "火雷噬嗑", "山雷颐", "山风蛊",
        ],
        "坎宫": [
            "坎为水", "水泽节", "水雷屯", "水火既济",
            "泽火革", "雷火丰", "地火明夷", "地水师",
        ],
        "离宫": [
            "离为火", "火山旅", "火风鼎", "火水未济",
            "山水蒙", "风水涣", "天水讼", "天火同人",
        ],
        "艮宫": [
            "艮为山", "山火贲", "山天大畜", "山泽损",
            "火泽睽", "天泽履", "风泽中孚", "风山渐",
        ],
        "兑宫": [
            "兑为泽", "泽水困", "泽地萃", "泽山咸",
            "水山蹇", "地山谦", "雷山小过", "雷泽归妹",
        ],
    }

    # 卦名到宫位和位置的索引
    _HEXAGRAM_INDEX: dict[str, tuple[str, int]] = {}

    @classmethod
    def _build_index(cls) -> None:
        """构建索引"""
        if cls._HEXAGRAM_INDEX:
            return
        for palace, hexagrams in cls.PALACE_ORDER.items():
            for idx, name in enumerate(hexagrams):
                cls._HEXAGRAM_INDEX[name] = (palace, idx)

    @classmethod
    def get_shi_ying(cls, hexagram_id: int) -> tuple[int, int]:
        """获取世爻和应爻位置

        Args:
            hexagram_id: 卦序号（1-64）

        Returns:
            (世爻位, 应爻位)，位置为1-6

        Raises:
            ValueError: 如果卦ID无效
        """
        # 需要从ID转换为卦名
        # 这里需要依赖hexagram_data，但为了避免循环依赖，直接使用映射
        from foundation.data.hexagram_data import HEXAGRAM_DATA

        if hexagram_id < 1 or hexagram_id > 64:
            raise ValueError(f"卦ID必须在1-64之间，实际为{hexagram_id}")

        # 获取卦名
        hex_data = HEXAGRAM_DATA[hexagram_id - 1]
        hex_name = hex_data[1]

        return cls.get_shi_ying_by_name(hex_name)

    @classmethod
    def get_shi_ying_by_name(cls, hex_name: str) -> tuple[int, int]:
        """根据卦名获取世爻和应爻位置

        Args:
            hex_name: 卦名

        Returns:
            (世爻位, 应爻位)

        Raises:
            ValueError: 如果卦名无效
        """
        cls._build_index()

        index_info = cls._HEXAGRAM_INDEX.get(hex_name)
        if index_info is None:
            raise ValueError(f"未找到卦：{hex_name}")

        palace, position = index_info

        # 根据在宫中的位置确定世爻
        # 位置0: 本宫卦 -> 世在六爻
        # 位置1: 一世卦 -> 世在初爻
        # 位置2: 二世卦 -> 世在二爻
        # 位置3: 三世卦 -> 世在三爻
        # 位置4: 四世卦 -> 世在四爻
        # 位置5: 五世卦 -> 世在五爻
        # 位置6: 游魂卦 -> 世在四爻
        # 位置7: 归魂卦 -> 世在三爻
        if position == 0:
            shi = 6
        elif position <= 5:
            shi = position
        elif position == 6:  # 游魂卦
            shi = 4
        else:  # 归魂卦
            shi = 3

        # 应爻 = 世爻 + 3，超过6则减6
        ying = (shi + 3) if (shi + 3) <= 6 else (shi + 3 - 6)

        return (shi, ying)

    @classmethod
    def get_palace(cls, hex_name: str) -> str:
        """获取卦所属的宫

        Args:
            hex_name: 卦名

        Returns:
            宫名

        Raises:
            ValueError: 如果卦名无效
        """
        cls._build_index()

        index_info = cls._HEXAGRAM_INDEX.get(hex_name)
        if index_info is None:
            raise ValueError(f"未找到卦：{hex_name}")

        return index_info[0]

    @classmethod
    def get_palace_element(cls, hex_name: str) -> str:
        """获取卦宫的五行属性

        Args:
            hex_name: 卦名

        Returns:
            五行属性
        """
        palace = cls.get_palace(hex_name)

        # 宫与五行的对应
        palace_element = {
            "乾宫": "金",
            "坤宫": "土",
            "震宫": "木",
            "巽宫": "木",
            "坎宫": "水",
            "离宫": "火",
            "艮宫": "土",
            "兑宫": "金",
        }

        return palace_element.get(palace, "未知")
