"""API请求/响应模型定义

定义所有API端点使用的Pydantic v2数据模型。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# 请求模型
# ============================================================================


class DivinationRequest(BaseModel):
    """起卦请求"""

    question: str = Field(..., description="用户问题", max_length=2000)
    method: str = Field("time", description="起卦方式: time/number/manual/plum_blossom")
    manual_lines: list[int] | None = Field(
        None, description="手动输入的6个阴阳值(0=阴/1=阳)"
    )
    numbers: list[int] | None = Field(
        None, description="数字起卦的两个数字"
    )
    moving_positions: list[int] | None = Field(
        None, description="动爻位置(1-6)，仅manual模式可选"
    )
    pb_numbers: list[int] | None = Field(
        None, description="梅花易数的两个数字"
    )
    pb_basis: str | None = Field(
        "先天数", description="梅花易数数字基准: 先天数/后天数"
    )


class InferenceRequest(BaseModel):
    """推演请求"""

    hexagram_id: int = Field(..., description="卦序号(1-64)")
    question_type: str = Field("通用", description="问题类型")
    max_depth: int = Field(3, description="推演深度(1-3)", ge=1, le=3)


# ============================================================================
# 响应模型
# ============================================================================


class LineResponse(BaseModel):
    """爻响应"""

    position: int = Field(..., description="爻位(1-6，从下到上)")
    yin_yang: str = Field(..., description="阴阳: yin/yang")
    is_moving: bool = Field(..., description="是否为动爻")
    element: str = Field(..., description="五行")
    six_relation: str = Field(..., description="六亲")
    six_spirit: str = Field(..., description="六神")
    gan_zhi: str = Field(..., description="干支")
    is_shi: bool = Field(..., description="是否为世爻")
    is_ying: bool = Field(..., description="是否为应爻")


class HexagramResponse(BaseModel):
    """卦响应"""

    id: int = Field(..., description="卦序号(1-64)")
    name: str = Field(..., description="卦名")
    upper_trigram: str = Field(..., description="上卦")
    lower_trigram: str = Field(..., description="下卦")
    lines: list[LineResponse] = Field(..., description="六爻数据")
    element: str = Field(..., description="卦的五行属性")
    judgment: str = Field(..., description="卦辞")
    image: str = Field(..., description="象辞")


class HexagramSummaryResponse(BaseModel):
    """卦摘要响应（用于列表）"""

    id: int
    name: str
    upper_trigram: str
    lower_trigram: str
    element: str


class VerdictResponse(BaseModel):
    """结论响应"""

    overall: str = Field(..., description="总体判断: 吉/凶/平")
    strength: int = Field(..., description="力量强度(0-100)")
    trend: str = Field(..., description="趋势: 上升/下降/平稳")
    confidence: int = Field(..., description="置信度(0-100)")


class AnalysisResponse(BaseModel):
    """规则分析响应"""

    yong_shen: str = Field(..., description="用神(六亲)")
    moving_lines: list[int] = Field(..., description="动爻位置列表")
    relationships: list[str] = Field(..., description="爻之间的关系描述")
    prosperity: str = Field(..., description="用神旺衰状态")
    verdict: VerdictResponse = Field(..., description="占卜结论")


class DivinationResponse(BaseModel):
    """起卦完整响应"""

    hexagram: HexagramResponse = Field(..., description="本卦")
    changed_hexagram: HexagramResponse | None = Field(
        None, description="变卦(有动爻时存在)"
    )
    analysis: AnalysisResponse = Field(..., description="规则分析结果")
    ai_interpretation: str | None = Field(None, description="AI解读(预留)")


class ApiResponse(BaseModel):
    """统一API响应格式"""

    success: bool = Field(..., description="请求是否成功")
    data: Any | None = Field(None, description="响应数据")
    error: str | None = Field(None, description="错误信息")


# ============================================================================
# 历史记录模型
# ============================================================================


class HistorySaveRequest(BaseModel):
    """保存历史记录请求"""

    question: str
    method: str
    hexagram_data: dict
    changed_hexagram_data: dict | None = None
    analysis_data: dict


class HistoryRecordResponse(BaseModel):
    """历史记录响应"""

    id: int
    question: str
    method: str
    hexagram_name: str
    fortune: str
    created_at: str
    hexagram_data: dict
    changed_hexagram_data: dict | None = None
    analysis_data: dict


class HistoryListResponse(BaseModel):
    """历史列表响应"""

    records: list[HistoryRecordResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# ============================================================================
# Phase 3 新增模型
# ============================================================================


class DeepReasoningRequest(BaseModel):
    """深度推演请求"""

    hexagram_name: str = Field(..., description="卦名（如'乾为天'）")
    question_type: str = Field("通用", description="问题类型")
    month_branch: str = Field("子", description="月份地支")
    max_steps: int = Field(10, description="推理步数(1-10)", ge=1, le=10)


class ProbabilityTreeRequest(BaseModel):
    """概率树推演请求"""

    hexagram_name: str = Field(..., description="卦名（如'乾为天'）")
    question_type: str = Field("通用", description="问题类型")
    month_branch: str = Field("子", description="月份地支")
    max_depth: int = Field(5, description="树深度(1-10)", ge=1, le=10)


class QiMenRequest(BaseModel):
    """奇门遁甲排盘请求"""

    year: int = Field(..., description="公历年份")
    month: int = Field(..., description="月份(1-12)", ge=1, le=12)
    day: int = Field(..., description="日期(1-31)", ge=1, le=31)
    hour: int = Field(..., description="时辰(0-23)", ge=0, le=23)
    question_type: str = Field("general", description="问题类型: general/career/wealth/health/lawsuit")


class ZiWeiRequest(BaseModel):
    """紫微斗数排盘请求"""

    year: int = Field(..., description="出生公历年份")
    month: int = Field(..., description="出生月份(1-12)", ge=1, le=12)
    day: int = Field(..., description="出生日期(1-31)", ge=1, le=31)
    hour: int = Field(..., description="出生时辰(0-23)", ge=0, le=23)
    gender: str = Field(..., description="性别: 男/女")
    question_type: str = Field("general", description="问题类型: general/事业/财运/感情/健康/人际")
