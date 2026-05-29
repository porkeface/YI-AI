"""起卦路由

实现时间起卦、数字起卦、手动排盘三种方式，
并整合卦象充实、变卦计算、规则分析等完整流程。
"""

from __future__ import annotations

import time as time_module
from datetime import datetime

import structlog
from fastapi import APIRouter

from api.schemas import ApiResponse, DivinationRequest
from foundation.types import (
    Element,
    Hexagram,
    Line,
    ProsperityState,
    RuleAnalysisResult,
    SixRelation,
    SixSpirit,
    Verdict,
    YinYang,
)
from foundation.element_engine import ElementEngine
from foundation.gan_zhi_engine import GanZhiEngine
from foundation.hexagram_engine import HexagramEngine
from foundation.six_relation_engine import SixRelationEngine
from foundation.six_spirit_engine import SixSpiritEngine
from foundation.shi_ying_engine import ShiYingEngine
from rule_engine.analyzer import Analyzer

logger = structlog.get_logger()
router = APIRouter(prefix="/api/divination", tags=["divination"])


# ============================================================================
# AI解释器（懒加载）
# ============================================================================

_ai_interpreter = None
_ai_init_attempted = False


def _get_ai_interpreter():
    """获取AI解释器单例（懒加载）

    首次调用时尝试初始化，失败后不再重试。
    未配置API Key时返回None，不影响主流程。

    Returns:
        AIInterpreter实例，或None（不可用时）
    """
    global _ai_interpreter, _ai_init_attempted

    if _ai_init_attempted:
        return _ai_interpreter

    _ai_init_attempted = True

    try:
        from ai.config import get_default_config
        from ai.llm_client import LLMClient
        from ai.interpreter import AIInterpreter
        from ai.knowledge_base import KnowledgeBase

        config = get_default_config()
        llm_client = LLMClient(config)
        knowledge_base = KnowledgeBase()
        _ai_interpreter = AIInterpreter(llm_client, knowledge_base)
        logger.info(
            "ai_interpreter_initialized",
            provider=config.provider,
            model=config.model,
        )
    except ValueError as e:
        # API Key未配置，这是正常情况
        logger.info("ai_interpreter_unavailable", reason=str(e))
        _ai_interpreter = None
    except Exception as e:
        logger.error("ai_interpreter_init_failed", error=str(e), exc_info=True)
        _ai_interpreter = None

    return _ai_interpreter


# ============================================================================
# 常量
# ============================================================================

# 先天八卦序号到二进制映射（mod 8: 0=坤, 1=乾, 2=兑, ..., 7=艮）
_TRIGRAM_NUM_TO_BINARY: dict[int, str] = {
    0: "000",  # 坤
    1: "111",  # 乾
    2: "110",  # 兑
    3: "101",  # 离
    4: "100",  # 震
    5: "011",  # 巽
    6: "010",  # 坎
    7: "001",  # 艮
}

# 问题关键词到用神类型的映射
_QUESTION_KEYWORDS: dict[str, str] = {
    "事业": "事业",
    "工作": "工作",
    "升职": "事业",
    "升迁": "事业",
    "财运": "财运",
    "钱": "财运",
    "财": "财运",
    "生意": "生意",
    "考试": "考试",
    "学习": "考试",
    "文书": "文书",
    "成绩": "考试",
    "婚姻": "婚姻",
    "感情": "婚姻",
    "恋爱": "婚姻",
    "爱情": "婚姻",
    "健康": "健康",
    "病": "疾病",
    "身体": "健康",
    "医疗": "疾病",
    "出行": "出行",
    "旅游": "出行",
    "旅行": "出行",
    "子女": "子女",
    "生育": "生育",
    "孩子": "子女",
    "官司": "官司",
    "诉讼": "诉讼",
    "法律": "官司",
    "兄弟": "兄弟",
    "朋友": "朋友",
}


# ============================================================================
# 辅助函数
# ============================================================================


def _extract_question_type(question: str) -> str:
    """从问题文本中提取问题类型

    通过关键词匹配确定问题所属类别，用于选取用神。

    Args:
        question: 用户问题文本

    Returns:
        问题类型字符串（如"事业"、"财运"等）
    """
    for keyword, q_type in _QUESTION_KEYWORDS.items():
        if keyword in question:
            return q_type
    return "通用"


