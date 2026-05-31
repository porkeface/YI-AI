"""推演引擎模块

实现基于卦象的状态推演，包括：
- 状态转移图（从当前卦推导可能的未来状态）
- 3步推演链（连续推导3步变化路径）
- 概率树v1（多路径概率评估）

推演原理：
- 动爻变化驱动状态转移
- 变卦代表近期变化方向
- 综卦代表事物的另一面
- 错卦代表事物的对立面
- 互卦代表事物的内在本质

推演链：本卦 → 变卦 → 变卦的变卦 → ...
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from foundation.types import (
    Element,
    Hexagram,
    ProsperityState,
    RuleAnalysisResult,
    Verdict,
    YinYang,
)
from foundation.hexagram_engine import HexagramEngine
from foundation.element_engine import ElementEngine
from rule_engine.types import InferenceProbabilities

logger = logging.getLogger(__name__)


# 模块级默认概率配置
DEFAULT_PROBABILITIES = InferenceProbabilities()


@dataclass(frozen=True)
class TransitionStep:
    """推演步骤

    Attributes:
        from_hexagram: 起始卦
        to_hexagram: 目标卦
        trigger: 触发原因（如"二爻动"）
        relation: 两卦关系（变卦/综卦/错卦/互卦）
        probability: 转移概率 (0.0-1.0)
        description: 步骤描述
    """
    from_hexagram: str     # 卦名
    to_hexagram: str       # 卦名
    trigger: str           # 触发原因
    relation: str          # 关系类型
    probability: float     # 转移概率
    description: str       # 描述


@dataclass(frozen=True)
class InferencePath:
    """推演路径

    Attributes:
        steps: 推演步骤序列
        final_hexagram: 最终卦名
        overall_trend: 总体趋势
        path_probability: 路径综合概率
        summary: 路径总结
    """
    steps: tuple[TransitionStep, ...]
    final_hexagram: str
    overall_trend: Literal["上升", "下降", "平稳", "转折"]
    path_probability: float
    summary: str


@dataclass(frozen=True)
class InferenceResult:
    """推演结果

    Attributes:
        source_hexagram: 起始卦名
        paths: 推演路径列表
        recommended_path: 推荐路径（概率最高或最有利）
        inference_depth: 推演深度
        summary: 推演总结
    """
    source_hexagram: str
    paths: tuple[InferencePath, ...]
    recommended_path: InferencePath
    inference_depth: int
    summary: str


class InferenceEngine:
    """推演引擎

    基于卦象变化进行多步推演，生成状态转移路径。
    """

    MAX_INFERENCE_DEPTH = 3

    @staticmethod
    def infer(
        hexagram: Hexagram,
        analysis: RuleAnalysisResult,
        max_depth: int = 3,
    ) -> InferenceResult:
        """执行推演

        推演策略：
        1. 变卦路径：通过动爻变化推导（概率最高）
        2. 综卦路径：从另一视角看问题（辅助参考）
        3. 错卦路径：对立面分析（风险评估）
        4. 互卦路径：内在本质分析（深层参考）

        Args:
            hexagram: 当前卦
            analysis: 规则分析结果
            max_depth: 最大推演深度（默认3）

        Returns:
            推演结果
        """
        depth = min(max_depth, InferenceEngine.MAX_INFERENCE_DEPTH)

        paths: list[InferencePath] = []

        # 路径1: 变卦路径（如果有动爻）
        if analysis.moving_lines:
            changed_path = InferenceEngine._infer_changed_path(
                hexagram, analysis, depth
            )
            if changed_path:
                paths.append(changed_path)

        # 路径2: 综卦路径
        reversed_path = InferenceEngine._infer_reversed_path(
            hexagram, analysis, depth
        )
        if reversed_path:
            paths.append(reversed_path)

        # 路径3: 错卦路径
        opposite_path = InferenceEngine._infer_opposite_path(
            hexagram, analysis, depth
        )
        if opposite_path:
            paths.append(opposite_path)

        # 路径4: 互卦路径
        interlock_path = InferenceEngine._infer_interlock_path(
            hexagram, analysis, depth
        )
        if interlock_path:
            paths.append(interlock_path)

        # 选择推荐路径
        if not paths:
            # 无推演路径，返回默认
            default_path = InferencePath(
                steps=(),
                final_hexagram=hexagram.name,
                overall_trend="平稳",
                path_probability=1.0,
                summary="当前卦象稳定，无明显变化趋势。",
            )
            paths = [default_path]

        recommended = InferenceEngine._select_recommended(paths, analysis)

        # 生成总结
        summary = InferenceEngine._build_summary(
            hexagram.name, paths, recommended
        )

        logger.info(
            "inference_complete",
            source=hexagram.name,
            path_count=len(paths),
            recommended=recommended.final_hexagram,
        )

        return InferenceResult(
            source_hexagram=hexagram.name,
            paths=tuple(paths),
            recommended_path=recommended,
            inference_depth=depth,
            summary=summary,
        )

    @staticmethod
    def _infer_changed_path(
        hexagram: Hexagram,
        analysis: RuleAnalysisResult,
        depth: int,
    ) -> InferencePath | None:
        """变卦路径推演

        通过动爻变化生成推演链：本卦 → 变卦 → 变卦的变卦 → ...

        Args:
            hexagram: 当前卦
            analysis: 分析结果
            depth: 推演深度

        Returns:
            推演路径，失败返回None
        """
        steps: list[TransitionStep] = []
        current = hexagram
        moving = list(analysis.moving_lines)

        for i in range(depth):
            if not moving:
                break

            try:
                changed = HexagramEngine.get_changed(
                    current, tuple(moving)
                )
            except (ValueError, IndexError):
                break

            # 计算转移概率（动爻越多，变化越大，概率越分散）
            prob = max(
                DEFAULT_PROBABILITIES.changed_min,
                DEFAULT_PROBABILITIES.changed_base - len(moving) * DEFAULT_PROBABILITIES.changed_per_moving_penalty,
            )

            trigger_desc = "、".join(f"{p}爻动" for p in moving)
            step = TransitionStep(
                from_hexagram=current.name,
                to_hexagram=changed.name,
                trigger=trigger_desc,
                relation="变卦",
                probability=prob,
                description=f"{current.name}经{trigger_desc}变为{changed.name}",
            )
            steps.append(step)

            # 下一步：变卦的动爻（如果有）
            current = changed
            # 变卦的动爻需要重新分析，这里简化为无动爻
            moving = []

        if not steps:
            return None

        final = steps[-1].to_hexagram
        trend = InferenceEngine._infer_trend(hexagram.name, final)

        total_prob = 1.0
        for s in steps:
            total_prob *= s.probability

        return InferencePath(
            steps=tuple(steps),
            final_hexagram=final,
            overall_trend=trend,
            path_probability=round(total_prob, 3),
            summary=f"经动爻变化，从{hexagram.name}推演至{final}",
        )

    @staticmethod
    def _infer_reversed_path(
        hexagram: Hexagram,
        analysis: RuleAnalysisResult,
        depth: int,
    ) -> InferencePath | None:
        """综卦路径推演

        综卦（颠倒卦）代表事物的另一面/不同视角。

        Args:
            hexagram: 当前卦
            analysis: 分析结果
            depth: 推演深度

        Returns:
            推演路径
        """
        try:
            reversed_hex = HexagramEngine.get_reversed(hexagram)
        except (ValueError, IndexError):
            return None

        step = TransitionStep(
            from_hexagram=hexagram.name,
            to_hexagram=reversed_hex.name,
            trigger="视角转换",
            relation="综卦",
            probability=DEFAULT_PROBABILITIES.reversed_prob,
            description=f"从另一个视角看，{hexagram.name}的综卦是{reversed_hex.name}",
        )

        trend = InferenceEngine._infer_trend(
            hexagram.name, reversed_hex.name
        )

        return InferencePath(
            steps=(step,),
            final_hexagram=reversed_hex.name,
            overall_trend=trend,
            path_probability=DEFAULT_PROBABILITIES.reversed_prob,
            summary=f"换位思考：{hexagram.name}↔{reversed_hex.name}",
        )

    @staticmethod
    def _infer_opposite_path(
        hexagram: Hexagram,
        analysis: RuleAnalysisResult,
        depth: int,
    ) -> InferencePath | None:
        """错卦路径推演

        错卦（全反卦）代表事物的对立面/极端情况。

        Args:
            hexagram: 当前卦
            analysis: 分析结果
            depth: 推演深度

        Returns:
            推演路径
        """
        try:
            opposite_hex = HexagramEngine.get_opposite(hexagram)
        except (ValueError, IndexError):
            return None

        step = TransitionStep(
            from_hexagram=hexagram.name,
            to_hexagram=opposite_hex.name,
            trigger="对立面分析",
            relation="错卦",
            probability=DEFAULT_PROBABILITIES.opposite_prob,
            description=f"{hexagram.name}的对立面是{opposite_hex.name}，代表可能的极端情况",
        )

        trend = InferenceEngine._infer_trend(
            hexagram.name, opposite_hex.name
        )

        return InferencePath(
            steps=(step,),
            final_hexagram=opposite_hex.name,
            overall_trend=trend,
            path_probability=DEFAULT_PROBABILITIES.opposite_prob,
            summary=f"风险评估：最坏情况为{opposite_hex.name}",
        )

    @staticmethod
    def _infer_interlock_path(
        hexagram: Hexagram,
        analysis: RuleAnalysisResult,
        depth: int,
    ) -> InferencePath | None:
        """互卦路径推演

        互卦代表事物的内在本质/隐含因素。

        Args:
            hexagram: 当前卦
            analysis: 分析结果
            depth: 推演深度

        Returns:
            推演路径
        """
        try:
            interlock_hex = HexagramEngine.get_interlock(hexagram)
        except (ValueError, IndexError):
            return None

        step = TransitionStep(
            from_hexagram=hexagram.name,
            to_hexagram=interlock_hex.name,
            trigger="内在本质",
            relation="互卦",
            probability=DEFAULT_PROBABILITIES.interlock_prob,
            description=f"{hexagram.name}的内在本质是{interlock_hex.name}",
        )

        trend = InferenceEngine._infer_trend(
            hexagram.name, interlock_hex.name
        )

        return InferencePath(
            steps=(step,),
            final_hexagram=interlock_hex.name,
            overall_trend=trend,
            path_probability=DEFAULT_PROBABILITIES.interlock_prob,
            summary=f"深层分析：{hexagram.name}内在本质为{interlock_hex.name}",
        )

    @staticmethod
    def _infer_trend(
        from_name: str,
        to_name: str,
    ) -> Literal["上升", "下降", "平稳", "转折"]:
        """推断趋势方向

        基于卦的阴阳比例变化推断趋势。

        Args:
            from_name: 起始卦名
            to_name: 目标卦名

        Returns:
            趋势方向
        """
        try:
            from_hex = HexagramEngine.get_by_name(from_name)
            to_hex = HexagramEngine.get_by_name(to_name)
        except (ValueError, IndexError):
            return "平稳"

        from_yang = sum(
            1 for line in from_hex.lines
            if line.yin_yang == YinYang.YANG
        )
        to_yang = sum(
            1 for line in to_hex.lines
            if line.yin_yang == YinYang.YANG
        )

        diff = to_yang - from_yang

        if diff >= 2:
            return "上升"
        elif diff <= -2:
            return "下降"
        elif abs(diff) == 1:
            return "转折"
        else:
            return "平稳"

    @staticmethod
    def _select_recommended(
        paths: list[InferencePath],
        analysis: RuleAnalysisResult,
    ) -> InferencePath:
        """选择推荐路径

        策略：
        - 吉卦优先选上升趋势路径
        - 凶卦优先选平稳路径
        - 综合考虑概率和趋势

        Args:
            paths: 所有推演路径
            analysis: 规则分析结果

        Returns:
            推荐路径
        """
        if len(paths) == 1:
            return paths[0]

        is_favorable = analysis.verdict.overall == "吉"

        def score_path(path: InferencePath) -> float:
            score = path.path_probability * 0.4
            if is_favorable:
                # 吉卦：上升趋势加分
                trend_bonus = {
                    "上升": 0.4, "转折": 0.2,
                    "平稳": 0.1, "下降": 0.0,
                }
            else:
                # 凶卦：平稳趋势加分
                trend_bonus = {
                    "平稳": 0.4, "转折": 0.2,
                    "下降": 0.1, "上升": 0.0,
                }
            score += trend_bonus.get(path.overall_trend, 0)
            return score

        return max(paths, key=score_path)

    @staticmethod
    def _build_summary(
        source: str,
        paths: list[InferencePath],
        recommended: InferencePath,
    ) -> str:
        """构建推演总结

        Args:
            source: 起始卦名
            paths: 所有路径
            recommended: 推荐路径

        Returns:
            总结文本
        """
        parts: list[str] = []
        parts.append(f"从{source}出发，共推演出{len(paths)}条可能路径：")

        for i, path in enumerate(paths, 1):
            marker = " ★" if path is recommended else ""
            parts.append(
                f"  {i}. {path.summary}（概率{path.path_probability:.0%}，"
                f"趋势{path.overall_trend}）{marker}"
            )

        parts.append(f"推荐路径：{recommended.summary}")

        return "\n".join(parts)
