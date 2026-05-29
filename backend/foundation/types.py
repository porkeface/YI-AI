"""核心类型定义模块

定义易学引擎的基础数据结构，包括阴阳、八卦、五行、六亲、六神等枚举和数据类。
所有数据结构使用 frozen=True 确保不可变性。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


# ============================================================================
# 基础枚举类型
# ============================================================================

class YinYang(str, Enum):
    """阴阳枚举"""
    YIN = "yin"
    YANG = "yang"


class TrigramName(str, Enum):
    """八卦名称枚举（先天八卦序）"""
    QIAN = "乾"    # 111
    DUI = "兑"     # 110
    LI = "离"      # 101
    ZHEN = "震"    # 100
    XUN = "巽"     # 011
    KAN = "坎"     # 010
    GEN = "艮"     # 001
    KUN = "坤"     # 000


class Element(str, Enum):
    """五行枚举"""
    METAL = "金"
    WOOD = "木"
    WATER = "水"
    FIRE = "火"
    EARTH = "土"


class SixRelation(str, Enum):
    """六亲枚举"""
    PARENT = "父母"      # 生我者
    OFFICIAL = "官鬼"    # 克我者
    WEALTH = "妻财"      # 我克者
    CHILDREN = "子孙"    # 我生者
    BROTHER = "兄弟"     # 同我者


class SixSpirit(str, Enum):
    """六神枚举（按日干排布）"""
    QINGLONG = "青龙"    # 甲乙日
    ZHUQUE = "朱雀"      # 丙丁日
    GOUCHEN = "勾陈"     # 戊日
    TENGHE = "螣蛇"      # 己日
    BAIHU = "白虎"       # 庚辛日
    XUANWU = "玄武"      # 壬癸日


class ProsperityState(str, Enum):
    """五行旺衰状态"""
    WANG = "旺"     # 当令
    XIANG = "相"    # 得生
    XIU = "休"      # 休息
    QIU = "囚"      # 被克
    SI = "死"        # 死绝


# ============================================================================
# 核心数据结构
# ============================================================================

@dataclass(frozen=True)
class Line:
    """爻的数据结构

    Attributes:
        position: 爻的位置（1-6，从下到上）
        yin_yang: 阴阳属性
        is_moving: 是否为动爻
        element: 五行属性
        six_relation: 六亲关系
        six_spirit: 六神
        gan_zhi: 干支（如"甲子"）
        is_shi: 是否为世爻
        is_ying: 是否为应爻
    """
    position: int  # 1-6
    yin_yang: YinYang
    is_moving: bool
    element: Element
    six_relation: SixRelation
    six_spirit: SixSpirit
    gan_zhi: str
    is_shi: bool
    is_ying: bool


@dataclass(frozen=True)
class Trigram:
    """三爻卦（经卦）数据结构

    Attributes:
        name: 卦名
        binary_rep: 二进制表示（3位，从下到上）
        element: 五行属性
        nature: 自然象
        direction: 方位
        family: 家族角色
        body: 身体部位
        animal: 动物象
    """
    name: TrigramName
    binary_rep: str  # 3位二进制，如"111"
    element: Element
    nature: str
    direction: str
    family: str
    body: str
    animal: str


@dataclass(frozen=True)
class Hexagram:
    """六爻卦（重卦）数据结构

    Attributes:
        id: 卦序号（1-64）
        name: 卦名
        upper_trigram: 上卦
        lower_trigram: 下卦
        lines: 六爻数据（从下到上）
        element: 卦的五行属性
        judgment: 卦辞
        image: 象辞
    """
    id: int
    name: str
    upper_trigram: Trigram
    lower_trigram: Trigram
    lines: tuple[Line, Line, Line, Line, Line, Line]  # 6个爻
    element: Element
    judgment: str
    image: str


@dataclass(frozen=True)
class Verdict:
    """占卜结论

    Attributes:
        overall: 总体判断（吉/凶/平）
        strength: 力量强度（0-100）
        trend: 趋势（上升/下降/平稳）
        confidence: 置信度（0-100）
    """
    overall: Literal["吉", "凶", "平"]
    strength: int  # 0-100
    trend: Literal["上升", "下降", "平稳"]
    confidence: int  # 0-100


@dataclass(frozen=True)
class RuleAnalysisResult:
    """规则分析结果

    Attributes:
        yong_shen: 用神（六亲类型）
        moving_lines: 动爻位置列表
        relationships: 爻之间的关系描述
        prosperity: 用神的旺衰状态
        verdict: 占卜结论
    """
    yong_shen: SixRelation
    moving_lines: tuple[int, ...]
    relationships: tuple[str, ...]
    prosperity: ProsperityState
    verdict: Verdict


# ============================================================================
# 类型别名
# ============================================================================

# 六爻阴阳序列（从下到上）
LineSequence = tuple[YinYang, YinYang, YinYang, YinYang, YinYang, YinYang]

# 干支对
GanZhiPair = tuple[str, str]  # (天干, 地支)
