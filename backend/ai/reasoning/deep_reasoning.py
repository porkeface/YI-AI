"""深度推演引擎

10步推理链: 分析 -> 推断 -> 比对 -> 演绎 -> 综合 -> 预测 -> 验证 -> 分支 -> 精炼 -> 结论
"""
from __future__ import annotations

from foundation.types import Element, Hexagram, ProsperityState
from foundation.hexagram_engine import HexagramEngine
from foundation.element_engine import ElementEngine

from ai.reasoning.types import (
    StepType, ConfidenceLevel, ReasoningStep, ReasoningChain,
)

_GENERATES: dict[Element, Element] = {
    Element.WOOD: Element.FIRE, Element.FIRE: Element.EARTH,
    Element.EARTH: Element.METAL, Element.METAL: Element.WATER,
    Element.WATER: Element.WOOD,
}
_OVERCOMES: dict[Element, Element] = {
    Element.WOOD: Element.EARTH, Element.EARTH: Element.WATER,
    Element.WATER: Element.FIRE, Element.FIRE: Element.METAL,
    Element.METAL: Element.WOOD,
}
_ELEMENT_QUAL: dict[Element, str] = {
    Element.METAL: "决断收敛", Element.WOOD: "生长扩展",
    Element.WATER: "智慧变通", Element.FIRE: "热情进取",
    Element.EARTH: "稳重包容",
}
_PROSPERITY_DESC: dict[ProsperityState, tuple[str, str]] = {
    ProsperityState.WANG: (
        "当令而旺，力量充沛", "旺相，有利于主动行事"),
    ProsperityState.XIANG: (
        "得生为相，力量较强", "相态，前景看好"),
    ProsperityState.XIU: (
        "休息，力量减弱", "休态，宜静待时机"),
    ProsperityState.QIU: (
        "被克为囚，力量受制", "囚态，需谨慎行事"),
    ProsperityState.SI: (
        "死绝，力量最弱", "死态，宜守不宜进"),
}

# 旺衰定性判断：基于五行旺衰的古典定性描述
_PROSPERITY_STRENGTH: dict[ProsperityState, str] = {
    ProsperityState.WANG: "力量充沛，利于行动",
    ProsperityState.XIANG: "力量较强，前景看好",
    ProsperityState.XIU: "力量不足，宜守不宜攻",
    ProsperityState.QIU: "力量受制，需谨慎行事",
    ProsperityState.SI: "力量极弱，大忌妄动",
}

# 上下卦互为颠倒的卦对（综卦关系）
# 如屯(水雷)与蒙(山水)互为综卦
_REVERSED_TRIGRAM: dict[str, str] = {
    "乾": "乾", "兑": "巽", "离": "离", "震": "艮",
    "巽": "兑", "坎": "坎", "艮": "震", "坤": "坤",
}

# 游魂卦ID（京房易传分类）
_WANDERING_SOUL_IDS: frozenset[int] = frozenset({
    34, 36, 42, 48, 52, 54, 58, 62,
})
# 归魂卦ID（京房易传分类）
_RETURNING_SOUL_IDS: frozenset[int] = frozenset({
    33, 35, 41, 47, 51, 53, 57, 61,
})