def _trigrams_to_yin_yangs(upper_num: int, lower_num: int) -> list[YinYang]:
    """将上下卦序号转换为6个阴阳值

    Args:
        upper_num: 上卦序号(0-7)
        lower_num: 下卦序号(0-7)

    Returns:
        6个阴阳值列表（从下到上）
    """
    upper_binary = _TRIGRAM_NUM_TO_BINARY[upper_num]
    lower_binary = _TRIGRAM_NUM_TO_BINARY[lower_num]
    # 二进制从下到上：lower(1-3爻) + upper(4-6爻)
    full_binary = lower_binary + upper_binary
    return [YinYang.YANG if b == "1" else YinYang.YIN for b in full_binary]


def _generate_lines_from_time() -> tuple[list[YinYang], list[int]]:
    """时间起卦

    使用当前时间戳生成上下卦和动爻。
    算法：时间戳对8取余得上下卦，对6取余得动爻位。

    Returns:
        (阴阳值列表, 动爻位置列表)
    """
    ts = int(time_module.time() * 1000)
    upper_num = ts % 8
    lower_num = (ts // 100) % 8
    moving_pos = ts % 6 + 1

    yin_yangs = _trigrams_to_yin_yangs(upper_num, lower_num)
    return yin_yangs, [moving_pos]


def _generate_lines_from_numbers(
    numbers: list[int],
) -> tuple[list[YinYang], list[int]]:
    """数字起卦

    两个数字分别对8取余得上下卦，两数之和对6取余得动爻位。

    Args:
        numbers: 两个数字

    Returns:
        (阴阳值列表, 动爻位置列表)
    """
    num1, num2 = numbers[0], numbers[1]
    upper_num = num1 % 8
    lower_num = num2 % 8
    moving_pos = (num1 + num2) % 6 + 1

    yin_yangs = _trigrams_to_yin_yangs(upper_num, lower_num)
    return yin_yangs, [moving_pos]


def _generate_lines_from_manual(
    manual_lines: list[int],
    moving_positions: list[int] | None,
) -> tuple[list[YinYang], list[int]]:
    """手动排盘

    Args:
        manual_lines: 6个阴阳值（0=阴，1=阳）
        moving_positions: 动爻位置列表，None则用当前时间推算

    Returns:
        (阴阳值列表, 动爻位置列表)
    """
    yin_yangs = [YinYang.YANG if v == 1 else YinYang.YIN for v in manual_lines]

    if moving_positions is None:
        ts = int(time_module.time() * 1000)
        moving_pos = ts % 6 + 1
        moving_positions = [moving_pos]

    return yin_yangs, moving_positions


def _enrich_hexagram(
    hexagram: Hexagram,
    moving_positions: list[int],
    day_stem: str,
) -> Hexagram:
    """充实卦数据

    为HexagramEngine创建的基础卦添加完整的六亲、六神、干支、世应信息。
    基础卦的爻只有position和yin_yang是正确的，其余字段为默认值。

    Args:
        hexagram: 基础卦对象
        moving_positions: 动爻位置列表
        day_stem: 日干（用于排六神）

    Returns:
        充实后的卦对象
    """
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


def _get_palace_name(hexagram: Hexagram) -> str:
    """获取卦所属宫位

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


def _hexagram_to_response(hexagram: Hexagram) -> dict:
    """将卦对象转换为前端期望的camelCase格式

    Args:
        hexagram: 卦对象

    Returns:
        可序列化的字典（camelCase格式）
    """
    palace = _get_palace_name(hexagram)

    lines = []
    for line in hexagram.lines:
        gan = line.gan_zhi[0] if line.gan_zhi else ""
        zhi = line.gan_zhi[1] if len(line.gan_zhi) > 1 else ""
        lines.append({
            "position": line.position,
            "yinYang": line.yin_yang.value,
            "isMoving": line.is_moving,
            "element": line.element.value,
            "sixRelation": line.six_relation.value,
            "sixSpirit": line.six_spirit.value,
            "ganZhi": {"gan": gan, "zhi": zhi},
            "isShi": line.is_shi,
            "isYing": line.is_ying,
        })

    return {
        "id": hexagram.id,
        "name": hexagram.name,
        "fullName": f"{hexagram.name}（{palace}宫）",
        "palace": palace,
        "upperTrigram": hexagram.upper_trigram.name.value,
        "lowerTrigram": hexagram.lower_trigram.name.value,
        "lines": lines,
        "element": hexagram.element.value,
        "judgment": hexagram.judgment,
        "image": hexagram.image,
    }


def _default_analysis_result(moving_positions: list[int]) -> RuleAnalysisResult:
    """分析失败时的默认结果"""
    return RuleAnalysisResult(
        yong_shen=SixRelation.BROTHER,
        moving_lines=tuple(moving_positions),
        relationships=("分析数据不足",),
        prosperity=ProsperityState.XIU,
        verdict=Verdict(
            overall="平",  # type: ignore[arg-type]
            strength=50,
            trend="平稳",  # type: ignore[arg-type]
            confidence=30,
        ),
    )


def _generate_advice(analysis: RuleAnalysisResult) -> str:
    """根据分析结果生成建议文本"""
    overall = analysis.verdict.overall
    strength = analysis.verdict.strength
    trend = analysis.verdict.trend

    parts = []
    if overall == "吉":
        parts.append("此卦整体吉利，事宜推进。")
    elif overall == "凶":
        parts.append("此卦整体不利，宜守不宜攻。")
    else:
        parts.append("此卦平稳，宜按部就班。")

    if strength >= 70:
        parts.append("力量充沛，可积极行动。")
    elif strength <= 30:
        parts.append("力量不足，宜积蓄待机。")

    if trend == "上升":
        parts.append("趋势向上，前景看好。")
    elif trend == "下降":
        parts.append("趋势下行，需谨慎应对。")
    else:
        parts.append("趋势平稳，保持现状为宜。")

    return "".join(parts)


def _format_analysis(analysis: RuleAnalysisResult, hexagram: Hexagram) -> dict:
    """将规则分析结果转换为前端展示格式

    Args:
        analysis: 规则分析结果
        hexagram: 卦对象

    Returns:
        前端期望的camelCase格式字典
    """
    key_points = []
    key_points.append(f"用神：{analysis.yong_shen.value}")
    if analysis.moving_lines:
        key_points.append(f"动爻：第{'、'.join(str(p) for p in analysis.moving_lines)}爻")
    key_points.append(f"旺衰：{analysis.prosperity.value}")
    for rel in analysis.relationships[:3]:
        key_points.append(rel)

    advice = _generate_advice(analysis)

    return {
        "fortune": analysis.verdict.overall,
        "summary": f"综合分析：{analysis.verdict.overall}，力量{analysis.verdict.strength}%，趋势{analysis.verdict.trend}",
        "advice": advice,
        "keyPoints": key_points,
        "details": {
            "yongShen": analysis.yong_shen.value,
            "movingLines": list(analysis.moving_lines),
            "relationships": list(analysis.relationships),
            "prosperity": analysis.prosperity.value,
            "verdict": {
                "overall": analysis.verdict.overall,
                "strength": analysis.verdict.strength,
                "trend": analysis.verdict.trend,
                "confidence": analysis.verdict.confidence,
            },
        },
    }


def _get_current_gan_zhi() -> tuple[str, str]:
    """获取当前时间的日干和月支

    Returns:
        (日干, 月支)
    """
    now = datetime.now()
    try:
        gan_zhi = GanZhiEngine.time_to_gan_zhi(
            now.year, now.month, now.day, now.hour
        )
        day_stem = gan_zhi["day"][0]
        month_branch = gan_zhi["month"][1]
        return day_stem, month_branch
    except (IndexError, ValueError):
        return "甲", "子"


# ============================================================================
# 路由
# ============================================================================


@router.get("/methods")
async def get_methods():
    """获取起卦方式列表"""
    return {
        "methods": [
            {
                "value": "time",
                "label": "时间起卦",
                "description": "使用当前时间自动起卦",
            },
            {
                "value": "number",
                "label": "数字起卦",
                "description": "输入两个数字起卦",
            },
            {
                "value": "manual",
                "label": "手动排盘",
                "description": "手动选择每爻阴阳",
            },
        ]
    }


@router.post("/", response_model=ApiResponse)
async def create_divination(request: DivinationRequest):
    """起卦

    完整流程：
    1. 根据起卦方式生成6个阴阳值和动爻位置
    2. 创建基础卦
    3. 充实卦数据（六亲、六神、干支、世应）
    4. 计算变卦
    5. 进行规则分析
    6. 返回完整结果
    """
    # ---- 1. 生成阴阳值和动爻 ----
    if request.method == "time":
        yin_yangs, moving_positions = _generate_lines_from_time()

    elif request.method == "number":
        if not request.numbers or len(request.numbers) < 2:
            return ApiResponse(
                success=False,
                error="数字起卦需要提供两个数字",
            )
        yin_yangs, moving_positions = _generate_lines_from_numbers(request.numbers)

    elif request.method == "manual":
        if not request.manual_lines or len(request.manual_lines) != 6:
            return ApiResponse(
                success=False,
                error="手动排盘需要提供6个阴阳值(0/1)",
            )
        if any(v not in (0, 1) for v in request.manual_lines):
            return ApiResponse(
                success=False,
                error="阴阳值只能是0(阴)或1(阳)",
            )
        yin_yangs, moving_positions = _generate_lines_from_manual(
            request.manual_lines, request.moving_positions
        )

    else:
        return ApiResponse(
            success=False,
            error=f"不支持的起卦方式: {request.method}",
        )

    # ---- 2. 创建基础卦 ----
    try:
        hexagram = HexagramEngine.create(yin_yangs)
    except ValueError as e:
        return ApiResponse(success=False, error=f"创建卦失败: {e}")

    # ---- 3. 获取当前干支 ----
    day_stem, month_branch = _get_current_gan_zhi()

    # ---- 4. 充实卦数据 ----
    enriched_hexagram = _enrich_hexagram(hexagram, moving_positions, day_stem)

    # ---- 5. 计算变卦 ----
    changed_hexagram: Hexagram | None = None
    if moving_positions:
        try:
            changed = HexagramEngine.get_changed(
                hexagram, tuple(moving_positions)
            )
            changed_hexagram = _enrich_hexagram(changed, [], day_stem)
        except (ValueError, IndexError) as e:
            logger.warning("changed_hexagram_error", error=str(e))
            changed_hexagram = None

    # ---- 6. 规则分析 ----
    question_type = _extract_question_type(request.question)
    try:
        analysis_result = Analyzer.analyze(
            enriched_hexagram, question_type, month_branch
        )
    except ValueError as e:
        logger.warning("rule_analysis_fallback", error=str(e))
        analysis_result = _default_analysis_result(moving_positions)
    except Exception as e:
        logger.error("rule_analysis_unexpected_error", error=str(e), exc_info=True)
        analysis_result = _default_analysis_result(moving_positions)

    # ---- 7. AI解释（可选，失败不影响主流程） ----
    ai_interpretation: str | None = None
    interpreter = _get_ai_interpreter()
    if interpreter is not None:
        try:
            from ai.safety_checker import check_safety

            raw_text = await interpreter.interpret(
                request.question, enriched_hexagram, analysis_result, question_type
            )
            check_result = check_safety(raw_text)
            ai_interpretation = check_result.text
            if check_result.warnings:
                logger.info(
                    "ai_safety_warnings",
                    warnings=check_result.warnings,
                )
        except Exception as e:
            logger.warning("ai_interpretation_failed", error=str(e))
            ai_interpretation = None

    # ---- 8. 构建响应 ----
    hexagram_response = _hexagram_to_response(enriched_hexagram)
    changed_response = (
        _hexagram_to_response(changed_hexagram)
        if changed_hexagram
        else None
    )

    analysis_response = _format_analysis(analysis_result, enriched_hexagram)

    data = {
        "hexagram": hexagram_response,
        "changedHexagram": changed_response,
        "analysis": analysis_response,
        "aiInterpretation": ai_interpretation,
    }

    return ApiResponse(success=True, data=data)
