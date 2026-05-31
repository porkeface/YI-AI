"""梅花易数模块

实现梅花易数起卦方法，包括：
- 数字起卦（先天数/后天数）
- 时间起卦（年月日时）
- 外应起卦（环境现象）
- 体用分析（主卦/变卦的体用关系）

梅花易数核心原理：
- 以数起卦，除8取余定上下卦
- 以数之和除6取余定动爻
- 动爻所在卦为"用卦"，不动卦为"体卦"
- 体卦代表主体，用卦代表客体/变化
"""

from __future__ import annotations

import logging
import time as time_module
from dataclasses import dataclass
from enum import Enum

from foundation.types import Element, Hexagram, YinYang
from foundation.hexagram_engine import HexagramEngine
from foundation.element_engine import ElementEngine

logger = logging.getLogger(__name__)


class NumberBasis(str, Enum):
    """数字起卦基准"""
    XIANTIAN = "先天数"   # 先天八卦数: 乾1兑2离3震4巽5坎6艮7坤8
    HOUTIAN = "后天数"    # 后天八卦数: 坎1坤2震3巽4中5乾6兑7艮8离9


class ExternalSign(str, Enum):
    """外应类型"""
    SOUND = "声音"        # 听到的声音
    SIGHT = "视觉"        # 看到的景象
    ANIMAL = "动物"       # 遇到的动物
    OBJECT = "物体"       # 看到的物体
    DIRECTION = "方向"    # 来人/物的方向
    NUMBER = "数字"       # 偶然看到的数字


# 先天八卦数到卦名映射
_XIANTIAN_MAP: dict[int, str] = {
    1: "乾", 2: "兑", 3: "离", 4: "震",
    5: "巽", 6: "坎", 7: "艮", 8: "坤",
}

# 后天八卦数到卦名映射
_HOUTIAN_MAP: dict[int, str] = {
    1: "坎", 2: "坤", 3: "震", 4: "巽", 5: "中宫",
    6: "乾", 7: "兑", 8: "艮", 9: "离",
}

# 方位到卦名映射
_DIRECTION_MAP: dict[str, str] = {
    "北": "坎", "南": "离", "东": "震", "西": "兑",
    "东北": "艮", "东南": "巽", "西南": "坤", "西北": "乾",
}

# 动物到卦名映射
_ANIMAL_MAP: dict[str, str] = {
    "龙": "震", "凤": "离", "虎": "兑", "龟": "坎",
    "马": "乾", "牛": "坤", "鸡": "巽", "狗": "艮",
}

# 五行到卦的映射（用于外应推断）
_ELEMENT_TO_TRIGRAM: dict[Element, str] = {
    Element.METAL: "乾",
    Element.WOOD: "震",
    Element.WATER: "坎",
    Element.FIRE: "离",
    Element.EARTH: "坤",
}


@dataclass(frozen=True)
class PlumBlossomResult:
    """梅花易数起卦结果

    Attributes:
        hexagram: 主卦
        changed_hexagram: 变卦
        ti_gua: 体卦（不动的卦）
        yong_gua: 用卦（动爻所在的卦）
        ti_element: 体卦五行
        yong_element: 用卦五行
        sheng_ke_relation: 体用生克关系
        method: 起卦方法描述
    """
    hexagram: Hexagram
    changed_hexagram: Hexagram | None
    ti_gua: str        # 体卦名称
    yong_gua: str      # 用卦名称
    ti_element: Element
    yong_element: Element
    sheng_ke_relation: str  # 体用生克关系
    method: str


