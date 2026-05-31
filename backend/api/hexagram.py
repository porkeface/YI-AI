"""卦象查询路由

提供64卦的列表查询、详情查询和名称搜索功能。
"""

from __future__ import annotations

from fastapi import APIRouter

from api.schemas import ApiResponse
from api.hexagram_enrich import enrich_hexagram
from api.hexagram_utils import (
    get_palace_name,
    hexagram_to_dict,
    hexagram_to_summary,
)
from foundation.hexagram_engine import HexagramEngine
from foundation.types import Hexagram

router = APIRouter(prefix="/api/hexagram", tags=["hexagram"])


@router.get("/")
async def list_hexagrams():
    """获取所有64卦列表"""
    hexagrams = HexagramEngine.get_all_hexagrams()
    data = [hexagram_to_summary(h) for h in hexagrams]
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

    hexagram = enrich_hexagram(hexagram)
    return ApiResponse(success=True, data=hexagram_to_dict(hexagram))


@router.get("/{hexagram_id}/relationships")
async def get_hexagram_relationships(hexagram_id: int):
    """获取卦的关系（错卦、综卦、互卦）"""
    try:
        hexagram = HexagramEngine.get_by_id(hexagram_id)
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))

    try:
        opposite = HexagramEngine.get_opposite(hexagram)
        reversed_hex = HexagramEngine.get_reversed(hexagram)
        interlock = HexagramEngine.get_interlock(hexagram)
    except ValueError as e:
        return ApiResponse(success=False, error=f"计算关系失败: {e}")

    return ApiResponse(
        success=True,
        data={
            "opposite": hexagram_to_summary(opposite),
            "reversed": hexagram_to_summary(reversed_hex),
            "interlock": hexagram_to_summary(interlock),
        },
    )


@router.get("/search/{name}")
async def search_hexagram(name: str):
    """按名称搜索卦（支持模糊匹配）

    Args:
        name: 搜索关键词
    """
    hexagrams = HexagramEngine.get_all_hexagrams()
    results = [
        hexagram_to_summary(h)
        for h in hexagrams
        if name in h.name
    ]
    return ApiResponse(success=True, data=results)
