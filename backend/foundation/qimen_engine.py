"""奇门遁甲引擎模块

实现奇门遁甲排盘核心逻辑，包括定局、排盘、分析等功能。
奇门遁甲是中国古代术数体系，以时间为依据进行预测。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from foundation.types import Verdict
from foundation.gan_zhi_engine import GanZhiEngine


# ============================================================================
# 枚举类型
# ============================================================================

class QMDoor(str, Enum):
    """八门"""
    XIU = "休"
    SHENG = "生"
    SHANG = "伤"
    DU = "杜"
    JING = "景"
    SI_GATE = "死"
    JING_GATE = "惊"
    KAI = "开"


class QMStar(str, Enum):
    """九星"""
    TIANPENG = "天蓬"
    TIANREN = "天任"
    TIANCHONG = "天冲"
    TIANFU = "天辅"
    TIANQIN = "天禽"
    TIANXIN = "天心"
    TIANZHU = "天柱"
    TIANYING = "天英"
    TIANRUI = "天芮"


class QMSpirit(str, Enum):
    """八神"""
    ZHIFU = "值符"
    TENGHE = "腾蛇"
    TAIBAI = "太阴"
    LIUHE = "六合"
    BAIHU = "白虎(勾陈)"
    XUANWU = "玄武(朱雀)"
    JIUDE = "九地"
    JIUTIAN = "九天"


class QMSanQi(str, Enum):
    """三奇"""
    YI = "乙奇"
    BING = "丙奇"
    DING = "丁奇"


class QMLiuYi(str, Enum):
    """六仪"""
    WU = "戊"
    JI = "己"
    GENG = "庚"
    XIN = "辛"
    REN = "壬"
    GUI = "癸"


class QMPalace(str, Enum):
    """九宫"""
    KAN = "坎一宫"
    KUN = "坤二宫"
    ZHEN = "震三宫"
    XUN = "巽四宫"
    CENTER = "中五宫"
    QIAN = "乾六宫"
    DUI = "兑七宫"
    GEN = "艮八宫"
    LI = "离九宫"


# ============================================================================
# 结果数据类
# ============================================================================

@dataclass(frozen=True)
class QMPalaceInfo:
    """一宫的信息"""
    palace: QMPalace
    door: QMDoor
    star: QMStar
    spirit: QMSpirit
    tian_pan: str    # 天盘干
    di_pan: str      # 地盘干
    is_shi: bool     # 是否值使宫
    is_fuxing: bool  # 是否伏吟
    is_fanin: bool   # 是否反吟


@dataclass(frozen=True)
class QMChart:
    """奇门遁甲完整盘"""
    ju: int                                      # 局数 (1-9)
    yin_yang: str                                # "阳遁" or "阴遁"
    dun: int                                     # 遁甲几局
    palace_info: tuple[QMPalaceInfo, ...]        # 9宫信息
    year_gan_zhi: str
    month_gan_zhi: str
    day_gan_zhi: str
    hour_gan_zhi: str
    xun_kong: tuple[str, ...]                    # 旬空地支
    ma_xing: str                                 # 马星


@dataclass(frozen=True)
class QMAnalysis:
    """奇门遁甲分析结果"""
    yong_shen_palace: QMPalace
    yong_shen_door: QMDoor
    yong_shen_star: QMStar
    description: str
    verdict: Verdict


# ============================================================================
# 奇门遁甲引擎
# ============================================================================

class QiMenEngine:
    """奇门遁甲引擎

    提供奇门遁甲排盘和分析功能，采用纯类方法接口。
    """

    # 节气到局数映射: (月, 日) -> (阴阳遁, 局数)
    _JU_TABLE: dict[tuple[int, int], tuple[str, int]] = {
        (12, 22): ("阳遁", 1), (1, 6): ("阳遁", 2), (1, 20): ("阳遁", 3),
        (2, 4): ("阳遁", 4), (2, 19): ("阳遁", 5), (3, 6): ("阳遁", 6),
        (3, 21): ("阳遁", 7), (4, 5): ("阳遁", 8), (4, 20): ("阳遁", 9),
        (6, 21): ("阴遁", 9), (7, 7): ("阴遁", 8), (7, 23): ("阴遁", 7),
        (8, 7): ("阴遁", 6), (8, 23): ("阴遁", 5), (9, 8): ("阴遁", 4),
        (9, 23): ("阴遁", 3), (10, 8): ("阴遁", 2), (10, 23): ("阴遁", 1),
        (11, 7): ("阳遁", 1), (11, 22): ("阳遁", 2), (12, 7): ("阳遁", 3),
    }

    # 宫位编号到九宫枚举
    _PALACE_MAP: dict[int, QMPalace] = {
        1: QMPalace.KAN, 2: QMPalace.KUN, 3: QMPalace.ZHEN,
        4: QMPalace.XUN, 5: QMPalace.CENTER, 6: QMPalace.QIAN,
        7: QMPalace.DUI, 8: QMPalace.GEN, 9: QMPalace.LI,
    }

    # 八门固定循环顺序
    _DOOR_CYCLE: list[QMDoor] = [
        QMDoor.XIU, QMDoor.SHENG, QMDoor.SHANG, QMDoor.DU,
        QMDoor.JING, QMDoor.SI_GATE, QMDoor.JING_GATE, QMDoor.KAI,
    ]

    # 九星洛书轨迹顺序
    _STAR_CYCLE: list[QMStar] = [
        QMStar.TIANPENG, QMStar.TIANREN, QMStar.TIANCHONG, QMStar.TIANFU,
        QMStar.TIANQIN, QMStar.TIANXIN, QMStar.TIANZHU, QMStar.TIANYING,
        QMStar.TIANRUI,
    ]

    # 八神固定顺序
    _SPIRIT_ORDER: list[QMSpirit] = [
        QMSpirit.ZHIFU, QMSpirit.TENGHE, QMSpirit.TAIBAI, QMSpirit.LIUHE,
        QMSpirit.BAIHU, QMSpirit.XUANWU, QMSpirit.JIUDE, QMSpirit.JIUTIAN,
    ]

    # 非中宫序列（阅读顺序：左→右、上→下）
    _NON_CENTER: list[int] = [1, 2, 3, 4, 6, 7, 8, 9]

    # 宫位编号对应的地支（用于空亡/马星匹配）
    # 坎一宫→子，坤二宫→未，震三宫→卯，巽四宫→辰，
    # 中五宫→未（寄坤），乾六宫→戌，兑七宫→酉，艮八宫→丑，离九宫→午
    _PALACE_BRANCHES: tuple[str, ...] = (
        "", "子", "未", "卯", "辰", "未", "戌", "酉", "丑", "午",
    )

    # 天干相冲对（用于反吟判断）
    _CLASH_PAIRS: frozenset[tuple[str, str]] = frozenset({
        ("甲", "庚"), ("庚", "甲"), ("乙", "辛"), ("辛", "乙"),
        ("丙", "壬"), ("壬", "丙"), ("丁", "癸"), ("癸", "丁"),
        ("戊", "己"), ("己", "戊"),
    })

    # ---- 辅助方法 ----

    @staticmethod
    def _get_ju_number(month: int, day: int) -> tuple[str, int]:
        """根据月日确定阴阳遁和局数

        以节气中点为分界，确定当前所处节气对应的局数。
        """
        sorted_terms = sorted(QiMenEngine._JU_TABLE.keys())
        for i in range(len(sorted_terms) - 1, -1, -1):
            t_month, t_day = sorted_terms[i]
            if month > t_month or (month == t_month and day >= t_day):
                return QiMenEngine._JU_TABLE[sorted_terms[i]]
        return ("阳遁", 1)

    @staticmethod
    def _arrange_base_palaces(ju: int, yin_yang: str) -> dict[int, str]:
        """排列三奇六仪地盘位置

        阳遁从局数宫位起顺排，阴遁逆排。
        排列顺序：戊己庚辛壬癸丁丙乙（六仪在前，三奇在后：星奇丁、月奇丙、日奇乙）。
        """
        stems = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
        base: dict[int, str] = {}
        for i, stem in enumerate(stems):
            if yin_yang == "阳遁":
                p = (ju - 1 + i) % 9 + 1
            else:
                p = (ju - 1 - i) % 9
                p = p + 9 if p <= 0 else p
            base[p] = stem
        return base

    @staticmethod
    def _get_stem_index(hour_stem: str) -> int:
        """获取时干在六甲旬中的偏移量（0-8）

        甲=0（隐藏于戊），乙=1，...，壬=8，癸=0（满九归零）。
        """
        return GanZhiEngine.STEMS.index(hour_stem) % 9

    @staticmethod
    def _find_stem_palace(stem: str, base: dict[int, str]) -> int:
        """在地盘中找到天干所在宫位。甲隐藏于戊。中五宫寄坤二宫。"""
        lookup = "戊" if stem == "甲" else stem
        for p, s in base.items():
            if s == lookup:
                return 2 if p == 5 else p  # 中五宫寄坤二宫
        return 2

    @classmethod
    def _rotate_star(
        cls, ju: int, offset: int, yin_yang: str
    ) -> dict[int, QMStar]:
        """旋转天盘九星

        基础排列中宫位k对应星 (k + ju - 2) % 9。
        阳遁顺转：每宫的星来自 (p - offset) 位置。
        阴遁逆转：每宫的星来自 (p + offset) 位置。
        """
        stars = cls._STAR_CYCLE
        result: dict[int, QMStar] = {}
        for p in range(1, 10):
            if yin_yang == "阳遁":
                idx = (p - offset + ju - 2) % 9
            else:
                idx = (p + offset + ju - 2) % 9
            result[p] = stars[idx]
        return result

    @classmethod
    def _rotate_door(
        cls, offset: int, yin_yang: str
    ) -> dict[int, QMDoor]:
        """旋转人盘八门

        八门排布于八个非中宫位置，按偏移量旋转。
        阳遁顺时针，阴遁逆时针。
        """
        seq = cls._NON_CENTER if yin_yang == "阳遁" else list(reversed(cls._NON_CENTER))
        doors = cls._DOOR_CYCLE
        direction = 1 if yin_yang == "阳遁" else -1
        result: dict[int, QMDoor] = {}
        for i in range(8):
            target = (i + offset * direction) % 8
            result[seq[target]] = doors[i]
        return result

    @classmethod
    def _assign_spirit(
        cls, zhi_fu_palace: int, yin_yang: str
    ) -> dict[int, QMSpirit]:
        """排布八神

        值符始终在值符宫位，其余八神按固定顺序排布。
        阳遁顺排，阴遁逆排。
        中五宫寄坤二宫。
        """
        # 中五宫寄坤二宫
        palace = 2 if zhi_fu_palace == 5 else zhi_fu_palace
        seq = cls._NON_CENTER if yin_yang == "阳遁" else list(reversed(cls._NON_CENTER))
        start = seq.index(palace)
        spirits = cls._SPIRIT_ORDER
        result: dict[int, QMSpirit] = {}
        for i in range(8):
            result[seq[(start + i) % 8]] = spirits[i]
        return result

    @staticmethod
    def _get_xun_kong(day_gan_zhi: str) -> tuple[str, ...]:
        """计算日干支所在旬的旬空地支

        每旬（10个干支）有两个地支无天干配对，称为旬空。
        """
        stems = GanZhiEngine.STEMS
        branches = GanZhiEngine.BRANCHES
        stem_idx = stems.index(day_gan_zhi[0])
        branch_idx = branches.index(day_gan_zhi[1])
        jia_branch = (branch_idx - stem_idx) % 12
        return (branches[(jia_branch + 10) % 12], branches[(jia_branch + 11) % 12])

    @staticmethod
    def _get_ma_xing(day_branch: str) -> str:
        """计算日支对应的马星

        申子辰→寅，寅午戌→申，巳酉丑→亥，亥卯未→巳。
        """
        ma_map = {"申": "寅", "子": "寅", "辰": "寅", "寅": "申",
                  "午": "申", "戌": "申", "巳": "亥", "酉": "亥",
                  "丑": "亥", "亥": "巳", "卯": "巳", "未": "巳"}
        return ma_map[day_branch]

    # ---- 公开接口 ----

    @classmethod
    def time_to_chart(
        cls, year: int, month: int, day: int, hour: int
    ) -> QMChart:
        """根据时间排出奇门遁甲盘

        Args:
            year: 年份（公历）
            month: 月份 (1-12)
            day: 日期 (1-31)
            hour: 时辰 (0-23，24小时制)

        Returns:
            奇门遁甲完整盘
        """
        # 1. 时间转干支
        gz = GanZhiEngine.time_to_gan_zhi(year, month, day, hour)
        year_gz, month_gz = gz["year"], gz["month"]
        day_gz, hour_gz = gz["day"], gz["hour"]
        hour_stem = hour_gz[0]

        # 2. 定局：确定阴阳遁和局数
        yin_yang, ju = cls._get_ju_number(month, day)

        # 3. 排地盘：三奇六仪基础排列
        base = cls._arrange_base_palaces(ju, yin_yang)

        # 4. 计算偏移量（时干在旬中的位置）
        offset = cls._get_stem_index(hour_stem)

        # 5. 确定值符宫位（时干所落宫）
        zhi_fu_palace = cls._find_stem_palace(hour_stem, base)

        # 6. 旋转天盘（九星）
        star_map = cls._rotate_star(ju, offset, yin_yang)

        # 7. 旋转人盘（八门）
        door_map = cls._rotate_door(offset, yin_yang)

        # 8. 排八神
        spirit_map = cls._assign_spirit(zhi_fu_palace, yin_yang)

        # 9. 计算天盘干（旋转后的天干位置）和值使宫
        tian_map: dict[int, str] = {}
        for p in range(1, 10):
            if yin_yang == "阳遁":
                src = ((p - 1 - offset) % 9) + 1
            else:
                src = ((p - 1 + offset) % 9) + 1
            tian_map[p] = base[src]

        # 值使门 = 值符宫在基础排列中的门，旋转后所在宫即为值使宫
        nc = cls._NON_CENTER if yin_yang == "阳遁" else list(reversed(cls._NON_CENTER))
        zs_idx = nc.index(zhi_fu_palace)
        zs_dir = 1 if yin_yang == "阳遁" else -1
        zs_target = nc[(zs_idx + offset * zs_dir) % 8]

        # 10. 组装九宫信息
        clash = cls._CLASH_PAIRS
        palace_info_list: list[QMPalaceInfo] = []
        for p in range(1, 10):
            tian, di = tian_map[p], base[p]
            # 中五宫无门星神，寄坤二宫
            if p == 5:
                door, star, spirit = QMDoor.XIU, QMStar.TIANQIN, QMSpirit.ZHIFU
            else:
                door, star, spirit = door_map[p], star_map[p], spirit_map[p]
            palace_info_list.append(QMPalaceInfo(
                palace=cls._PALACE_MAP[p],
                door=door,
                star=star,
                spirit=spirit,
                tian_pan=tian,
                di_pan=di,
                is_shi=(p == zs_target),
                is_fuxing=(tian == di),
                is_fanin=(tian, di) in clash,
            ))

        # 11. 旬空与马星
        xun_kong = cls._get_xun_kong(day_gz)
        ma_xing = cls._get_ma_xing(day_gz[1])

        return QMChart(
            ju=ju, yin_yang=yin_yang, dun=ju,
            palace_info=tuple(palace_info_list),
            year_gan_zhi=year_gz, month_gan_zhi=month_gz,
            day_gan_zhi=day_gz, hour_gan_zhi=hour_gz,
            xun_kong=xun_kong, ma_xing=ma_xing,
        )

    @classmethod
    def analyze_chart(
        cls, chart: QMChart, question_type: str = "general"
    ) -> QMAnalysis:
        """分析奇门盘，给出吉凶判断

        Args:
            chart: 奇门遁甲盘
            question_type: 问题类型
                - "general": 通用（以日干落宫为用神）
                - "career": 事业（以开门落宫为用神）
                - "wealth": 财运（以生门落宫为用神）
                - "health": 健康（以天芮落宫为用神）
                - "lawsuit": 诉讼（以惊门落宫为用神）

        Returns:
            奇门遁甲分析结果
        """
        ys = cls._find_yong_shen(chart, question_type)
        score = 50
        # 八门评分
        score += {QMDoor.KAI: 20, QMDoor.SHENG: 20, QMDoor.XIU: 15,
                  QMDoor.JING: 5, QMDoor.DU: -5, QMDoor.SHANG: -15,
                  QMDoor.SI_GATE: -20, QMDoor.JING_GATE: -10}.get(ys.door, 0)
        # 九星评分
        score += {QMStar.TIANXIN: 15, QMStar.TIANREN: 15, QMStar.TIANFU: 15,
                  QMStar.TIANPENG: 10, QMStar.TIANCHONG: 5, QMStar.TIANQIN: 5,
                  QMStar.TIANZHU: -10, QMStar.TIANYING: -10,
                  QMStar.TIANRUI: -15}.get(ys.star, 0)
        # 八神评分
        score += {QMSpirit.ZHIFU: 15, QMSpirit.TAIBAI: 10, QMSpirit.LIUHE: 10,
                  QMSpirit.JIUTIAN: 10, QMSpirit.JIUDE: 10, QMSpirit.TENGHE: -10,
                  QMSpirit.BAIHU: -15, QMSpirit.XUANWU: -15}.get(ys.spirit, 0)
        if ys.is_fuxing:
            score -= 5
        if ys.is_fanin:
            score -= 10

        # 空亡影响：空亡宫位的门/星/神力量减半
        xun_kong_set = set(chart.xun_kong)
        branches = cls._PALACE_BRANCHES
        for palace_idx, _ in enumerate(chart.palace_info):
            palace_branch = branches[palace_idx + 1] if palace_idx + 1 < len(branches) else ""
            if palace_branch and palace_branch in xun_kong_set:
                score -= 5

        # 马星宫位加分（主动、变动）
        if chart.ma_xing:
            for palace_idx, _ in enumerate(chart.palace_info):
                palace_branch = branches[palace_idx + 1] if palace_idx + 1 < len(branches) else ""
                if palace_branch == chart.ma_xing:
                    score += 8

        score = max(0, min(100, score))

        if score >= 65:
            overall, trend = "吉", "上升"
        elif score <= 35:
            overall, trend = "凶", "下降"
        else:
            overall, trend = "平", "平稳"

        # 动态置信度：基于用神宫单项评分的清晰程度
        yong_shen_idx = None
        for i, p in enumerate(chart.palace_info):
            if p is ys:
                yong_shen_idx = i
                break

        if yong_shen_idx is not None:
            yong_score = 0
            yong_score += {QMDoor.KAI: 20, QMDoor.SHENG: 20, QMDoor.XIU: 15,
                           QMDoor.JING: 5, QMDoor.DU: -5, QMDoor.SHANG: -15,
                           QMDoor.SI_GATE: -20, QMDoor.JING_GATE: -10}.get(ys.door, 0)
            yong_score += {QMStar.TIANXIN: 15, QMStar.TIANREN: 15, QMStar.TIANFU: 15,
                           QMStar.TIANPENG: 10, QMStar.TIANCHONG: 5, QMStar.TIANQIN: 5,
                           QMStar.TIANZHU: -10, QMStar.TIANYING: -10,
                           QMStar.TIANRUI: -15}.get(ys.star, 0)
            yong_score += {QMSpirit.ZHIFU: 15, QMSpirit.TAIBAI: 10, QMSpirit.LIUHE: 10,
                           QMSpirit.JIUTIAN: 10, QMSpirit.JIUDE: 10, QMSpirit.TENGHE: -10,
                           QMSpirit.BAIHU: -15, QMSpirit.XUANWU: -15}.get(ys.spirit, 0)
            if ys.is_fuxing:
                yong_score -= 5
            if ys.is_fanin:
                yong_score -= 10
            confidence = max(40, min(90, 50 + abs(yong_score)))
        else:
            confidence = 50

        parts = [f"用神落{ys.palace.value}", f"临{ys.door.value}门",
                 ys.star.value, ys.spirit.value]
        if ys.is_fuxing:
            parts.append("伏吟")
        if ys.is_fanin:
            parts.append("反吟")

        # 描述中补充空亡/马星信息
        yong_branch = ""
        for pb_idx, pb in enumerate(chart.palace_info):
            if pb is ys:
                yong_branch = branches[pb_idx + 1] if pb_idx + 1 < len(branches) else ""
                break
        if yong_branch and yong_branch in xun_kong_set:
            parts.append("落空亡")
        if yong_branch and yong_branch == chart.ma_xing:
            parts.append("临马星")

        return QMAnalysis(
            yong_shen_palace=ys.palace, yong_shen_door=ys.door,
            yong_shen_star=ys.star, description="，".join(parts),
            verdict=Verdict(overall=overall, strength=score,
                            trend=trend, confidence=confidence),
        )

    @classmethod
    def _find_yong_shen(cls, chart: QMChart, question_type: str) -> QMPalaceInfo:
        """根据问题类型确定用神宫位"""
        info = chart.palace_info
        door_map = {"career": QMDoor.KAI, "wealth": QMDoor.SHENG,
                    "lawsuit": QMDoor.JING_GATE}
        if question_type == "health":
            for p in info:
                if p.star == QMStar.TIANRUI:
                    return p
            return info[0]
        target_door = door_map.get(question_type)
        if target_door:
            for p in info:
                if p.door == target_door:
                    return p
        # 通用：以日干落宫为用神
        return cls._find_palace_by_stem(chart, chart.day_gan_zhi[0])

    @classmethod
    def _find_palace_by_stem(cls, chart: QMChart, stem: str) -> QMPalaceInfo:
        """根据天干找到地盘对应的宫位（甲隐藏于戊）"""
        idx = GanZhiEngine.STEMS.index(stem) % 9
        ju, yy = chart.dun, chart.yin_yang
        if yy == "阳遁":
            pn = (ju - 1 + idx) % 9 + 1
        else:
            pn = (ju - 1 - idx) % 9
            pn = pn + 9 if pn <= 0 else pn
        target = cls._PALACE_MAP[pn]
        for p in chart.palace_info:
            if p.palace == target:
                return p
        return chart.palace_info[0]
