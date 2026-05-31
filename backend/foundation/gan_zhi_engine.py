"""干支纳甲引擎模块

实现天干地支基础数据、干支组合（60甲子）和纳甲规则。
"""

from __future__ import annotations

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
        except Exception:
            pass  # fall back to hardcoded
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

        if len(name) >= 3:
            upper_nature = name[0]
            lower_nature = name[1]
            upper = nature_to_trigram.get(upper_nature)
            lower = nature_to_trigram.get(lower_nature)
            if upper is not None and lower is not None:
                return (upper, lower)

        raise ValueError(f"无法解析卦名：{name}")

    @classmethod
    def time_to_gan_zhi(
        cls, year: int, month: int, day: int, hour: int
    ) -> dict[str, str]:
        """时间转干支

        Args:
            year: 年份（公历）
            month: 月份（1-12）
            day: 日期（1-31）
            hour: 时辰（0-23）

        Returns:
            包含年干支、月干支、日干支、时干支的字典
        """
        cls._build_jiazi_table()

        # 年干支（以立春为界，简化处理）
        year_stem_idx = (year - 4) % 10
        year_branch_idx = (year - 4) % 12
        year_gz = f"{cls.STEMS[year_stem_idx]}{cls.BRANCHES[year_branch_idx]}"

        # 月干支（简化处理，实际需要考虑节气）
        # 月支：寅月(1月)开始
        month_branch_idx = (month + 1) % 12
        # 月干根据年干推算
        month_stem_base = (year_stem_idx % 5) * 2
        month_stem_idx = (month_stem_base + month - 1 + 2) % 10
        month_gz = f"{cls.STEMS[month_stem_idx]}{cls.BRANCHES[month_branch_idx]}"

        # 日干支（简化处理，实际需要查万年历）
        # 使用蔡勒公式的变体
        if month <= 2:
            year_adj = year - 1
            month_adj = month + 12
        else:
            year_adj = year
            month_adj = month
        day_julian = (
            day
            + 153 * (month_adj - 3) // 5
            + 365 * year_adj
            + year_adj // 4
            - year_adj // 100
            + year_adj // 400
            - 32045
        )
        day_stem_idx = (day_julian + 9) % 10
        day_branch_idx = (day_julian + 1) % 12
        day_gz = f"{cls.STEMS[day_stem_idx]}{cls.BRANCHES[day_branch_idx]}"

        # 时干支
        # 时支：子时(23-1)开始
        hour_branch_idx = ((hour + 1) // 2) % 12
        # 时干根据日干推算
        hour_stem_base = (day_stem_idx % 5) * 2
        hour_stem_idx = (hour_stem_base + hour_branch_idx) % 10
        hour_gz = f"{cls.STEMS[hour_stem_idx]}{cls.BRANCHES[hour_branch_idx]}"

        return {
            "year": year_gz,
            "month": month_gz,
            "day": day_gz,
            "hour": hour_gz,
        }

    @classmethod
    def get_jiazi_table(cls) -> list[str]:
        """获取60甲子表

        Returns:
            60甲子列表
        """
        cls._build_jiazi_table()
        return cls._JIAZI_TABLE.copy()
