"""紫微斗数API

提供紫微斗数命盘排盘和分析服务。
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter

from api.schemas import ApiResponse, ZiWeiRequest
from foundation.ziwei_engine import ZiWeiEngine

logger = structlog.get_logger()
router = APIRouter(prefix="/api/ziwei", tags=["ziwei"])


@router.post("/chart", response_model=ApiResponse)
async def create_ziwei_chart(request: ZiWeiRequest):
    """排紫微斗数命盘

    根据出生时间和性别排出完整的紫微斗数命盘。
    """
    try:
        chart = ZiWeiEngine.generate_chart(
            request.year, request.month, request.day,
            request.hour, request.gender,
        )
    except Exception as e:
        logger.error("ziwei_chart_error", error=str(e), exc_info=True)
        return ApiResponse(success=False, error=f"排盘失败: {e}")

    palaces_data = []
    for p in chart.palaces:
        palaces_data.append({
            "palace": p.palace.value,
            "ganZhi": p.gan_zhi,
            "mainStars": [s.value for s in p.main_stars],
            "auxStars": [s.value for s in p.aux_stars],
            "brightness": list(p.brightness),
            "huaStars": [h.value for h in p.hua_stars],
            "isBodyPalace": p.is_body_palace,
        })

    data = {
        "palaces": palaces_data,
        "yearGanZhi": chart.year_gan_zhi,
        "monthGanZhi": chart.month_gan_zhi,
        "dayGanZhi": chart.day_gan_zhi,
        "hourGanZhi": chart.hour_gan_zhi,
        "gender": chart.gender,
        "wuXingJu": chart.wu_xing_ju,
        "mingPalace": chart.ming_palace.value,
        "shenPalace": chart.shen_palace.value,
    }

    return ApiResponse(success=True, data=data)


@router.post("/analyze", response_model=ApiResponse)
async def analyze_ziwei(request: ZiWeiRequest):
    """紫微斗数分析

    排盘并分析指定宫位的吉凶。
    """
    try:
        chart = ZiWeiEngine.generate_chart(
            request.year, request.month, request.day,
            request.hour, request.gender,
        )
    except Exception as e:
        logger.error("ziwei_chart_error", error=str(e), exc_info=True)
        return ApiResponse(success=False, error=f"排盘失败: {e}")

    try:
        analysis = ZiWeiEngine.analyze_chart(chart, request.question_type)
    except Exception as e:
        logger.error("ziwei_analyze_error", error=str(e), exc_info=True)
        return ApiResponse(success=False, error=f"分析失败: {e}")

    data = {
        "targetPalace": analysis.target_palace.value,
        "mainStars": [s.value for s in analysis.main_stars],
        "huaInfluence": [h.value for h in analysis.hua_influence],
        "description": analysis.description,
        "verdict": {
            "overall": analysis.verdict.overall,
            "strength": analysis.verdict.strength,
            "trend": analysis.verdict.trend,
            "confidence": analysis.verdict.confidence,
        },
    }

    return ApiResponse(success=True, data=data)