class PlumBlossomEngine:
    """梅花易数引擎

    提供多种梅花易数起卦方式和体用分析。
    """

    @staticmethod
    def divinate_by_numbers(
        num1: int,
        num2: int,
        basis: NumberBasis = NumberBasis.XIANTIAN,
    ) -> PlumBlossomResult:
        """数字起卦

        两个数字分别除8取余定上下卦，两数之和除6取余定动爻。

        Args:
            num1: 第一个数字（定上卦）
            num2: 第二个数字（定下卦）
            basis: 数字基准（先天/后天）

        Returns:
            梅花易数起卦结果
        """
        trigram_map = (
            _XIANTIAN_MAP if basis == NumberBasis.XIANTIAN
            else _HOUTIAN_MAP
        )

        # 定卦
        upper_idx = num1 % 8
        if upper_idx == 0:
            upper_idx = 8
        lower_idx = num2 % 8
        if lower_idx == 0:
            lower_idx = 8

        upper_name = trigram_map[upper_idx]
        lower_name = trigram_map[lower_idx]

        # 定动爻
        moving_pos = (num1 + num2) % 6
        if moving_pos == 0:
            moving_pos = 6

        method = f"数字起卦({basis.value})：{num1}、{num2}"

        return PlumBlossomEngine._build_result(
            upper_name, lower_name, [moving_pos], method
        )

    @staticmethod
    def divinate_by_time(
        year: int | None = None,
        month: int | None = None,
        day: int | None = None,
        hour: int | None = None,
    ) -> PlumBlossomResult:
        """时间起卦

        年数+月数+日数 除8取余定上卦
        年数+月数+日数+时辰数 除6取余定动爻
        年数+月数+日数+时辰数 除8取余定下卦

        Args:
            year: 年份（默认当前年）
            month: 月份（默认当前月）
            day: 日期（默认当前日）
            hour: 时辰（1-12，默认当前时）

        Returns:
            梅花易数起卦结果
        """
        import datetime
        now = datetime.datetime.now()
        year = year or now.year
        month = month or now.month
        day = day or now.day

        # 时辰：2小时为一个时辰，从子时(23-1)开始
        if hour is None:
            hour_idx = ((now.hour + 1) % 24) // 2
        else:
            hour_idx = hour % 12

        # 上卦：年+月+日 除8
        upper_sum = year + month + day
        upper_idx = upper_sum % 8
        if upper_idx == 0:
            upper_idx = 8

        # 下卦：年+月+日+时辰 除8
        total = upper_sum + hour_idx
        lower_idx = total % 8
        if lower_idx == 0:
            lower_idx = 8

        # 动爻：年+月+日+时辰 除6
        moving_pos = total % 6
        if moving_pos == 0:
            moving_pos = 6

        upper_name = _XIANTIAN_MAP[upper_idx]
        lower_name = _XIANTIAN_MAP[lower_idx]

        method = f"时间起卦：{year}年{month}月{day}日 时辰{hour_idx}"

        return PlumBlossomEngine._build_result(
            upper_name, lower_name, [moving_pos], method
        )

    @staticmethod
    def divinate_by_external_sign(
        upper_sign: str,
        lower_sign: str,
        sign_type: ExternalSign = ExternalSign.DIRECTION,
        moving_position: int | None = None,
    ) -> PlumBlossomResult:
        """外应起卦

        根据环境中的现象（方位、动物、声音等）起卦。
        梅花易数要求有动爻才能区分体/用，因此默认初爻动。

        Args:
            upper_sign: 上卦对应的外应（如"北"、"龙"等）
            lower_sign: 下卦对应的外应（如"南"、"虎"等）
            sign_type: 外应类型
            moving_position: 动爻位置（1-6），默认None时取初爻动

        Returns:
            梅花易数起卦结果

        Raises:
            ValueError: 无法识别的外应或动爻位置无效
        """
        sign_map = PlumBlossomEngine._get_sign_map(sign_type)

        upper_name = sign_map.get(upper_sign)
        lower_name = sign_map.get(lower_sign)

        if upper_name is None:
            raise ValueError(
                f"无法从{sign_type.value}推断上卦：'{upper_sign}'"
            )
        if lower_name is None:
            raise ValueError(
                f"无法从{sign_type.value}推断下卦：'{lower_sign}'"
            )

        # 默认初爻动，确保有动爻区分体/用
        if moving_position is None:
            moving_position = 1

        if not (1 <= moving_position <= 6):
            raise ValueError(
                f"动爻位置必须在1-6之间，收到: {moving_position}"
            )

        method = f"外应起卦({sign_type.value})：上'{upper_sign}' 下'{lower_sign}'"

        return PlumBlossomEngine._build_result(
            upper_name, lower_name, [moving_position], method
        )

    @staticmethod
    def _get_sign_map(sign_type: ExternalSign) -> dict[str, str]:
        """获取外应类型对应的映射表

        Args:
            sign_type: 外应类型

        Returns:
            映射字典
        """
        if sign_type == ExternalSign.DIRECTION:
            return _DIRECTION_MAP
        elif sign_type == ExternalSign.ANIMAL:
            return _ANIMAL_MAP
        else:
            # 其他类型暂返回空映射
            return {}

    @staticmethod
    def _build_result(
        upper_name: str,
        lower_name: str,
        moving_positions: list[int],
        method: str,
    ) -> PlumBlossomResult:
        """构建起卦结果

        Args:
            upper_name: 上卦名
            lower_name: 下卦名
            moving_positions: 动爻位置列表
            method: 起卦方法描述

        Returns:
            梅花易数起卦结果
        """
        # 构建阴阳值
        yin_yangs = PlumBlossomEngine._trigram_names_to_yin_yangs(
            upper_name, lower_name
        )

        # 创建主卦
        hexagram = HexagramEngine.create(yin_yangs)

        # 创建变卦
        changed_hexagram = None
        if moving_positions:
            try:
                changed_hexagram = HexagramEngine.get_changed(
                    hexagram, tuple(moving_positions)
                )
            except (ValueError, IndexError):
                changed_hexagram = None

        # 体用分析
        ti_gua, yong_gua, ti_element, yong_element, relation = (
            PlumBlossomEngine._analyze_ti_yong(
                upper_name, lower_name, moving_positions
            )
        )

        return PlumBlossomResult(
            hexagram=hexagram,
            changed_hexagram=changed_hexagram,
            ti_gua=ti_gua,
            yong_gua=yong_gua,
            ti_element=ti_element,
            yong_element=yong_element,
            sheng_ke_relation=relation,
            method=method,
        )

    @staticmethod
    def _trigram_names_to_yin_yangs(
        upper_name: str,
        lower_name: str,
    ) -> list[YinYang]:
        """将卦名转换为阴阳值列表

        Args:
            upper_name: 上卦名
            lower_name: 下卦名

        Returns:
            6个阴阳值（从下到上）
        """
        # 先天八卦二进制映射
        trigram_binary: dict[str, str] = {
            "乾": "111", "兑": "110", "离": "101", "震": "100",
            "巽": "011", "坎": "010", "艮": "001", "坤": "000",
        }

        lower_bin = trigram_binary.get(lower_name, "000")
        upper_bin = trigram_binary.get(upper_name, "000")

        full_binary = lower_bin + upper_bin
        return [
            YinYang.YANG if b == "1" else YinYang.YIN
            for b in full_binary
        ]

    @staticmethod
    def _analyze_ti_yong(
        upper_name: str,
        lower_name: str,
        moving_positions: list[int],
    ) -> tuple[str, str, Element, Element, str]:
        """体用分析

        梅花易数核心：动爻所在的卦为"用卦"，不动的卦为"体卦"。
        体卦代表主体/自身，用卦代表客体/环境/变化。

        五行生克关系：
        - 用生体：客体有利于主体，吉
        - 体生用：主体消耗精力，小凶
        - 用克体：客体对主体不利，凶
        - 体克用：主体能控制客体，小吉
        - 比和：体用同五行，平稳

        Args:
            upper_name: 上卦名
            lower_name: 下卦名
            moving_positions: 动爻位置列表

        Returns:
            (体卦名, 用卦名, 体五行, 用五行, 生克关系)
        """
        # 判断动爻在哪个卦
        # 爻位1-3在下卦，4-6在上卦
        has_lower_moving = any(p <= 3 for p in moving_positions)
        has_upper_moving = any(p >= 4 for p in moving_positions)

        # 获取卦的五行
        trigram_element: dict[str, Element] = {
            "乾": Element.METAL, "兑": Element.METAL,
            "离": Element.FIRE, "震": Element.WOOD,
            "巽": Element.WOOD, "坎": Element.WATER,
            "艮": Element.EARTH, "坤": Element.EARTH,
        }

        upper_element = trigram_element.get(upper_name, Element.EARTH)
        lower_element = trigram_element.get(lower_name, Element.EARTH)

        # 体用判定
        if has_lower_moving and not has_upper_moving:
            # 动爻在下卦 → 下卦为用，上卦为体
            ti_gua = upper_name
            yong_gua = lower_name
            ti_element = upper_element
            yong_element = lower_element
        elif has_upper_moving and not has_lower_moving:
            # 动爻在上卦 → 上卦为用，下卦为体
            ti_gua = lower_name
            yong_gua = upper_name
            ti_element = lower_element
            yong_element = upper_element
        else:
            # 上下都有动爻或无动爻 → 默认上为用，下为体
            ti_gua = lower_name
            yong_gua = upper_name
            ti_element = lower_element
            yong_element = upper_element

        # 生克关系
        relation = PlumBlossomEngine._get_sheng_ke(ti_element, yong_element)

        return ti_gua, yong_gua, ti_element, yong_element, relation

    @staticmethod
    def _get_sheng_ke(ti_element: Element, yong_element: Element) -> str:
        """判断体用五行生克关系

        Args:
            ti_element: 体卦五行
            yong_element: 用卦五行

        Returns:
            生克关系描述
        """
        if ti_element == yong_element:
            return "比和（体用同五行，平稳）"

        # 五行相生：木生火，火生土，土生金，金生水，水生木
        sheng_map: dict[Element, Element] = {
            Element.WOOD: Element.FIRE,
            Element.FIRE: Element.EARTH,
            Element.EARTH: Element.METAL,
            Element.METAL: Element.WATER,
            Element.WATER: Element.WOOD,
        }

        # 用生体
        if sheng_map.get(yong_element) == ti_element:
            return "用生体（客体有利于主体，吉）"

        # 体生用
        if sheng_map.get(ti_element) == yong_element:
            return "体生用（主体消耗精力，小凶）"

        # 用克体
        try:
            if ElementEngine.overcomes(yong_element, ti_element):
                return "用克体（客体对主体不利，凶）"
        except (ValueError, KeyError):
            pass

        # 体克用
        try:
            if ElementEngine.overcomes(ti_element, yong_element):
                return "体克用（主体能控制客体，小吉）"
        except (ValueError, KeyError):
            pass

        return "关系不明"
