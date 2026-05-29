"""卦引擎模块

实现六爻卦的创建、变卦、错卦、综卦、互卦等核心功能。
"""

from __future__ import annotations

from foundation.types import (
    Element,
    Hexagram,
    Line,
    SixRelation,
    SixSpirit,
    Trigram,
    TrigramName,
    YinYang,
)
from foundation.trigram_engine import TrigramEngine
from foundation.data.hexagram_data import HEXAGRAM_DATA


class HexagramEngine:
    """卦引擎

    提供六爻卦的创建和变换功能。
    """

    # 名称到数据的索引
    _NAME_INDEX: dict[str, int] = {}
    # ID到数据的索引
    _ID_INDEX: dict[int, int] = {}
    # 二进制到数据的索引
    _BINARY_INDEX: dict[str, int] = {}

    @classmethod
    def _build_indexes(cls) -> None:
        """构建索引（懒加载）"""
        if cls._NAME_INDEX:
            return
        for idx, data in enumerate(HEXAGRAM_DATA):
            hex_id, name, _, _, binary, _, _, _ = data
            cls._NAME_INDEX[name] = idx
            cls._ID_INDEX[hex_id] = idx
            cls._BINARY_INDEX[binary] = idx

    @classmethod
    def _create_default_lines(
        cls,
        upper: Trigram,
        lower: Trigram,
    ) -> tuple[Line, Line, Line, Line, Line, Line]:
        """创建默认爻数据（无动爻、无六亲六神等）

        Args:
            upper: 上卦
            lower: 下卦

        Returns:
            6个爻的元组
        """
        binary = lower.binary_rep + upper.binary_rep
        default_line = Line(
            position=1,
            yin_yang=YinYang.YANG,
            is_moving=False,
            element=Element.METAL,
            six_relation=SixRelation.BROTHER,
            six_spirit=SixSpirit.QINGLONG,
            gan_zhi="甲子",
            is_shi=False,
            is_ying=False,
        )
        lines = []
        for i, bit in enumerate(binary):
            yin_yang = YinYang.YANG if bit == "1" else YinYang.YIN
            lines.append(Line(
                position=i + 1,
                yin_yang=yin_yang,
                is_moving=False,
                element=default_line.element,
                six_relation=default_line.six_relation,
                six_spirit=default_line.six_spirit,
                gan_zhi=default_line.gan_zhi,
                is_shi=False,
                is_ying=False,
            ))
        return tuple(lines)  # type: ignore[return-value]

    @classmethod
    def create(cls, lines: list[YinYang]) -> Hexagram:
        """从阴阳序列创建卦

        Args:
            lines: 6个阴阳值的列表（从下到上）

        Returns:
            卦对象

        Raises:
            ValueError: 如果不是6个爻
        """
        if len(lines) != 6:
            raise ValueError(f"需要6个爻，实际得到{len(lines)}个")

        # 构建二进制表示
        binary = "".join(
            "1" if y == YinYang.YANG else "0" for y in lines
        )

        # 获取上下卦
        lower_binary = binary[:3]
        upper_binary = binary[3:]
        lower = TrigramEngine.get_by_binary(lower_binary)
        upper = TrigramEngine.get_by_binary(upper_binary)

        # 查找卦数据
        cls._build_indexes()
        idx = cls._BINARY_INDEX.get(binary)
        if idx is not None:
            data = HEXAGRAM_DATA[idx]
            hex_id, name, _, _, _, element, judgment, image = data
        else:
            # 理论上不应该发生，因为64卦覆盖了所有组合
            hex_id = 0
            name = f"{upper.name.value}{lower.name.value}"
            element = upper.element
            judgment = ""
            image = ""

        # 创建爻数据
        hex_lines = cls._create_default_lines(upper, lower)

        return Hexagram(
            id=hex_id,
            name=name,
            upper_trigram=upper,
            lower_trigram=lower,
            lines=hex_lines,
            element=element,
            judgment=judgment,
            image=image,
        )

    @classmethod
    def get_changed(
        cls, hexagram: Hexagram, moving_lines: tuple[int, ...]
    ) -> Hexagram:
        """计算变卦

        Args:
            hexagram: 原卦
            moving_lines: 动爻位置（1-6）

        Returns:
            变卦

        Raises:
            ValueError: 如果动爻位置无效
        """
        for pos in moving_lines:
            if not 1 <= pos <= 6:
                raise ValueError(f"动爻位置必须在1-6之间，实际为{pos}")

        # 翻转动爻
        new_yin_yangs = []
        for i, line in enumerate(hexagram.lines):
            pos = i + 1
            if pos in moving_lines:
                # 翻转阴阳
                if line.yin_yang == YinYang.YANG:
                    new_yin_yangs.append(YinYang.YIN)
                else:
                    new_yin_yangs.append(YinYang.YANG)
            else:
                new_yin_yangs.append(line.yin_yang)

        return cls.create(new_yin_yangs)

    @classmethod
    def get_opposite(cls, hexagram: Hexagram) -> Hexagram:
        """计算错卦（所有爻取反）

        Args:
            hexagram: 原卦

        Returns:
            错卦
        """
        new_yin_yangs = []
        for line in hexagram.lines:
            if line.yin_yang == YinYang.YANG:
                new_yin_yangs.append(YinYang.YIN)
            else:
                new_yin_yangs.append(YinYang.YANG)
        return cls.create(new_yin_yangs)

    @classmethod
    def get_reversed(cls, hexagram: Hexagram) -> Hexagram:
        """计算综卦（爻序颠倒）

        Args:
            hexagram: 原卦

        Returns:
            综卦
        """
        new_yin_yangs = [
            line.yin_yang for line in reversed(hexagram.lines)
        ]
        return cls.create(new_yin_yangs)

    @classmethod
    def get_interlock(cls, hexagram: Hexagram) -> Hexagram:
        """计算互卦（2-4爻为下卦，3-5爻为上卦）

        Args:
            hexagram: 原卦

        Returns:
            互卦
        """
        # 2-4爻为下卦，3-5爻为上卦
        lower_yin_yangs = [
            hexagram.lines[1].yin_yang,  # 第2爻
            hexagram.lines[2].yin_yang,  # 第3爻
            hexagram.lines[3].yin_yang,  # 第4爻
        ]
        upper_yin_yangs = [
            hexagram.lines[2].yin_yang,  # 第3爻
            hexagram.lines[3].yin_yang,  # 第4爻
            hexagram.lines[4].yin_yang,  # 第5爻
        ]
        return cls.create(lower_yin_yangs + upper_yin_yangs)

    @classmethod
    def get_by_id(cls, hex_id: int) -> Hexagram:
        """按ID查卦

        Args:
            hex_id: 卦序号（1-64）

        Returns:
            卦对象

        Raises:
            ValueError: 如果ID无效
        """
        cls._build_indexes()
        idx = cls._ID_INDEX.get(hex_id)
        if idx is None:
            raise ValueError(f"无效的卦ID：{hex_id}")
        return cls._create_from_data(HEXAGRAM_DATA[idx])

    @classmethod
    def get_by_name(cls, name: str) -> Hexagram:
        """按名查卦

        Args:
            name: 卦名（如"乾为天"）

        Returns:
            卦对象

        Raises:
            ValueError: 如果卦名无效
        """
        cls._build_indexes()
        idx = cls._NAME_INDEX.get(name)
        if idx is None:
            raise ValueError(f"无效的卦名：{name}")
        return cls._create_from_data(HEXAGRAM_DATA[idx])

    @classmethod
    def _create_from_data(cls, data: tuple) -> Hexagram:
        """从静态数据创建卦对象

        Args:
            data: 卦数据元组

        Returns:
            卦对象
        """
        hex_id, name, upper_name, lower_name, binary, element, judgment, image = data
        upper = TrigramEngine.get_by_name(upper_name)
        lower = TrigramEngine.get_by_name(lower_name)
        lines = cls._create_default_lines(upper, lower)
        return Hexagram(
            id=hex_id,
            name=name,
            upper_trigram=upper,
            lower_trigram=lower,
            lines=lines,
            element=element,
            judgment=judgment,
            image=image,
        )

    @classmethod
    def get_all_hexagrams(cls) -> list[Hexagram]:
        """获取所有64卦

        Returns:
            64卦列表
        """
        return [cls._create_from_data(data) for data in HEXAGRAM_DATA]
