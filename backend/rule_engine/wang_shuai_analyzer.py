"""旺衰分析模块

根据月令（地支）判断用神的旺衰状态。
根据日辰（地支）判断用神的长生十二宫状态（生旺墓绝空）。

五行旺衰状态：
- 旺：五行当令（与月令同五行）
- 相：五行得生（月令生该五行）
- 休：五行休息（该五行生月令）
- 囚：五行被克（该五行克月令）
- 死：五行死绝（月令克该五行）

日辰十二长生状态：
- 生：长生/沐浴/冠带/临官/帝旺（力量较强）
- 旺：帝旺（力量最强）
- 墓：入墓（力量受困）
- 绝：绝地（力量最弱）
- 空：旬空（暂时无力）
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from foundation.types import Element, Hexagram, ProsperityState, SixRelation
from foundation.element_engine import ElementEngine


# 地支顺序
_BRANCH_ORDER: list[str] = [
    "子", "丑", "寅", "卯", "辰", "巳",
    "午", "未", "申", "酉", "戌", "亥",
]


class LifecycleStage(str, Enum):
    """长生十二宫完整阶段"""
    CHANG_SHENG = "长生"   # 出生
    MU_YU = "沐浴"         # 洗浴
    GUAN_DAI = "冠带"      # 成年
    LIN_GUAN = "临官"      # 做官
    DI_WANG = "帝旺"       # 鼎盛
    SHUAI = "衰"           # 衰退
    BING = "病"            # 生病
    SI = "死"              # 死亡
    MU = "墓"              # 入墓
    JUE = "绝"             # 绝地
    TAI = "胎"             # 投胎
    YANG = "养"            # 养育


class YongShenLifecycle(str, Enum):
    """用神日辰生命周期（简化四状态）"""
    SHENG = "生"    # 长生~帝旺，力量较强
    WANG = "旺"     # 帝旺，力量最强
    MU = "墓"       # 入墓，力量受困
    JUE = "绝"      # 绝地，力量最弱
    KONG = "空"     # 旬空，暂时无力


# 五行的长生起始地支
_CHANG_SHENG_BRANCH: dict[Element, str] = {
    Element.WOOD: "亥",    # 木长生在亥
    Element.FIRE: "寅",    # 火长生在寅
    Element.EARTH: "申",   # 土长生在申（随火行）
    Element.METAL: "巳",   # 金长生在巳
    Element.WATER: "申",   # 水长生在申
}

# 五行的关键生命周期地支映射（简化为生/旺/墓/绝）
# key: (Element, branch) -> YongShenLifecycle
_LIFECYCLE_MAP: dict[tuple[Element, str], YongShenLifecycle] = {}


def _build_lifecycle_map() -> None:
    """构建五行生命周期映射表"""
    if _LIFECYCLE_MAP:
        return

    stages = list(LifecycleStage)
    for element, birth_branch in _CHANG_SHENG_BRANCH.items():
        birth_idx = _BRANCH_ORDER.index(birth_branch)
        for i, stage in enumerate(stages):
            branch = _BRANCH_ORDER[(birth_idx + i) % 12]
            if stage == LifecycleStage.DI_WANG:
                simplified = YongShenLifecycle.WANG
            elif stage == LifecycleStage.MU:
                simplified = YongShenLifecycle.MU
            elif stage == LifecycleStage.JUE:
                simplified = YongShenLifecycle.JUE
            else:
                # 长生、沐浴、冠带、临官 -> 生；衰、病、死、胎、养 -> 生
                simplified = YongShenLifecycle.SHENG
            _LIFECYCLE_MAP[(element, branch)] = simplified


def _get_lifecycle(element: Element, branch: str) -> YongShenLifecycle:
    """获取五行在指定地支的生命周期状态"""
    _build_lifecycle_map()
    return _LIFECYCLE_MAP.get((element, branch), YongShenLifecycle.SHENG)


# 生命周期状态描述
_LIFECYCLE_DESCRIPTIONS: dict[YongShenLifecycle, str] = {
    YongShenLifecycle.SHENG: "日辰生旺，用神得力",
    YongShenLifecycle.WANG: "日辰帝旺，用神最旺",
    YongShenLifecycle.MU: "日辰入墓，用神受困",
    YongShenLifecycle.JUE: "日辰绝地，用神无力",
    YongShenLifecycle.KONG: "日辰旬空，用神暂无实意",
}


@dataclass(frozen=True)
class DayBranchAnalysis:
    """日辰分析结果

    Attributes:
        day_branch: 日支
        day_element: 日支的五行
        yong_shen_lifecycle: 用神在日辰的生命周期状态
        lifecycle_stage: 完整的长生十二宫阶段
        description: 状态描述
    """

    day_branch: str
    day_element: Element
    yong_shen_lifecycle: YongShenLifecycle
    lifecycle_stage: LifecycleStage
    description: str


# 旺衰状态的描述文本
_PROSPERITY_DESCRIPTIONS: dict[ProsperityState, str] = {
    ProsperityState.WANG: "当令旺相，力量最强",
    ProsperityState.XIANG: "得月令生扶，力量较强",
    ProsperityState.XIU: "休息状态，力量一般",
    ProsperityState.QIU: "受月令克制，力量较弱",
    ProsperityState.SI: "死绝无气，力量最弱",
}


@dataclass(frozen=True)
class ProsperityAnalysis:
    """旺衰分析结果

    Attributes:
        month_element: 月令的五行
        yong_shen_element: 用神的五行
        prosperity_state: 用神的旺衰状态
        description: 旺衰状态的文字描述
        day_branch_analysis: 日辰分析结果（可选）
    """

    month_element: Element
    yong_shen_element: Element
    prosperity_state: ProsperityState
    description: str
    day_branch_analysis: DayBranchAnalysis | None = None


class WangShuaiAnalyzer:
    """旺衰分析器

    根据月令判断用神的旺衰状态。
    """

    @classmethod
    def analyze(
        cls,
        hexagram: Hexagram,
        yong_shen: SixRelation,
        month_branch: str,
        day_branch: str | None = None,
    ) -> ProsperityAnalysis:
        """分析用神旺衰（含可选的日辰分析）

        Args:
            hexagram: 卦对象
            yong_shen: 用神六亲
            month_branch: 月份地支（如"子"、"丑"等）
            day_branch: 日辰地支（可选，如"子"、"丑"等）

        Returns:
            旺衰分析结果

        Raises:
            ValueError: 如果地支无效或卦中未找到用神
        """
        # 获取月令五行
        month_element = ElementEngine.get_element_by_branch(month_branch)

        # 找到用神爻的五行
        yong_shen_element = cls._find_yong_shen_element(hexagram, yong_shen)

        # 判断旺衰
        prosperity_state = ElementEngine.judge_prosperity(
            yong_shen_element, month_branch
        )

        # 获取描述
        description = _PROSPERITY_DESCRIPTIONS[prosperity_state]

        # 日辰分析（可选）
        day_branch_analysis = None
        if day_branch is not None:
            day_branch_analysis = cls.analyze_day_branch(
                hexagram, yong_shen, day_branch
            )

        return ProsperityAnalysis(
            month_element=month_element,
            yong_shen_element=yong_shen_element,
            prosperity_state=prosperity_state,
            description=description,
            day_branch_analysis=day_branch_analysis,
        )

    @classmethod
    def analyze_day_branch(
        cls,
        hexagram: Hexagram,
        yong_shen: SixRelation,
        day_branch: str,
    ) -> DayBranchAnalysis:
        """分析日辰对用神的影响

        依据《卜筮正宗》："日辰为六爻之主宰"，"日辰主要定用爻的生旺墓绝空等"。

        通过长生十二宫判断用神在日辰的生命周期状态。

        Args:
            hexagram: 卦对象
            yong_shen: 用神六亲
            day_branch: 日辰地支（如"子"、"丑"等）

        Returns:
            日辰分析结果

        Raises:
            ValueError: 如果地支无效或卦中未找到用神
        """
        day_element = ElementEngine.get_element_by_branch(day_branch)
        yong_shen_element = cls._find_yong_shen_element(hexagram, yong_shen)

        # 获取完整的长生十二宫阶段
        lifecycle_stage = cls._get_full_lifecycle_stage(
            yong_shen_element, day_branch
        )

        # 获取简化生命周期状态
        lifecycle = _get_lifecycle(yong_shen_element, day_branch)

        description = _LIFECYCLE_DESCRIPTIONS[lifecycle]

        return DayBranchAnalysis(
            day_branch=day_branch,
            day_element=day_element,
            yong_shen_lifecycle=lifecycle,
            lifecycle_stage=lifecycle_stage,
            description=description,
        )

    @staticmethod
    def _get_full_lifecycle_stage(
        element: Element, branch: str
    ) -> LifecycleStage:
        """获取五行在指定地支的完整长生十二宫阶段

        Args:
            element: 五行属性
            branch: 地支

        Returns:
            完整的长生十二宫阶段
        """
        birth_branch = _CHANG_SHENG_BRANCH[element]
        birth_idx = _BRANCH_ORDER.index(birth_branch)
        branch_idx = _BRANCH_ORDER.index(branch)
        offset = (branch_idx - birth_idx) % 12
        return list(LifecycleStage)[offset]

    @classmethod
    def _find_yong_shen_element(
        cls, hexagram: Hexagram, yong_shen: SixRelation
    ) -> Element:
        """找到用神爻的五行属性

        Args:
            hexagram: 卦对象
            yong_shen: 用神六亲

        Returns:
            用神的五行属性

        Raises:
            ValueError: 如果卦中未找到用神
        """
        for line in hexagram.lines:
            if line.six_relation == yong_shen:
                return line.element
        raise ValueError(f"卦中未找到用神 {yong_shen.value} 对应的爻")
