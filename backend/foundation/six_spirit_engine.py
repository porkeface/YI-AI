"""六神引擎模块

实现根据日干排列六神的功能。
六神顺序：青龙、朱雀、勾陈、螣蛇、白虎、玄武
甲乙日起青龙，丙丁日起朱雀，戊日起勾陈，己日起螣蛇，庚辛日起白虎，壬癸日起玄武
"""

from __future__ import annotations

from foundation.types import SixSpirit


class SixSpiritEngine:
    """六神引擎

    根据日干排列六神。
    """

    _DATA_LOADED: bool = False

    # 六神顺序（固定）
    SPIRIT_ORDER: list[SixSpirit] = [
        SixSpirit.QINGLONG,  # 青龙
        SixSpirit.ZHUQUE,    # 朱雀
        SixSpirit.GOUCHEN,   # 勾陈
        SixSpirit.TENGHE,    # 螣蛇
        SixSpirit.BAIHU,     # 白虎
        SixSpirit.XUANWU,    # 玄武
    ]

    # 日干到起始六神的映射
    _STEM_TO_SPIRIT: dict[str, SixSpirit] = {
        "甲": SixSpirit.QINGLONG,  # 甲乙日起青龙
        "乙": SixSpirit.QINGLONG,
        "丙": SixSpirit.ZHUQUE,    # 丙丁日起朱雀
        "丁": SixSpirit.ZHUQUE,
        "戊": SixSpirit.GOUCHEN,   # 戊日起勾陈
        "己": SixSpirit.TENGHE,    # 己日起螣蛇
        "庚": SixSpirit.BAIHU,     # 庚辛日起白虎
        "辛": SixSpirit.BAIHU,
        "壬": SixSpirit.XUANWU,    # 壬癸日起玄武
        "癸": SixSpirit.XUANWU,
    }

    @classmethod
    def _ensure_data_loaded(cls) -> None:
        """从JSON数据文件加载六神映射（懒加载）

        成功加载后覆盖硬编码的 _STEM_TO_SPIRIT，失败时保留硬编码数据。
        """
        if cls._DATA_LOADED:
            return
        try:
            from foundation.reference_data import get_six_spirit_rules

            rules_list = get_six_spirit_rules()
            if rules_list:
                stem_to_spirit: dict[str, SixSpirit] = {}
                for rule in rules_list:
                    if rule["line_position"] == 1:
                        stem = rule["day_stem"]
                        spirit = SixSpirit(rule["spirit"])
                        stem_to_spirit[stem] = spirit
                if stem_to_spirit:
                    cls._STEM_TO_SPIRIT = stem_to_spirit
        except Exception:
            pass  # fall back to hardcoded
        cls._DATA_LOADED = True

    @classmethod
    def assign(cls, day_stem: str) -> list[SixSpirit]:
        """根据日干分配六神

        Args:
            day_stem: 日干（如"甲"、"乙"等）

        Returns:
            6个爻的六神列表（从初爻到六爻）

        Raises:
            ValueError: 如果日干无效
        """
        cls._ensure_data_loaded()
        start_spirit = cls._STEM_TO_SPIRIT.get(day_stem)
        if start_spirit is None:
            raise ValueError(f"无效的日干：{day_stem}")

        # 找到起始六神的索引
        start_idx = cls.SPIRIT_ORDER.index(start_spirit)

        # 按顺序分配六神
        spirits = []
        for i in range(6):
            idx = (start_idx + i) % 6
            spirits.append(cls.SPIRIT_ORDER[idx])

        return spirits

    @classmethod
    def get_spirit_for_position(
        cls, day_stem: str, position: int
    ) -> SixSpirit:
        """获取指定位置的六神

        Args:
            day_stem: 日干
            position: 爻的位置（1-6）

        Returns:
            六神

        Raises:
            ValueError: 如果日干或位置无效
        """
        if not 1 <= position <= 6:
            raise ValueError(f"爻位置必须在1-6之间，实际为{position}")

        spirits = cls.assign(day_stem)
        return spirits[position - 1]
