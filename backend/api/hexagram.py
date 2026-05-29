"""卦象查询路由

提供64卦的列表查询、详情查询和名称搜索功能。
"""

from __future__ import annotations

from fastapi import APIRouter

from api.schemas import ApiResponse
from foundation.hexagram_engine import HexagramEngine
from foundation.shi_ying_engine import ShiYingEngine
from foundation.types import Hexagram, Line

router = APIRouter(prefix="/api/hexagram", tags=["hexagram"])


def _get_palace_name(hexagram: Hexagram) -> str:
    """获取卦所属宫位"""
    try:
        palace_full = ShiYingEngine.get_palace(hexagram.name)
        return palace_full.replace("宫", "")
    except ValueError:
        return "未知"


def _line_to_dict(line: Line) -> dict:
    """将爻对象转换为camelCase字典"""
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


def _hexagram_to_dict(hexagram: Hexagram) -> dict:
    """将卦对象转换为完整camelCase字典"""
    palace = _get_palace_name(hexagram)
    return {
        "id": hexagram.id,
        "name": hexagram.name,
        "fullName": f"{hexagram.name}（{palace}宫）",
        "palace": palace,
        "upperTrigram": hexagram.upper_trigram.name.value,
        "lowerTrigram": hexagram.lower_trigram.name.value,
        "lines": [_line_to_dict(line) for line in hexagram.lines],
        "element": hexagram.element.value,
        "judgment": hexagram.judgment,
        "image": hexagram.image,
    }


def _hexagram_to_summary(hexagram: Hexagram) -> dict:
    """将卦对象转换为camelCase摘要字典"""
    palace = _get_palace_name(hexagram)
    return {
        "id": hexagram.id,
        "name": hexagram.name,
        "fullName": f"{hexagram.name}（{palace}宫）",
        "palace": palace,
        "upperTrigram": hexagram.upper_trigram.name.value,
        "lowerTrigram": hexagram.lower_trigram.name.value,
        "element": hexagram.element.value,
    }


@router.get("/")
async def list_hexagrams():
    """获取所有64卦列表"""
    hexagrams = HexagramEngine.get_all_hexagrams()
    data = [_hexagram_to_summary(h) for h in hexagrams]
    return ApiResponse(success=True, data=data)


@router.get("/{hexagram_id}")
async def get_hexagram(hexagram_id: int):
    """获取单个卦详情

    Args:
        hexagram_id: 卦序号(1-64)
    """
    try:
        hexagram = HexagramEngine.get_by_id(hexagram_id)
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))

    return ApiResponse(success=True, data=_hexagram_to_dict(hexagram))


@router.get("/search/{name}")
async def search_hexagram(name: str):
    """按名称搜索卦（支持模糊匹配）

    Args:
        name: 搜索关键词
    """
    hexagrams = HexagramEngine.get_all_hexagrams()
    results = [
        _hexagram_to_summary(h)
        for h in hexagrams
        if name in h.name
    ]
    return ApiResponse(success=True, data=results)
