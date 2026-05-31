"""卦象数据转换工具模块

提供 Hexagram/Line 对象到前端 camelCase 字典的通用转换函数。
供 divination.py 和 hexagram.py 共用，消除重复代码。
"""

from __future__ import annotations

from foundation.types import Hexagram, Line


def get_palace_name(hexagram: Hexagram) -> str:
    """获取卦所属宫位名称

    Args:
        hexagram: 卦对象

    Returns:
        宫名（如"乾"、"坤"等），查不到时返回"未知"
    """
    from foundation.shi_ying_engine import ShiYingEngine

    try:
        palace_full = ShiYingEngine.get_palace(hexagram.name)
        # palace_full 形如 "乾宫"，去掉"宫"字返回
        return palace_full.replace("宫", "")
    except ValueError:
        return "未知"


def line_to_dict(line: Line) -> dict:
    """将爻对象转换为 camelCase 字典

    Args:
        line: 爻对象

    Returns:
        可序列化的字典
    """
    gan = line.gan_zhi[0] if line.gan_zhi else ""
    zhi = line.gan_zhi[1] if len(line.gan_zhi) > 1 else ""
    return {
        "position": line.position,
        "yinYang": line.yin_yang.value,
        "isMoving": line.is_moving,
        "element": line.element.value,
        "sixRelation": line.six_relation.value,
        "sixSpirit": line.six_spirit.value,
        "ganZhi": {"gan": gan, "zhi": zhi},
        "isShi": line.is_shi,
        "isYing": line.is_ying,
    }


def hexagram_to_dict(hexagram: Hexagram) -> dict:
    """将卦对象转换为完整 camelCase 字典

    Args:
        hexagram: 卦对象

    Returns:
        可序列化的字典（camelCase 格式，含六爻详情）
    """
    palace = get_palace_name(hexagram)
    return {
        "id": hexagram.id,
        "name": hexagram.name,
        "fullName": f"{hexagram.name}（{palace}宫）",
        "palace": palace,
        "upperTrigram": hexagram.upper_trigram.name.value,
        "lowerTrigram": hexagram.lower_trigram.name.value,
        "lines": [line_to_dict(line) for line in hexagram.lines],
        "element": hexagram.element.value,
        "judgment": hexagram.judgment,
        "image": hexagram.image,
    }


def hexagram_to_summary(hexagram: Hexagram) -> dict:
    """将卦对象转换为 camelCase 摘要字典（不含六爻详情）

    Args:
        hexagram: 卦对象

    Returns:
        可序列化的字典（camelCase 格式，仅包含摘要信息）
    """
    palace = get_palace_name(hexagram)
    return {
        "id": hexagram.id,
        "name": hexagram.name,
        "fullName": f"{hexagram.name}（{palace}宫）",
        "palace": palace,
        "upperTrigram": hexagram.upper_trigram.name.value,
        "lowerTrigram": hexagram.lower_trigram.name.value,
        "element": hexagram.element.value,
    }