class DeepReasoningEngine:
    """深度推演引擎，基于五行生克执行10步推理链。"""

    @classmethod
    def reason(
        cls, hexagram_name: str, question_type: str,
        month_branch: str = "子", max_steps: int = 10,
    ) -> ReasoningChain:
        """执行深度推演，生成从分析到结论的完整推理链。"""
        hexagram = HexagramEngine.get_by_name(hexagram_name)
        steps: list[ReasoningStep] = []
        branch_points: list[int] = []

        builders = [
            cls._s1_analyze, cls._s2_infer, cls._s3_compare,
            cls._s4_deduce, cls._s5_synthesize, cls._s6_predict,
            cls._s7_validate, cls._s8_branch, cls._s9_refine,
            cls._s10_conclude,
        ]

        for i, fn in enumerate(builders[:max_steps]):
            prev = steps[-1] if steps else None
            step = fn(hexagram, prev, month_branch, steps)
            steps.append(step)
            if step.step_type == StepType.BRANCH:
                branch_points.append(step.step_number)

        trend = cls._build_trend_analysis(tuple(steps))
        final_hex = cls._determine_final_hexagram(steps)
        confidence = cls._compute_overall_confidence(tuple(steps))
        conclusion = cls._build_conclusion(tuple(steps), question_type)

        return ReasoningChain(
            steps=tuple(steps), initial_hexagram=hexagram_name,
            final_hexagram=final_hex, branch_points=tuple(branch_points),
            overall_confidence=confidence, conclusion=conclusion,
            trend_analysis=trend,
        )

    # -- 步骤构建器 -------------------------------------------------------

    @classmethod
    def _s1_analyze(
        cls, hex: Hexagram, _prev: ReasoningStep | None,
        _mb: str, _chain: list[ReasoningStep],
    ) -> ReasoningStep:
        u, lo = hex.upper_trigram, hex.lower_trigram
        rel = ElementEngine.get_relation(lo.element, u.element)
        jdg = hex.judgment[:20] if hex.judgment else "无"
        return ReasoningStep(
            step_number=1, step_type=StepType.ANALYZE,
            input_state=f"卦:{hex.name} 上:{u.name.value}({u.element.value}) 下:{lo.name.value}({lo.element.value})",
            logic=f"上下卦五行「{rel}」，{lo.element.value}{rel}{u.element.value}。卦辞:{jdg}。",
            output_state=f"{lo.element.value}{rel}{u.element.value}。{u.nature}在{lo.nature}上。",
            confidence=ConfidenceLevel.HIGH,
            element_changes=(f"上卦{u.element.value}", f"下卦{lo.element.value}"),
            related_hexagrams=(hex.name,),
        )

    @classmethod
    def _s2_infer(
        cls, hex: Hexagram, prev: ReasoningStep | None,
        _mb: str, _chain: list[ReasoningStep],
    ) -> ReasoningStep:
        u_e, l_e = hex.upper_trigram.element, hex.lower_trigram.element
        rel = ElementEngine.get_relation(l_e, u_e)
        tendency = (
            "有助力" if rel in ("生", "被生")
            else "有阻力" if rel in ("克", "被克")
            else "平稳")
        conf = (
            ConfidenceLevel.HIGH if tendency == "有助力"
            else ConfidenceLevel.MEDIUM)
        return ReasoningStep(
            step_number=2, step_type=StepType.INFER,
            input_state=f"前步:{prev.output_state if prev else '无'}",
            logic=(
                f"{l_e.value}{rel}{u_e.value}，事物发展{tendency}。"
                f"卦五行{hex.element.value}主{_ELEMENT_QUAL.get(hex.element, '')}。"),
            output_state=f"推断:{tendency}。五行{hex.element.value}。",
            confidence=conf,
            element_changes=(f"{l_e.value}{rel}{u_e.value}",),
            related_hexagrams=(hex.name,),
        )

    @classmethod
    def _s3_compare(
        cls, hex: Hexagram, prev: ReasoningStep | None,
        _mb: str, _chain: list[ReasoningStep],
    ) -> ReasoningStep:
        """Step 3: 比对 — 基于古典易学理论的卦象模式分析。"""
        pat = cls._analyze_hexagram_pattern(hex)
        return ReasoningStep(
            step_number=3, step_type=StepType.COMPARE,
            input_state=f"前步:{prev.output_state if prev else '无'}",
            logic=pat["description"],
            output_state=f"模式:{pat['type']}。{pat['inference']}",
            confidence=pat["confidence"],
            element_changes=(),
            related_hexagrams=(hex.name,),
        )

    @classmethod
    def _s4_deduce(
        cls, hex: Hexagram, prev: ReasoningStep | None,
        month_branch: str, _chain: list[ReasoningStep],
    ) -> ReasoningStep:
        h_e = hex.element
        try:
            pros = ElementEngine.judge_prosperity(h_e, month_branch)
        except ValueError:
            pros = ProsperityState.XIU
        m_e = ElementEngine.get_element_by_branch(month_branch)
        rel = ElementEngine.get_relation(h_e, m_e)
        p_logic, p_conc = _PROSPERITY_DESC.get(pros, ("状态不明", "无法判断"))
        return ReasoningStep(
            step_number=4, step_type=StepType.DEDUCE,
            input_state=f"前步:{prev.output_state if prev else '无'} 月令:{month_branch}({m_e.value})",
            logic=f"{h_e.value}在{month_branch}月({m_e.value}当令)「{pros.value}」。{p_logic}。关系:{rel}。",
            output_state=f"{h_e.value}{pros.value}。{p_conc}",
            confidence=ConfidenceLevel.HIGH,
            element_changes=(f"{h_e.value}处于{pros.value}态",),
            related_hexagrams=(hex.name,),
        )

    @classmethod
    def _s5_synthesize(
        cls, _hex: Hexagram, _prev: ReasoningStep | None,
        _mb: str, chain: list[ReasoningStep],
    ) -> ReasoningStep:
        pos_kw, neg_kw = ("助力", "上升", "旺", "相"), ("阻力", "下降", "衰", "囚", "死")
        pos = sum(1 for s in chain if any(k in s.output_state + s.logic for k in pos_kw))
        neg = sum(1 for s in chain if any(k in s.output_state + s.logic for k in neg_kw))
        if pos > neg:
            balance, conf = "偏吉", ConfidenceLevel.HIGH
        elif neg > pos:
            balance, conf = "偏凶", ConfidenceLevel.MEDIUM
        else:
            balance, conf = "平稳", ConfidenceLevel.MEDIUM
        return ReasoningStep(
            step_number=5, step_type=StepType.SYNTHESIZE,
            input_state=f"汇总{len(chain)}步分析",
            logic=f"正向信号{pos}个，负向信号{neg}个。综合判断「{balance}」。",
            output_state=f"综合:{balance}。正{pos}/负{neg}。",
            confidence=conf,
            element_changes=tuple(
                c for s in chain for c in s.element_changes)[:5],
            related_hexagrams=(),
        )

    @classmethod
    def _s6_predict(
        cls, hex: Hexagram, prev: ReasoningStep | None,
        _mb: str, _chain: list[ReasoningStep],
    ) -> ReasoningStep:
        try:
            opp = HexagramEngine.get_opposite(hex)
            inter = HexagramEngine.get_interlock(hex)
        except (ValueError, KeyError):
            opp, inter = hex, hex
        is_pos = prev and "偏吉" in prev.output_state
        if is_pos:
            trend, conf = "上升", ConfidenceLevel.MEDIUM
            logic = f"综合偏吉，错卦{opp.name}({opp.element.value})提示转化。互卦{inter.name}支持积极趋势。"
        else:
            trend, conf = "需谨慎", ConfidenceLevel.LOW
            logic = f"关注错卦{opp.name}({opp.element.value})。互卦{inter.name}({inter.element.value})揭示阻力。"
        return ReasoningStep(
            step_number=6, step_type=StepType.PREDICT,
            input_state=f"前步:{prev.output_state if prev else '无'}", logic=logic,
            output_state=f"趋势:{trend}。关键卦:{opp.name}、{inter.name}。",
            confidence=conf,
            element_changes=(f"{hex.element.value}->{opp.element.value}",),
            related_hexagrams=(hex.name, opp.name),
        )

    @classmethod
    def _s7_validate(
        cls, _hex: Hexagram, _prev: ReasoningStep | None,
        _mb: str, chain: list[ReasoningStep],
    ) -> ReasoningStep:
        has_ji = any("偏吉" in s.output_state for s in chain)
        has_xiong = any("偏凶" in s.output_state for s in chain)
        if has_ji and has_xiong:
            status, conf, logic = "存在矛盾", ConfidenceLevel.LOW, "吉凶矛盾信号"
        elif has_ji:
            status, conf, logic = "逻辑一致", ConfidenceLevel.HIGH, "吉向信号一致"
        elif has_xiong:
            status, conf, logic = "逻辑一致", ConfidenceLevel.MEDIUM, "凶向信号一致"
        else:
            status, conf, logic = "方向不明确", ConfidenceLevel.MEDIUM, "信号不明确"
        return ReasoningStep(
            step_number=7, step_type=StepType.VALIDATE,
            input_state=f"验证{len(chain)}步推理", logic=logic,
            output_state=f"验证:{status}。",
            confidence=conf, element_changes=(), related_hexagrams=(),
        )

    @classmethod
    def _s8_branch(
        cls, hex: Hexagram, prev: ReasoningStep | None,
        month_branch: str, _chain: list[ReasoningStep],
    ) -> ReasoningStep:
        """Step 8: 分支投影 — 基于五行生克旺衰的定性趋势判断。"""
        h_e = hex.element
        gen = _GENERATES.get(h_e, h_e)
        over = _OVERCOMES.get(h_e, h_e)

        # 判断卦五行在月令的旺衰
        try:
            pros = ElementEngine.judge_prosperity(h_e, month_branch)
        except ValueError:
            pros = ProsperityState.XIU
        strength_desc = _PROSPERITY_STRENGTH.get(pros, "状态不明")

        # 基于旺衰和五行生克给出定性趋势
        if pros in (ProsperityState.WANG, ProsperityState.XIANG):
            trend = "利于进取"
            conf = ConfidenceLevel.HIGH
            detail = (f"卦五行{h_e.value}在{month_branch}月{pros.value}，"
                      f"{strength_desc}。生扶方向{gen.value}有力，"
                      f"克制方向{over.value}不足为虑。")
        elif pros == ProsperityState.XIU:
            trend = "宜守待时"
            conf = ConfidenceLevel.MEDIUM
            detail = (f"卦五行{h_e.value}在{month_branch}月{pros.value}，"
                      f"{strength_desc}。生扶{gen.value}乏力，"
                      f"克制{over.value}有压。")
        else:
            trend = "宜静忌动"
            conf = ConfidenceLevel.LOW
            detail = (f"卦五行{h_e.value}在{month_branch}月{pros.value}，"
                      f"{strength_desc}。事多阻碍，不宜冒进。")

        return ReasoningStep(
            step_number=8, step_type=StepType.BRANCH,
            input_state=f"前步:{prev.output_state if prev else '无'}",
            logic=detail,
            output_state=f"趋势:{trend}。{h_e.value}{pros.value}，{strength_desc}。",
            confidence=conf,
            element_changes=(
                f"生扶方向->{gen.value}", f"克制方向->{over.value}",
                f"比和方向->{h_e.value}"),
            related_hexagrams=(hex.name,),
        )

    @classmethod
    def _s9_refine(
        cls, _hex: Hexagram, _prev: ReasoningStep | None,
        _mb: str, chain: list[ReasoningStep],
    ) -> ReasoningStep:
        validated = any(
            s.step_type == StepType.VALIDATE and "一致" in s.output_state
            for s in chain)
        contradicts = any(
            s.step_type == StepType.VALIDATE and "矛盾" in s.output_state
            for s in chain)
        if contradicts:
            ref, conf = "存在矛盾，取主导信号精炼", ConfidenceLevel.LOW
        elif validated:
            ref, conf = "逻辑一致，直接精炼", ConfidenceLevel.HIGH
        else:
            ref, conf = "未充分验证，保守精炼", ConfidenceLevel.MEDIUM
        direction = cls._extract_direction(chain, StepType.SYNTHESIZE)
        return ReasoningStep(
            step_number=9, step_type=StepType.REFINE,
            input_state="基于验证和分支分析精炼",
            logic=f"{ref}。保留主导推理路径。",
            output_state=f"精炼方向:{direction}。",
            confidence=conf, element_changes=(), related_hexagrams=(),
        )

    @classmethod
    def _s10_conclude(
        cls, _hex: Hexagram, _prev: ReasoningStep | None,
        _mb: str, chain: list[ReasoningStep],
    ) -> ReasoningStep:
        direction = cls._extract_direction(chain, StepType.REFINE)
        pos_kw = ("偏吉", "上升", "旺", "助力")
        neg_kw = ("偏凶", "下降", "衰", "阻力", "囚", "死")
        pos = sum(1 for s in chain if any(k in s.output_state + s.logic for k in pos_kw))
        neg = sum(1 for s in chain if any(k in s.output_state + s.logic for k in neg_kw))
        return ReasoningStep(
            step_number=10, step_type=StepType.CONCLUDE,
            input_state=f"整合{len(chain)}步推理",
            logic=f"正向{pos}/负向{neg}。方向:{direction}。",
            output_state=f"结论:{direction}。",
            confidence=ConfidenceLevel.MEDIUM,
            element_changes=(), related_hexagrams=(),
        )

    # -- 辅助方法 ---------------------------------------------------------

    @classmethod
    def _is_reversed_trigram_pair(cls, hex: Hexagram) -> bool:
        """判断上下卦是否互为综卦关系（颠倒关系）。

        如屯(水雷)与蒙(山水)互为综卦，泰(地天)与否(天地)互为综卦。
        """
        upper_nature = hex.upper_trigram.nature
        lower_nature = hex.lower_trigram.nature
        return _REVERSED_TRIGRAM.get(upper_nature) == lower_nature

    @classmethod
    def _analyze_hexagram_pattern(cls, hex: Hexagram) -> dict[str, object]:
        """基于古典易学理论分析卦象模式。

        检查：上下卦是否互为综卦、是否游魂/归魂卦。
        参考京房易传和《增删卜易》的分类体系。
        """
        patterns: list[str] = []
        inferences: list[str] = []
        conf = ConfidenceLevel.MEDIUM

        # 检查上下卦综卦关系
        if cls._is_reversed_trigram_pair(hex):
            patterns.append("上下互综")
            inferences.append(
                "上下卦互为颠倒，事物表里不一，需透过现象看本质。")

        # 检查游魂卦（八宫中第七卦，世在四爻）
        if hex.id in _WANDERING_SOUL_IDS:
            patterns.append("游魂卦")
            inferences.append(
                "游魂主心神不定、事物迁移，宜安定心神再行动。")
            conf = ConfidenceLevel.LOW

        # 检查归魂卦（八宫中第八卦，世在三爻）
        if hex.id in _RETURNING_SOUL_IDS:
            patterns.append("归魂卦")
            inferences.append(
                "归魂主回归安定，事物将有定论，宜顺势而为。")
            conf = ConfidenceLevel.HIGH

        if not patterns:
            return {"type": "常规卦象", "confidence": ConfidenceLevel.MEDIUM,
                    "description": f"{hex.name}，上下卦{hex.upper_trigram.nature}在{hex.lower_trigram.nature}上。",
                    "inference": "卦象无特殊格局，按常规五行生克论断。"}

        return {
            "type": "、".join(patterns),
            "confidence": conf,
            "description": f"{hex.name}，{'、'.join(patterns)}格局。",
            "inference": " ".join(inferences),
        }

    @classmethod
    def _build_trend_analysis(
        cls, chain: tuple[ReasoningStep, ...],
    ) -> tuple[tuple[str, str], ...]:
        """构建定性趋势分析，替代虚假的数值概率。

        基于古典五行旺衰理论，统计推理链中的定性信号，
        输出吉/凶/平的定性判断及依据。
        """
        pos_kw = ("偏吉", "上升", "旺", "相", "助力", "利于进取")
        neg_kw = ("偏凶", "下降", "衰", "囚", "死", "阻力", "宜静忌动")
        pos = [s for s in chain if any(k in s.output_state + s.logic for k in pos_kw)]
        neg = [s for s in chain if any(k in s.output_state + s.logic for k in neg_kw)]

        if len(pos) > len(neg):
            ji_desc = f"正向信号{len(pos)}个，多于负向{len(neg)}个"
            result = (("吉", ji_desc),)
        elif len(neg) > len(pos):
            xiong_desc = f"负向信号{len(neg)}个，多于正向{len(pos)}个"
            result = (("凶", xiong_desc),)
        else:
            result = (("平", f"正负信号持平（{len(pos)}:{len(neg)}）"),)

        return result

    @classmethod
    def _compute_overall_confidence(
        cls, chain: tuple[ReasoningStep, ...],
    ) -> ConfidenceLevel:
        """基于推理链中各步骤置信度的定性综合判断。"""
        if not chain:
            return ConfidenceLevel.SPECULATIVE
        high_count = sum(1 for s in chain if s.confidence == ConfidenceLevel.HIGH)
        low_count = sum(1 for s in chain if s.confidence in (ConfidenceLevel.LOW, ConfidenceLevel.SPECULATIVE))
        if high_count > len(chain) * 0.6:
            return ConfidenceLevel.HIGH
        if low_count > len(chain) * 0.5:
            return ConfidenceLevel.LOW
        return ConfidenceLevel.MEDIUM

    @classmethod
    def _extract_direction(
        cls, chain: list[ReasoningStep] | tuple[ReasoningStep, ...],
        step_type: StepType,
    ) -> str:
        """从指定步骤类型中提取方向判断。"""
        step = next((s for s in chain if s.step_type == step_type), None)
        if step:
            if "偏吉" in step.output_state:
                return "偏吉"
            if "偏凶" in step.output_state:
                return "偏凶"
        return "平稳"

    @classmethod
    def _determine_final_hexagram(cls, steps: list[ReasoningStep]) -> str | None:
        for s in steps:
            if s.step_type == StepType.PREDICT and len(s.related_hexagrams) > 1:
                return s.related_hexagrams[1]
        return None

    @classmethod
    def _build_conclusion(
        cls, chain: tuple[ReasoningStep, ...], question_type: str,
    ) -> str:
        direction = cls._extract_direction(chain, StepType.CONCLUDE)
        q = question_type or "整体运势"
        synth = next(
            (s for s in chain if s.step_type == StepType.SYNTHESIZE), None)
        parts = [
            f"针对「{q}」的推演结论：",
            f"综合{len(chain)}步推理，当前卦象呈「{direction}」态势。"]
        if synth:
            parts.append(synth.output_state)
        parts.append("以上推演仅供参考，请理性看待。")
        return " ".join(parts)
