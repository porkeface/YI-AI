"""深度推演API

提供深度推理链和概率推演树服务。
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter

from api.schemas import ApiResponse, DeepReasoningRequest, ProbabilityTreeRequest
from ai.reasoning.deep_reasoning import DeepReasoningEngine
from ai.reasoning.probability_tree import ProbabilityTreeEngine

logger = structlog.get_logger()
router = APIRouter(prefix="/api/reasoning", tags=["reasoning"])


@router.post("/deep", response_model=ApiResponse)
async def deep_reason(request: DeepReasoningRequest):
    """深度推演

    执行10步推理链，返回完整推理过程和概率分布。
    """
    try:
        chain = DeepReasoningEngine.reason(
            request.hexagram_name,
            request.question_type,
            request.month_branch,
            request.max_steps,
        )
    except Exception as e:
        logger.error("deep_reasoning_error", error=str(e), exc_info=True)
        return ApiResponse(success=False, error=f"推演失败: {e}")

    steps_data = []
    for step in chain.steps:
        steps_data.append({
            "stepNumber": step.step_number,
            "stepType": step.step_type.value,
            "inputState": step.input_state,
            "logic": step.logic,
            "outputState": step.output_state,
            "confidence": step.confidence.value,
            "elementChanges": list(step.element_changes),
            "relatedHexagrams": list(step.related_hexagrams),
        })

    data = {
        "steps": steps_data,
        "initialHexagram": chain.initial_hexagram,
        "finalHexagram": chain.final_hexagram,
        "branchPoints": list(chain.branch_points),
        "overallConfidence": chain.overall_confidence.value,
        "conclusion": chain.conclusion,
        "trendAnalysis": dict(chain.trend_analysis),
    }

    return ApiResponse(success=True, data=data)


@router.post("/tree", response_model=ApiResponse)
async def probability_tree(request: ProbabilityTreeRequest):
    """概率推演树

    构建概率推演树，枚举所有路径并计算期望值和风险评估。
    """
    try:
        tree = ProbabilityTreeEngine.build_tree(
            request.hexagram_name,
            request.question_type,
            request.month_branch,
            request.max_depth,
        )
    except Exception as e:
        logger.error("probability_tree_error", error=str(e), exc_info=True)
        return ApiResponse(success=False, error=f"构建概率树失败: {e}")

    # 枚举前10条路径
    top_paths = ProbabilityTreeEngine.get_top_paths(tree, n=10)
    paths_data = []
    for path_hexagrams, prob, verdict, score in top_paths:
        paths_data.append({
            "hexagrams": list(path_hexagrams),
            "probability": round(prob, 4),
            "verdict": verdict,
            "score": score,
        })

    data = {
        "maxDepth": tree.max_depth,
        "branchFactor": tree.branch_factor,
        "totalPaths": tree.total_paths,
        "expectedValue": tree.expected_value,
        "riskAssessment": tree.risk_assessment,
        "topPaths": paths_data,
    }

    return ApiResponse(success=True, data=data)
