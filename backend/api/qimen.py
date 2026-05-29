"""奇门遁甲API

提供奇门遁甲排盘和分析服务。
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter

from api.schemas import ApiResponse, QiMenRequest
from foundation.qimen_engine import QiMenEngine

logger = structlog.get_logger()
router = APIRouter(prefix="/api/qimen", tags=["qimen"])


@router.post("/chart", response_model=ApiResponse)
async def create_qimen_chart(request: QiMenRequest):
    """排奇门遁甲盘

    根据时间排出完整的奇门遁甲盘，包括九宫、八门、九星、八神等信息。
    """
    try:
        chart = QiMenEngine.time_to_chart(
            request.year, request.month, request.day, request.hour
        )
    except Exception as e:
        logger.error("qimen_chart_error", error=str(e), exc_info=True)
        return ApiResponse(success=False, error=f"排盘失败: {e}")

    palace_data = []
    for p in chart.palace_info:
        palace_data.append({
            "palace": p.palace.value,
            "door": p.door.value,
            "star": p.star.value,
            "spirit": p.spirit.value,
            "tianPan": p.tian_pan,
            "diPan": p.di_pan,
            "isShi": p.is_shi,
            "isFuxing": p.is_fuxing,
            "isFanin": p.is_fanin,
        })

    data = {
        "ju": chart.ju,
        "yinYang": chart.yin_yang,
        "dun": chart.dun,
        "palaceInfo": palace_data,
        "yearGanZhi": chart.year_gan_zhi,
        "monthGanZhi": chart.month_gan_zhi,
        "dayGanZhi": chart.day_gan_zhi,
        "hourGanZhi": chart.hour_gan_zhi,
        "xunKong": list(chart.xun_kong),
        "maXing": chart.ma_xing,
    }

    return ApiResponse(success=True, data=data)


@router.post("/analyze", response_model=ApiResponse)
async def analyze_qimen(request: QiMenRequest):
    """奇门遁甲分析

    排盘并分析，给出吉凶判断和用神分析。
    """
    try:
        chart = QiMenEngine.time_to_chart(
            request.year, request.month, request.day, request.hour
        )
    except Exception as e:
        logger.error("qimen_chart_error", error=str(e), exc_info=True)
        return ApiResponse(success=False, error=f"排盘失败: {e}")

    try:
        analysis = QiMenEngine.analyze_chart(chart, request.question_type)
    except Exception as e:
        logger.error("qimen_analyze_error", error=str(e), exc_info=True)
        return ApiResponse(success=False, error=f"分析失败: {e}")

    data = {
        "yongShenPalace": analysis.yong_shen_palace.value,
        "yongShenDoor": analysis.yong_shen_door.value,
        "yongShenStar": analysis.yong_shen_star.value,
        "description": analysis.description,
        "verdict": {
            "overall": analysis.verdict.overall,
            "strength": analysis.verdict.strength,
            "trend": analysis.verdict.trend,
            "confidence": analysis.verdict.confidence,
        },
    }

    return ApiResponse(success=True, data=data)
