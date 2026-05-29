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

        dist = cls._build_probability_distribution(tuple(steps))
        final_hex = cls._determine_final_hexagram(steps)
        confidence = cls._compute_overall_confidence(tuple(steps))
        conclusion = cls._build_conclusion(tuple(steps), question_type)

        return ReasoningChain(
            steps=tuple(steps), initial_hexagram=hexagram_name,
            final_hexagram=final_hex, branch_points=tuple(branch_points),
            overall_confidence=confidence, conclusion=conclusion,
            probability_distribution=dist,
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
        u_n, l_n = hex.upper_trigram.nature, hex.lower_trigram.nature
        pat = cls._identify_pattern(u_n, l_n)
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
        _mb: str, _chain: list[ReasoningStep],
    ) -> ReasoningStep:
        h_e = hex.element
        gen = _GENERATES.get(h_e, h_e)
        over = _OVERCOMES.get(h_e, h_e)
        return ReasoningStep(
            step_number=8, step_type=StepType.BRANCH,
            input_state=f"前步:{prev.output_state if prev else '无'}",
            logic=(
                f"从{h_e.value}出发: 生{gen.value}(60%)、"
                f"克{over.value}(25%)、比和{h_e.value}(15%)。"),
            output_state=f"三分支: 生{gen.value}|克{over.value}|比和{h_e.value}",
            confidence=ConfidenceLevel.MEDIUM,
            element_changes=(
                f"生扶->{gen.value}", f"克制->{over.value}",
                f"比和->{h_e.value}"),
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
    def _identify_pattern(cls, upper: str, lower: str) -> dict[str, object]:
        dyn, stab = {"天", "雷", "风", "火", "水"}, {"山", "地", "泽"}
        if upper in dyn and lower in stab:
            return {"type": "动上静下", "confidence": ConfidenceLevel.MEDIUM,
                    "description": f"外在活跃内在稳固，如{upper}在{lower}上。",
                    "inference": "表象活跃根基稳固，宜主动但需守本。"}
        if upper in stab and lower in dyn:
            return {"type": "静上动下", "confidence": ConfidenceLevel.MEDIUM,
                    "description": f"外在沉稳内在活跃，如{upper}下有{lower}。",
                    "inference": "表面平静内在动力足，宜稳中求进。"}
        return {"type": "流动组合", "confidence": ConfidenceLevel.LOW,
                "description": f"{upper}与{lower}的组合。",
                "inference": "事物变化较快，宜灵活应对。"}

    @classmethod
    def _compute_confidence(cls, score: float) -> ConfidenceLevel:
        if score >= 75:
            return ConfidenceLevel.HIGH
        if score >= 50:
            return ConfidenceLevel.MEDIUM
        if score >= 25:
            return ConfidenceLevel.LOW
        return ConfidenceLevel.SPECULATIVE

    @classmethod
    def _build_probability_distribution(
        cls, chain: tuple[ReasoningStep, ...],
    ) -> tuple[tuple[str, float], ...]:
        wm = {ConfidenceLevel.HIGH: 1.5, ConfidenceLevel.MEDIUM: 1.0,
              ConfidenceLevel.LOW: 0.6, ConfidenceLevel.SPECULATIVE: 0.3}
        pos_kw, neg_kw = ("偏吉", "上升", "旺", "助力"), ("偏凶", "下降", "衰", "阻力", "囚", "死")
        pos = sum(wm.get(s.confidence, 1.0) for s in chain if any(k in s.output_state + s.logic for k in pos_kw))
        neg = sum(wm.get(s.confidence, 1.0) for s in chain if any(k in s.output_state + s.logic for k in neg_kw))
        total = pos + neg
        if total == 0:
            return (("吉", 0.33), ("凶", 0.33), ("平", 0.34))
        ji, xiong = pos / total, neg / total
        ping = max(0.0, 1.0 - ji - xiong)
        if ping == 0 and (ji + xiong) > 0:
            ji /= (ji + xiong)
            xiong = 1.0 - ji
        return (("吉", round(ji, 3)), ("凶", round(xiong, 3)), ("平", round(ping, 3)))

    @classmethod
    def _compute_overall_confidence(
        cls, chain: tuple[ReasoningStep, ...],
    ) -> ConfidenceLevel:
        if not chain:
            return ConfidenceLevel.SPECULATIVE
        sm = {ConfidenceLevel.HIGH: 90, ConfidenceLevel.MEDIUM: 60,
              ConfidenceLevel.LOW: 35, ConfidenceLevel.SPECULATIVE: 15}
        return cls._compute_confidence(sum(sm.get(s.confidence, 50) for s in chain) / len(chain))

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
