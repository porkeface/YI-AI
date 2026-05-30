"""卦象数据充实模块

为HexagramEngine创建的基础卦添加完整的六亲、六神、干支、世应信息。
基础卦的爻只有position和yin_yang是正确的，其余字段为默认值。
"""

from __future__ import annotations

from datetime import datetime

from foundation.types import (
    Element,
    Hexagram,
    Line,
    SixRelation,
    SixSpirit,
)
from foundation.element_engine import ElementEngine
from foundation.gan_zhi_engine import GanZhiEngine
from foundation.six_relation_engine import SixRelationEngine
from foundation.six_spirit_engine import SixSpiritEngine
from foundation.shi_ying_engine import ShiYingEngine


def _get_current_day_stem() -> str:
    """获取当前日干"""
    now = datetime.now()
    try:
        gan_zhi = GanZhiEngine.time_to_gan_zhi(
            now.year, now.month, now.day, now.hour
        )
        return gan_zhi["day"][0]
    except (IndexError, ValueError):
        return "甲"


def enrich_hexagram(
    hexagram: Hexagram,
    moving_positions: list[int] | None = None,
    day_stem: str | None = None,
) -> Hexagram:
    """充实卦数据

    为HexagramEngine创建的基础卦添加完整的六亲、六神、干支、世应信息。

    Args:
        hexagram: 基础卦对象
        moving_positions: 动爻位置列表，默认为空（所有爻不动）
        day_stem: 日干（用于排六神），默认使用今天

    Returns:
        充实后的卦对象
    """
    if moving_positions is None:
        moving_positions = []

    # 1. 获取纳甲干支（每爻的干支）
    try:
        najia = GanZhiEngine.get_najia(hexagram.name)
    except ValueError:
        najia = ["甲子", "甲寅", "甲辰", "壬午", "壬申", "壬戌"]

    # 2. 从干支地支推导各爻五行
    line_elements: list[Element] = []
    for gz in najia:
        branch = gz[1]  # 第二个字符是地支
        try:
            element = ElementEngine.get_element_by_branch(branch)
        except ValueError:
            element = Element.EARTH
        line_elements.append(element)

    # 3. 分配六亲（根据卦五行与爻五行的关系）
    try:
        relations = SixRelationEngine.assign(hexagram.element, line_elements)
    except ValueError:
        relations = [SixRelation.BROTHER] * 6

    # 4. 分配六神（根据日干）
    if day_stem is None:
        day_stem = _get_current_day_stem()
    try:
        spirits = SixSpiritEngine.assign(day_stem)
    except ValueError:
        spirits = [SixSpirit.QINGLONG] * 6

    # 5. 获取世应位置
    try:
        shi_pos, ying_pos = ShiYingEngine.get_shi_ying(hexagram.id)
    except (ValueError, IndexError):
        shi_pos, ying_pos = 6, 3

    # 6. 创建充实后的爻
    enriched_lines: list[Line] = []
    for i, line in enumerate(hexagram.lines):
        enriched_lines.append(
            Line(
                position=line.position,
                yin_yang=line.yin_yang,
                is_moving=(line.position in moving_positions),
                element=line_elements[i],
                six_relation=relations[i],
                six_spirit=spirits[i],
                gan_zhi=najia[i],
                is_shi=(line.position == shi_pos),
                is_ying=(line.position == ying_pos),
            )
        )

    # 7. 创建充实后的卦
    return Hexagram(
        id=hexagram.id,
        name=hexagram.name,
        upper_trigram=hexagram.upper_trigram,
        lower_trigram=hexagram.lower_trigram,
        lines=tuple(enriched_lines),  # type: ignore[arg-type]
        element=hexagram.element,
        judgment=hexagram.judgment,
        image=hexagram.image,
    )
