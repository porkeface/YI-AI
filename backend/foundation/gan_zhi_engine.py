"""干支纳甲引擎模块

实现天干地支基础数据、干支组合（60甲子）和纳甲规则。
"""

from __future__ import annotations

import sxtwl

from foundation.types import TrigramName


class GanZhiEngine:
    """干支纳甲引擎

    提供干支组合查询和纳甲规则功能。
    """

    _DATA_LOADED: bool = False

    # 10天干
    STEMS: list[str] = [
        "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"
    ]

    # 12地支
    BRANCHES: list[str] = [
        "子", "丑", "寅", "卯", "辰", "巳",
        "午", "未", "申", "酉", "戌", "亥"
    ]

    # 60甲子表
    _JIAZI_TABLE: list[str] = []

    @classmethod
    def _build_jiazi_table(cls) -> None:
        """构建60甲子表"""
        if cls._JIAZI_TABLE:
            return
        for i in range(60):
            stem = cls.STEMS[i % 10]
            branch = cls.BRANCHES[i % 12]
            cls._JIAZI_TABLE.append(f"{stem}{branch}")

    # 纳甲规则：每个卦的六爻干支
    # 根据京房易纳甲法
    # 格式：卦名 -> [初爻干支, 二爻干支, 三爻干支, 四爻干支, 五爻干支, 六爻干支]
    NAJIA_RULES: dict[TrigramName, list[str]] = {
        # 乾卦纳甲壬，外卦壬，内卦甲
        TrigramName.QIAN: [
            "甲子", "甲寅", "甲辰", "壬午", "壬申", "壬戌"
        ],
        # 坤卦纳乙癸，外卦癸，内卦乙
        TrigramName.KUN: [
            "乙未", "乙巳", "乙卯", "癸丑", "癸亥", "癸酉"
        ],
        # 震卦纳庚
        TrigramName.ZHEN: [
            "庚子", "庚寅", "庚辰", "庚午", "庚申", "庚戌"
        ],
        # 巽卦纳辛
        TrigramName.XUN: [
            "辛丑", "辛亥", "辛酉", "辛未", "辛巳", "辛卯"
        ],
        # 坎卦纳戊
        TrigramName.KAN: [
            "戊寅", "戊辰", "戊午", "戊申", "戊戌", "戊子"
        ],
        # 离卦纳己
        TrigramName.LI: [
            "己卯", "己丑", "己亥", "己酉", "己未", "己巳"
        ],
        # 艮卦纳丙
        TrigramName.GEN: [
            "丙辰", "丙午", "丙申", "丙戌", "丙子", "丙寅"
        ],
        # 兑卦纳丁
        TrigramName.DUI: [
            "丁巳", "丁卯", "丁丑", "丁亥", "丁酉", "丁未"
        ],
    }

    @classmethod
    def _ensure_data_loaded(cls) -> None:
        """从JSON数据文件加载纳甲规则（懒加载）

        成功加载后覆盖硬编码的 NAJIA_RULES，失败时保留硬编码数据。
        """
        if cls._DATA_LOADED:
            return
        try:
            from foundation.reference_data import get_najia_rules

            rules_list = get_najia_rules()
            if rules_list:
                najia: dict[TrigramName, list[str]] = {}
                for rule in rules_list:
                    trigram = TrigramName(rule["trigram"])
                    position = rule["position"]
                    gz = rule["heavenly_stem"] + rule["earthly_branch"]
                    if trigram not in najia:
                        najia[trigram] = [""] * 6
                    najia[trigram][position - 1] = gz
                if najia:
                    cls.NAJIA_RULES = najia
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("纳甲JSON加载失败，使用硬编码数据: %s", e)
        cls._DATA_LOADED = True

    @classmethod
    def get_gan_zhi(cls, stem: str, branch: str) -> str:
        """组合天干地支

        Args:
            stem: 天干
            branch: 地支

        Returns:
            干支字符串

        Raises:
            ValueError: 如果天干或地支无效
        """
        if stem not in cls.STEMS:
            raise ValueError(f"无效的天干：{stem}")
        if branch not in cls.BRANCHES:
            raise ValueError(f"无效的地支：{branch}")
        return f"{stem}{branch}"

    @classmethod
    def get_najia(cls, hexagram_name: str) -> list[str]:
        """获取卦的纳甲干支

        Args:
            hexagram_name: 卦名

        Returns:
            6个爻的干支列表（从初爻到六爻）

        Raises:
            ValueError: 如果卦名无效
        """
        cls._ensure_data_loaded()

        # 解析卦名，获取上卦和下卦
        # 卦名格式如"乾为天"、"坤为地"、"水雷屯"等
        upper_name, lower_name = cls._parse_hexagram_name(hexagram_name)

        # 获取下卦（内卦）的纳甲
        lower_najia = cls.NAJIA_RULES.get(lower_name)
        if lower_najia is None:
            raise ValueError(f"未找到卦的纳甲规则：{lower_name}")

        # 获取上卦（外卦）的纳甲
        upper_najia = cls.NAJIA_RULES.get(upper_name)
        if upper_najia is None:
            raise ValueError(f"未找到卦的纳甲规则：{upper_name}")

        # 组合：下卦3爻 + 上卦3爻
        return lower_najia[:3] + upper_najia[3:]

    @classmethod
    def _parse_hexagram_name(
        cls, name: str
    ) -> tuple[TrigramName, TrigramName]:
        """解析卦名，获取上卦和下卦

        Args:
            name: 卦名

        Returns:
            (上卦名, 下卦名)

        Raises:
            ValueError: 如果卦名格式无效
        """
        # 特殊情况：八纯卦
        pure_map = {
            "乾为天": (TrigramName.QIAN, TrigramName.QIAN),
            "坤为地": (TrigramName.KUN, TrigramName.KUN),
            "震为雷": (TrigramName.ZHEN, TrigramName.ZHEN),
            "巽为风": (TrigramName.XUN, TrigramName.XUN),
            "坎为水": (TrigramName.KAN, TrigramName.KAN),
            "离为火": (TrigramName.LI, TrigramName.LI),
            "艮为山": (TrigramName.GEN, TrigramName.GEN),
            "兑为泽": (TrigramName.DUI, TrigramName.DUI),
        }
        if name in pure_map:
            return pure_map[name]

        # 一般情况：前两个字是上卦，后两个字是下卦（但实际是前2后2，中间2字是卦名）
        # 如"水雷屯"：上卦=坎(水)，下卦=震(雷)
        # 需要从自然象反推卦名
        nature_to_trigram = {
            "天": TrigramName.QIAN,
            "地": TrigramName.KUN,
            "雷": TrigramName.ZHEN,
            "风": TrigramName.XUN,
            "水": TrigramName.KAN,
            "火": TrigramName.LI,
            "山": TrigramName.GEN,
            "泽": TrigramName.DUI,
        }

        # 单字卦名（八纯卦）：乾、坤、震、巽、坎、离、艮、兑
        single_to_trigram = {
            "乾": TrigramName.QIAN,
            "坤": TrigramName.KUN,
            "震": TrigramName.ZHEN,
            "巽": TrigramName.XUN,
            "坎": TrigramName.KAN,
            "离": TrigramName.LI,
            "艮": TrigramName.GEN,
            "兑": TrigramName.DUI,
        }
        if len(name) == 1 and name in single_to_trigram:
            t = single_to_trigram[name]
            return (t, t)

        if len(name) >= 3:
            upper_nature = name[0]
            lower_nature = name[1]
            upper = nature_to_trigram.get(upper_nature)
            lower = nature_to_trigram.get(lower_nature)
            if upper is not None and lower is not None:
                return (upper, lower)

        raise ValueError(f"无法解析卦名：{name}")

    @staticmethod
    def _hour_to_branch_idx(hour: int) -> int:
        """将24小时制转换为地支索引（子时=0开始）

        Args:
            hour: 0-23小时

        Returns:
            地支索引 0-11
        """
        return ((hour + 1) // 2) % 12

    @classmethod
    def time_to_gan_zhi(
        cls, year: int, month: int, day: int, hour: int
    ) -> dict[str, str]:
        """时间转干支（使用sxtwl天文历算库）

        自动处理立春换年、节气换月等边界。

        Args:
            year: 年份（公历）
            month: 月份（1-12）
            day: 日期（1-31）
            hour: 时辰（0-23）

        Returns:
            包含年干支、月干支、日干支、时干支的字典
        """
        day_info = sxtwl.fromSolar(year, month, day)

        year_gz = day_info.getYearGZ()
        month_gz = day_info.getMonthGZ()
        day_gz = day_info.getDayGZ()

        # 时干支：根据日干推算时干（五鼠遁元法）
        hour_branch_idx = cls._hour_to_branch_idx(hour)
        hour_stem_idx = (day_gz.tg * 2 + hour_branch_idx) % 10

        return {
            "year": f"{cls.STEMS[year_gz.tg]}{cls.BRANCHES[year_gz.dz]}",
            "month": f"{cls.STEMS[month_gz.tg]}{cls.BRANCHES[month_gz.dz]}",
            "day": f"{cls.STEMS[day_gz.tg]}{cls.BRANCHES[day_gz.dz]}",
            "hour": f"{cls.STEMS[hour_stem_idx]}{cls.BRANCHES[hour_branch_idx]}",
        }

    @classmethod
    def get_jiazi_table(cls) -> list[str]:
        """获取60甲子表

        Returns:
            60甲子列表
        """
        cls._build_jiazi_table()
        return cls._JIAZI_TABLE.copy()
