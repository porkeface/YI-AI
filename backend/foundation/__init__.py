"""易学基础引擎模块

提供八卦、五行、干支等基础易学功能。
"""

from foundation.types import (
    Element,
    Hexagram,
    Line,
    ProsperityState,
    RuleAnalysisResult,
    SixRelation,
    SixSpirit,
    Trigram,
    TrigramName,
    Verdict,
    YinYang,
)
from foundation.element_engine import ElementEngine
from foundation.trigram_engine import TrigramEngine
from foundation.hexagram_engine import HexagramEngine
from foundation.gan_zhi_engine import GanZhiEngine
from foundation.six_relation_engine import SixRelationEngine
from foundation.six_spirit_engine import SixSpiritEngine
from foundation.shi_ying_engine import ShiYingEngine
from foundation.qimen_engine import (
    QiMenEngine,
    QMDoor,
    QMStar,
    QMSpirit,
    QMSanQi,
    QMLiuYi,
    QMPalace,
    QMPalaceInfo,
    QMChart,
    QMAnalysis,
)
from foundation.ziwei_engine import (
    ZiWeiEngine,
    ZWStar,
    ZWAuxStar,
    ZWHua,
    ZWPalace,
    ZWPalaceType,
    ZWStarPosition,
    ZWPalaceInfo,
    ZWChart,
    ZWAnalysis,
)

__all__ = [
    # 类型
    "Element",
    "Hexagram",
    "Line",
    "ProsperityState",
    "RuleAnalysisResult",
    "SixRelation",
    "SixSpirit",
    "Trigram",
    "TrigramName",
    "Verdict",
    "YinYang",
    # 引擎
    "ElementEngine",
    "TrigramEngine",
    "HexagramEngine",
    "GanZhiEngine",
    "SixRelationEngine",
    "SixSpiritEngine",
    "ShiYingEngine",
    # 奇门遁甲
    "QiMenEngine",
    "QMDoor",
    "QMStar",
    "QMSpirit",
    "QMSanQi",
    "QMLiuYi",
    "QMPalace",
    "QMPalaceInfo",
    "QMChart",
    "QMAnalysis",
    # 紫微斗数
    "ZiWeiEngine",
    "ZWStar",
    "ZWAuxStar",
    "ZWHua",
    "ZWPalace",
    "ZWPalaceType",
    "ZWStarPosition",
    "ZWPalaceInfo",
    "ZWChart",
    "ZWAnalysis",
]
