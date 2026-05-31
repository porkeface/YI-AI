"""紫微斗数引擎模块

实现紫微斗数命盘排盘和分析功能：定命宫、身宫、五行局、安星、四化、亮度、分析。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import ceil
from typing import Any

from lunardate import LunarDate

from foundation.types import Verdict


# ---- 枚举类型 ----

class ZWStar(str, Enum):
    """十四主星"""
    ZIWEI = "紫微"
    TIANJI = "天机"
    TAIYANG = "太阳"
    WUQU = "武曲"
    TIANFU = "天府"
    TAIYIN = "太阴"
    TANLANG = "贪狼"
    JUMEN = "巨门"
    TIANXIANG = "天相"
    TIANLIANG = "天梁"
    QISHA = "七杀"
    POJUN = "破军"
    LIANZHEN = "廉贞"
    TIANTONG = "天同"


class ZWAuxStar(str, Enum):
    """辅星"""
    WENQU = "文昌"
    WENQU2 = "文曲"
    ZUOFU = "左辅"
    YOUBI = "右弼"
    TIANKUI = "天魁"
    TIANYUE = "天钺"
    LUCUN = "禄存"
    QINGYANG = "擎羊"
    TUOLUO = "陀罗"
    HUOXING = "火星"
    LINGXING = "铃星"
    DIKONG = "地空"
    DIJIE = "地劫"


class ZWHua(str, Enum):
    """四化"""
    HUA_LU = "化禄"
    HUA_QUAN = "化权"
    HUA_KE = "化科"
    HUA_JI = "化忌"


class ZWPalace(str, Enum):
    """十二宫"""
    MING = "命宫"
    XIONGDI = "兄弟"
    FUQI = "夫妻"
    ZINV = "子女"
    CAIBO = "财帛"
    JIBING = "疾厄"
    QIANYI = "迁移"
    NUPU = "奴仆"
    GUANLU = "官禄"
    TIANZHAI = "田宅"
    FUDE = "福德"
    FUMU = "父母"


class ZWPalaceType(str, Enum):
    """宫位类型"""
    BENGONG = "本宫"
    DUIGONG = "对宫"
    SANFANG = "三方"


# ---- 数据结构 ----

@dataclass(frozen=True)
class ZWStarPosition:
    """星曜在某宫的位置"""
    star: ZWStar
    palace: ZWPalace
    brightness: str
    hua: ZWHua | None


@dataclass(frozen=True)
class ZWPalaceInfo:
    """一宫的完整信息"""
    palace: ZWPalace
    gan_zhi: str
    main_stars: tuple[ZWStar, ...]
    aux_stars: tuple[ZWAuxStar, ...]
    brightness: tuple[str, ...]
    hua_stars: tuple[ZWHua, ...]
    is_body_palace: bool


@dataclass(frozen=True)
class ZWChart:
    """紫微斗数完整命盘"""
    palaces: tuple[ZWPalaceInfo, ...]
    year_gan_zhi: str
    month_gan_zhi: str
    day_gan_zhi: str
    hour_gan_zhi: str
    gender: str
    wu_xing_ju: int
    ming_palace: ZWPalace
    shen_palace: ZWPalace


@dataclass(frozen=True)
class ZWAnalysis:
    """紫微命盘分析结果"""
    target_palace: ZWPalace
    main_stars: tuple[ZWStar, ...]
    hua_influence: tuple[ZWHua, ...]
    description: str
    verdict: Verdict


# ---- 引擎 ----

class ZiWeiEngine:
    """紫微斗数引擎，所有方法为 classmethod，无需实例化。"""

    BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
    STEMS = "甲乙丙丁戊己庚辛壬癸"
    _PALACE_NAMES = ("命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
                     "迁移", "奴仆", "官禄", "田宅", "福德", "父母")

    # 十四主星亮度表（子丑寅卯辰巳午未申酉戌亥）
    _BRIGHTNESS: dict[str, tuple[str, ...]] = {
        "紫微": ("平","旺","庙","旺","庙","平","旺","庙","旺","得","庙","陷"),
        "天机": ("旺","陷","庙","旺","平","庙","平","旺","陷","旺","庙","平"),
        "太阳": ("陷","不","庙","旺","旺","旺","庙","平","平","陷","陷","不"),
        "武曲": ("旺","庙","旺","庙","平","庙","陷","平","庙","旺","平","陷"),
        "天府": ("庙","旺","庙","得","庙","旺","庙","得","庙","旺","庙","得"),
        "太阴": ("庙","旺","陷","旺","庙","旺","陷","旺","庙","旺","庙","陷"),
        "贪狼": ("旺","庙","陷","平","庙","旺","庙","陷","平","旺","陷","庙"),
        "巨门": ("旺","庙","庙","旺","庙","旺","陷","庙","庙","旺","陷","庙"),
        "天相": ("庙","旺","庙","陷","庙","旺","庙","陷","庙","旺","庙","陷"),
        "天梁": ("庙","旺","庙","旺","庙","陷","庙","旺","庙","旺","陷","庙"),
        "七杀": ("庙","平","庙","陷","庙","平","庙","陷","庙","平","庙","陷"),
        "破军": ("庙","旺","庙","陷","庙","旺","庙","陷","庙","旺","庙","陷"),
        "廉贞": ("平","庙","旺","庙","陷","平","庙","旺","庙","陷","平","庙"),
        "天同": ("庙","平","庙","旺","陷","庙","庙","旺","庙","旺","陷","庙"),
    }

    # 十干四化表（化禄, 化权, 化科, 化忌）
    _SIHUA: dict[str, tuple[str, str, str, str]] = {
        "甲": ("廉贞","破军","武曲","太阳"),
        "乙": ("天机","天梁","紫微","太阴"),
        "丙": ("天同","天机","文昌","廉贞"),
        "丁": ("太阴","天同","天机","巨门"),
        "戊": ("贪狼","太阴","右弼","天机"),
        "己": ("武曲","贪狼","天梁","文曲"),
        "庚": ("太阳","武曲","太阴","天同"),
        "辛": ("巨门","太阳","文曲","文昌"),
        "壬": ("天梁","紫微","左辅","武曲"),
        "癸": ("破军","巨门","太阴","贪狼"),
    }

    # 天魁天钺（年干→(魁索引, 钺索引)）
    _KUIYUE: dict[str, tuple[int, int]] = {
        "甲": (1,7), "乙": (0,8), "丙": (11,9), "丁": (11,9), "戊": (1,7),
        "己": (0,8), "庚": (1,7), "辛": (10,2), "壬": (3,5), "癸": (3,5),
    }

    # 禄存（年干→宫索引）
    _LUCUN: dict[str, int] = {
        "甲": 2, "乙": 3, "丙": 5, "丁": 6, "戊": 5,
        "己": 6, "庚": 8, "辛": 9, "壬": 11, "癸": 0,
    }

    # 火星铃星起始宫（年支分组→起始宫索引）
    _FIRE_START: dict[str, int] = {"寅午戌": 2, "申子辰": 8, "巳酉丑": 5, "亥卯未": 11}
    _BELL_START: dict[str, int] = {"寅午戌": 3, "申子辰": 9, "巳酉丑": 6, "亥卯未": 0}

    # 天府星系累计偏移
    _TIANFU_OFFSETS: tuple[int, ...] = (0, 1, 3, 6, 10, 15, 21, 24)

    # 纳音五行映射（构建后填充）
    _NAYIN: dict[tuple[int, int], int] = {}

    @classmethod
    def _build_nayin(cls) -> None:
        """构建六十甲子纳音五行映射表

        纳音五行局数：水二局=2, 木三局=3, 金四局=4, 土五局=5, 火六局=6
        每对相邻干支共享同一纳音。
        """
        if cls._NAYIN:
            return
        # 30对纳音的五行局数（甲子乙丑→海中金→4, ...）
        pair_ju = (
            4,6,3,5,4,6,2,5,4,3, 2,5,6,3,2,4,6,3,5,4,
            6,2,5,4,3,2,5,6,3,2,
        )
        for i in range(60):
            cls._NAYIN[(i % 10, i % 12)] = pair_ju[i // 2]

    # ---- 公共方法 ----

    @classmethod
    def generate_chart(
        cls, year: int, month: int, day: int, hour: int, gender: str,
    ) -> ZWChart:
        """排紫微斗数命盘

        Args:
            year: 出生年（公历）; month: 出生月（1-12）; day: 出生日
            hour: 出生时辰（0-23，23为子时）; gender: "男" 或 "女"
        """
        cls._build_nayin()
        stems = "甲乙丙丁戊己庚辛壬癸"
        branches = "子丑寅卯辰巳午未申酉戌亥"
        hour_zhi_idx = ((hour + 1) // 2) % 12

        # 公历转农历（紫微斗数排盘使用农历）
        lunar = LunarDate.fromSolarDate(year, month, day)
        lunar_year = lunar.year
        lunar_month = lunar.month
        lunar_day = lunar.day

        # 年干支（使用农历年，处理公历1-2月跨年情况）
        lunar_year_stem_idx = (lunar_year - 4) % 10
        lunar_year_branch_idx = (lunar_year - 4) % 12
        year_stem = stems[lunar_year_stem_idx]
        year_gan_zhi = f"{year_stem}{branches[lunar_year_branch_idx]}"

        # 月干支（使用农历月和农历年天干）
        month_branch_idx = (lunar_month + 1) % 12
        month_stem_idx = ((lunar_year_stem_idx % 5) * 2 + lunar_month - 1 + 2) % 10
        month_gan_zhi = f"{stems[month_stem_idx]}{branches[month_branch_idx]}"

        # 日干支
        y_adj = year - 1 if month <= 2 else year
        m_adj = month + 12 if month <= 2 else month
        jd = (day + 153 * (m_adj - 3) // 5 + 365 * y_adj
              + y_adj // 4 - y_adj // 100 + y_adj // 400 - 32045)
        day_stem_idx = (jd + 9) % 10
        day_branch_idx = (jd + 1) % 12
        day_gan_zhi = f"{stems[day_stem_idx]}{branches[day_branch_idx]}"

        # 时干支
        hour_stem_idx = ((day_stem_idx % 5) * 2 + hour_zhi_idx) % 10
        hour_gan_zhi = f"{stems[hour_stem_idx]}{branches[hour_zhi_idx]}"

        # 命宫、身宫（使用农历月）
        ming_idx = (2 + lunar_month - 1 - hour_zhi_idx) % 12
        shen_idx = (2 + lunar_month - 1 + hour_zhi_idx) % 12

        # 命宫天干→五行局
        ming_stem_idx = cls._palace_stem(lunar_year_stem_idx, ming_idx)
        ju = cls._NAYIN[(ming_stem_idx, ming_idx)]

        # 安主星：紫微位置 = 从寅起数 ceil(农历日/局) 步
        ziwei_pos = (ceil(lunar_day / ju) + 1) % 12
        all_main: dict[int, list[str]] = {}
        for pos, stars in cls._ziwei_stars(ziwei_pos).items():
            all_main.setdefault(pos, []).extend(stars)
        for pos, stars in cls._tianfu_stars(ziwei_pos).items():
            all_main.setdefault(pos, []).extend(stars)

        # 安辅星（左辅/右弼使用农历月）
        aux_map = cls._aux_stars(lunar_year_stem_idx, lunar_year_branch_idx, lunar_month, hour_zhi_idx)

        # 四化映射（星名→四化名）
        hua_names = ("化禄", "化权", "化科", "化忌")
        sihua = cls._SIHUA[year_stem]
        star_hua: dict[str, str] = {}
        for i, h_name in enumerate(hua_names):
            star_hua[sihua[i]] = h_name

        # 构建十二宫
        shen_offset = (shen_idx - ming_idx) % 12
        palaces: list[ZWPalaceInfo] = []
        for i, pname in enumerate(cls._PALACE_NAMES):
            bi = (ming_idx + i) % 12
            ps = cls._palace_stem(lunar_year_stem_idx, bi)
            ms_names = all_main.get(bi, [])
            ms = tuple(ZWStar(s) for s in ms_names)
            as_names = aux_map.get(bi, [])
            br = tuple(cls._BRIGHTNESS.get(s.value, ("平",)*12)[bi] for s in ms)
            h_list = [ZWHua(star_hua[n]) for n in ms_names if n in star_hua]
            palaces.append(ZWPalaceInfo(
                palace=ZWPalace(pname), gan_zhi=f"{stems[ps]}{branches[bi]}",
                main_stars=ms, aux_stars=tuple(ZWAuxStar(s) for s in as_names),
                brightness=br, hua_stars=tuple(h_list), is_body_palace=(i == shen_offset),
            ))

        return ZWChart(
            palaces=tuple(palaces), year_gan_zhi=year_gan_zhi,
            month_gan_zhi=month_gan_zhi, day_gan_zhi=day_gan_zhi,
            hour_gan_zhi=hour_gan_zhi, gender=gender, wu_xing_ju=ju,
            ming_palace=ZWPalace(cls._PALACE_NAMES[0]),
            shen_palace=ZWPalace(cls._PALACE_NAMES[shen_offset]),
        )

    @classmethod
    def analyze_chart(cls, chart: ZWChart, question_type: str = "general") -> ZWAnalysis:
        """分析紫微命盘

        Args:
            chart: 命盘; question_type: general/事业/财运/感情/健康/人际
        """
        type_map = {"事业": "官禄", "财运": "财帛", "感情": "夫妻", "健康": "疾厄", "人际": "奴仆"}
        target_name = type_map.get(question_type, "命宫")
        target_idx = cls._PALACE_NAMES.index(target_name)
        target = chart.palaces[target_idx]

        # 评分
        score = 60
        for br in target.brightness:
            if br in ("庙", "旺"):
                score += 8
            elif br in ("得", "利"):
                score += 4
            elif br in ("不", "陷"):
                score -= 8
        hua_list = list(target.hua_stars)
        for h in hua_list:
            score += {"化禄": 10, "化权": 8, "化科": 6, "化忌": -12}.get(h.value, 0)

        # 三方四正分析
        three_harmony = cls.analyze_three_harmony(chart, target_idx)
        score += three_harmony["total_score"]

        score = max(0, min(100, score))

        # 描述
        parts: list[str] = []
        if target.main_stars:
            parts.append(f"{target_name}主星为{'、'.join(s.value for s in target.main_stars)}")
        if hua_list:
            parts.append(f"有{'、'.join(h.value for h in hua_list)}入宫")
        overall = "吉" if score >= 60 else ("平" if score >= 40 else "凶")
        trend = "上升" if (ZWHua.HUA_LU in hua_list or ZWHua.HUA_KE in hua_list) \
            else ("下降" if ZWHua.HUA_JI in hua_list else "平稳")

        return ZWAnalysis(
            target_palace=target.palace, main_stars=target.main_stars,
            hua_influence=tuple(hua_list),
            description="；".join(parts) if parts else "该宫为空宫",
            verdict=Verdict(overall=overall, strength=score, trend=trend,
                          confidence=max(40, min(90, 50 + abs(score)))),
        )

    @classmethod
    def calculate_major_periods(
        cls, chart: ZWChart, num_periods: int = 8
    ) -> list[dict[str, Any]]:
        """计算大运（每10年一个大运）

        大运起法：
        1. 从命宫开始，阳男阴女顺行，阴男阳女逆行
        2. 每个大运10年
        3. 大运宫位的主星影响该10年运势

        Returns:
            大运列表，每个包含: period_num, start_age, end_age, palace_name,
            main_stars, brightness, transformations
        """
        ming_palace_idx = cls._PALACE_NAMES.index(chart.ming_palace.value)
        year_stem = chart.year_gan_zhi[0]

        # 判断阴阳：甲丙戊庚壬为阳，乙丁己辛癸为阴
        yang_stems = {"甲", "丙", "戊", "庚", "壬"}
        is_yang = year_stem in yang_stems
        is_male = chart.gender == "男"

        # 阳男阴女顺行，阴男阳女逆行
        direction = 1 if (is_yang == is_male) else -1

        periods = []
        current_age = 1

        for i in range(num_periods):
            palace_idx = (ming_palace_idx + i * direction) % 12
            palace_name = cls._PALACE_NAMES[palace_idx]
            palace = chart.palaces[palace_idx]

            # 该宫位的主星及亮度
            main_stars = []
            for j, star in enumerate(palace.main_stars):
                brightness = palace.brightness[j] if j < len(palace.brightness) else "平"
                main_stars.append({"star": star.value, "brightness": brightness})

            # 该大运的四化（用大运天干推算）
            period_stem_idx = (cls.STEMS.index(year_stem) + i) % 10
            period_stem = cls.STEMS[period_stem_idx]
            sihua = cls._SIHUA.get(period_stem, ())
            hua_names = ("化禄", "化权", "化科", "化忌")
            transformations = {
                hua_names[j]: sihua[j]
                for j in range(4) if j < len(sihua)
            } if sihua else {}

            periods.append({
                "period_num": i + 1,
                "start_age": current_age,
                "end_age": current_age + 9,
                "palace_name": palace_name,
                "palace_index": palace_idx,
                "main_stars": main_stars,
                "transformations": transformations,
            })
            current_age += 10

        return periods

    @classmethod
    def analyze_three_harmony(
        cls, chart: ZWChart, target_palace: int
    ) -> dict[str, Any]:
        """三方四正分析

        命宫三方：命宫 + 财帛宫 + 官禄宫
        四正：命宫 + 迁移宫（对宫）

        Args:
            target_palace: 目标宫位索引 (0-11)，对应 _PALACE_NAMES 的顺序

        Returns:
            三方四正分析结果
        """
        # 三方：target, target+4, target+8 (每隔4宫)
        three_harmony = [
            target_palace,
            (target_palace + 4) % 12,
            (target_palace + 8) % 12,
        ]
        # 四正：对宫
        opposite = (target_palace + 6) % 12
        four_square = three_harmony + [opposite]

        # 获取年干四化
        year_stem = chart.year_gan_zhi[0]
        sihua = cls._SIHUA.get(year_stem, ())
        hua_names = ("化禄", "化权", "化科", "化忌")
        sihua_map: dict[str, str] = {}
        if sihua:
            for j, h_name in enumerate(hua_names):
                if j < len(sihua):
                    sihua_map[sihua[j]] = h_name

        analysis: dict[str, Any] = {
            "target_palace": cls._PALACE_NAMES[target_palace],
            "three_harmony": [],
            "opposite_palace": cls._PALACE_NAMES[opposite],
            "total_score": 0,
        }

        for p_idx in four_square:
            palace_name = cls._PALACE_NAMES[p_idx]
            palace = chart.palaces[p_idx]

            stars = []
            for j, star in enumerate(palace.main_stars):
                brightness = palace.brightness[j] if j < len(palace.brightness) else "平"
                stars.append({"star": star.value, "brightness": brightness})

            # 计算该宫得分
            palace_score = 0
            for s in stars:
                br = s["brightness"]
                if br in ("庙", "旺"):
                    palace_score += 8
                elif br in ("得", "利"):
                    palace_score += 4
                elif br in ("不", "陷"):
                    palace_score -= 8

            # 四化加分
            for hua_star_name, hua_type in sihua_map.items():
                if any(s["star"] == hua_star_name for s in stars):
                    if hua_type == "化禄":
                        palace_score += 10
                    elif hua_type == "化权":
                        palace_score += 8
                    elif hua_type == "化科":
                        palace_score += 6
                    elif hua_type == "化忌":
                        palace_score -= 12

            analysis["three_harmony"].append({
                "palace": palace_name,
                "is_opposite": p_idx == opposite,
                "stars": stars,
                "score": palace_score,
            })
            analysis["total_score"] += palace_score

        return analysis

    # ---- 内部方法 ----

    @staticmethod
    def _palace_stem(year_stem_idx: int, branch_idx: int) -> int:
        """推算宫位天干序号

        五虎遁月法：寅宫天干 = (年干%5)*2 + 2，其余宫位按六十甲子排列。
        以寅(index=2)为基准，偏移量 = branch_idx - 2。
        """
        offset = (branch_idx - 2) % 12
        return ((year_stem_idx % 5) * 2 + 2 + offset) % 10

    @classmethod
    def _ziwei_stars(cls, ziwei_pos: int) -> dict[int, list[str]]:
        """安紫微星系6颗主星（天机-1, 太阳-3, 武曲-4, 天同-5, 廉贞+2）"""
        offsets = {"天机": -1, "太阳": -3, "武曲": -4, "天同": -5, "廉贞": 2}
        result: dict[int, list[str]] = {ziwei_pos: ["紫微"]}
        for name, off in offsets.items():
            pos = (ziwei_pos + off) % 12
            result.setdefault(pos, []).append(name)
        return result

    @classmethod
    def _tianfu_stars(cls, ziwei_pos: int) -> dict[int, list[str]]:
        """安天府星系8颗主星（天府=紫微+2，余按累计偏移顺行）"""
        tf = (ziwei_pos + 2) % 12
        names = ("天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军")
        result: dict[int, list[str]] = {}
        for i, name in enumerate(names):
            pos = (tf + cls._TIANFU_OFFSETS[i]) % 12
            result.setdefault(pos, []).append(name)
        return result

    @classmethod
    def _aux_stars(
        cls, year_stem_idx: int, year_branch_idx: int, month: int, hour_zhi_idx: int,
    ) -> dict[int, list[str]]:
        """安辅星，返回 {宫索引: [星名, ...]}"""
        r: dict[int, list[str]] = {}
        def _p(pos: int, name: str) -> None:
            r.setdefault(pos, []).append(name)
        stems = "甲乙丙丁戊己庚辛壬癸"
        branches = "子丑寅卯辰巳午未申酉戌亥"
        _p((5 - hour_zhi_idx) % 12, "文昌")       # 文昌: 辰起逆行
        _p((5 + hour_zhi_idx) % 12, "文曲")       # 文曲: 辰起顺行
        _p((5 + month - 1) % 12, "左辅")          # 左辅: 辰起顺数
        _p((11 - month + 1) % 12, "右弼")         # 右弼: 戌起逆行
        kui, yue = cls._KUIYUE[stems[year_stem_idx]]
        _p(kui, "天魁")
        _p(yue, "天钺")
        lu = cls._LUCUN[stems[year_stem_idx]]
        _p(lu, "禄存")
        _p((lu + 1) % 12, "擎羊")
        _p((lu - 1) % 12, "陀罗")
        for grp, start in cls._FIRE_START.items():
            if branches[year_branch_idx] in grp:
                _p((start + hour_zhi_idx) % 12, "火星"); break
        for grp, start in cls._BELL_START.items():
            if branches[year_branch_idx] in grp:
                _p((start + hour_zhi_idx) % 12, "铃星"); break
        _p((11 - hour_zhi_idx) % 12, "地空")      # 地空: 亥起逆行
        _p((11 + hour_zhi_idx) % 12, "地劫")      # 地劫: 亥起顺行
        return r
