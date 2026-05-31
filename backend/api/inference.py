"""推演引擎API

提供基于卦象的状态推演服务。
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter

from api.schemas import ApiResponse, InferenceRequest
from foundation.hexagram_engine import HexagramEngine
from rule_engine.inference_engine import InferenceEngine

logger = structlog.get_logger()
router = APIRouter(prefix="/api/inference", tags=["inference"])


@router.post("/", response_model=ApiResponse)
async def create_inference(request: InferenceRequest):
    """执行推演

    基于指定卦象进行多步推演，返回状态转移路径。
    """
    # 1. 获取卦象
    try:
        hexagram = HexagramEngine.get_by_id(request.hexagram_id)
    except (ValueError, IndexError) as e:
        return ApiResponse(success=False, error=f"无效的卦序号: {e}")

    # 2. 进行规则分析
    from rule_engine.analyzer import Analyzer

    try:
        analysis = Analyzer.analyze(hexagram, request.question_type)
    except Exception:
        logger.error("analysis_failed_fallback", hexagram_id=request.hexagram_id, exc_info=True)
        # 分析失败时使用默认分析
        from api.divination import _default_analysis_result
        analysis = _default_analysis_result([])

    # 3. 执行推演
    try:
        result = InferenceEngine.infer(
            hexagram, analysis, request.max_depth
        )
    except Exception as e:
        logger.error("inference_error", error=str(e), exc_info=True)
        return ApiResponse(success=False, error=f"推演失败: {e}")

    # 4. 构建响应
    paths_data = []
    for path in result.paths:
        steps_data = []
        for step in path.steps:
            steps_data.append({
                "fromHexagram": step.from_hexagram,
                "toHexagram": step.to_hexagram,
                "trigger": step.trigger,
                "relation": step.relation,
                "probability": step.probability,
                "description": step.description,
            })
        paths_data.append({
            "steps": steps_data,
            "finalHexagram": path.final_hexagram,
            "overallTrend": path.overall_trend,
            "pathProbability": path.path_probability,
            "summary": path.summary,
        })

    recommended_idx = 0
    for i, path in enumerate(result.paths):
        if path is result.recommended_path:
            recommended_idx = i
            break

    data = {
        "sourceHexagram": result.source_hexagram,
        "paths": paths_data,
        "recommendedIndex": recommended_idx,
        "inferenceDepth": result.inference_depth,
        "summary": result.summary,
    }

    return ApiResponse(success=True, data=data)
