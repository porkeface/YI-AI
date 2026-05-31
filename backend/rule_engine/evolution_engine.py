"""深度推演引擎

扩展推演引擎，支持：
- 10步推演链
- 概率树（分支因子3）
- 状态转移矩阵
- 时间维度推演

与inference_engine的区别：
- inference_engine: 3步推演，单路径
- evolution_engine: 10步推演，多分支概率树
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from foundation.types import (
    Element,
    Hexagram,
    RuleAnalysisResult,
    YinYang,
)
from foundation.hexagram_engine import HexagramEngine
from foundation.element_engine import ElementEngine

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InferenceProbabilities:
    """推演概率配置

    与 inference_engine 保持一致的概率配置，确保两个引擎使用相同的概率值。

    Attributes:
        changed_base: 变卦路径基础概率
        changed_per_moving_penalty: 每个动爻的惩罚系数
        changed_min: 变卦路径最低概率下限
        reversed_prob: 综卦路径概率
        opposite_prob: 错卦路径概率
        interlock_prob: 互卦路径概率
    """
    changed_base: float = 1.0
    changed_per_moving_penalty: float = 0.15
    changed_min: float = 0.3
    reversed_prob: float = 0.6
    opposite_prob: float = 0.3
    interlock_prob: float = 0.5


# 模块级默认概率配置
DEFAULT_PROBABILITIES = InferenceProbabilities()


@dataclass(frozen=True)
class EvolutionNode:
    """演化树节点

    Attributes:
        hexagram_name: 卦名
        depth: 深度（0=根节点）
        probability: 到达该节点的累积概率
        transition_trigger: 触发转移的原因
        relation: 与父节点的关系
        children: 子节点列表
        trend: 趋势方向
        element_strength: 五行力量值 (0-100)
    """
    hexagram_name: str
    depth: int
    probability: float
    transition_trigger: str
    relation: str
    children: tuple[EvolutionNode, ...]
    trend: Literal["上升", "下降", "平稳", "转折"]
    element_strength: float


@dataclass(frozen=True)
class ProbabilityTree:
    """概率树

    Attributes:
        root: 根节点
        max_depth: 最大深度
        branch_factor: 分支因子
        total_nodes: 总节点数
        paths: 所有叶子节点路径
    """
    root: EvolutionNode
    max_depth: int
    branch_factor: int
    total_nodes: int
    paths: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class StateTransition:
    """状态转移

    Attributes:
        from_state: 起始卦名
        to_state: 目标卦名
        trigger: 触发条件
        probability: 转移概率
        relation: 关系类型
        element_change: 五行变化描述
    """
    from_state: str
    to_state: str
    trigger: str
    probability: float
    relation: str
    element_change: str


@dataclass(frozen=True)
class EvolutionResult:
    """推演结果

    Attributes:
        source_hexagram: 起始卦名
        tree: 概率树
        transitions: 所有状态转移
        recommended_path: 推荐路径
        summary: 推演总结
    """
    source_hexagram: str
    tree: ProbabilityTree
    transitions: tuple[StateTransition, ...]
    recommended_path: tuple[str, ...]
    summary: str


class EvolutionEngine:
    """深度推演引擎

    支持10步推演链和概率树生成。
    """

    MAX_DEPTH = 10
    DEFAULT_BRANCH_FACTOR = 3

    @staticmethod
    def evolve(
        hexagram: Hexagram,
        analysis: RuleAnalysisResult | None = None,
        max_depth: int = 5,
        branch_factor: int = 3,
    ) -> EvolutionResult:
        """执行深度推演

        Args:
            hexagram: 起始卦
            analysis: 规则分析结果（可选）
            max_depth: 最大推演深度（默认5，最大10）
            branch_factor: 分支因子（默认3）

        Returns:
            推演结果
        """
        depth = min(max_depth, EvolutionEngine.MAX_DEPTH)
        bf = min(branch_factor, EvolutionEngine.DEFAULT_BRANCH_FACTOR)

        # 构建概率树
        root = EvolutionEngine._build_tree(
            hexagram, analysis, depth, bf, 1.0, 0
        )

        # 统计节点数
        total_nodes = EvolutionEngine._count_nodes(root)

        # 收集所有路径
        paths = EvolutionEngine._collect_paths(root)

        # 收集所有转移
        transitions = EvolutionEngine._collect_transitions(root)

        # 选择推荐路径
        recommended = EvolutionEngine._select_recommended_path(paths, root)

        # 生成总结
        summary = EvolutionEngine._build_summary(
            hexagram.name, root, paths, recommended
        )

        logger.info(
            "evolution_complete",
            source=hexagram.name,
            depth=depth,
            branch_factor=bf,
            total_nodes=total_nodes,
            path_count=len(paths),
        )

        return EvolutionResult(
            source_hexagram=hexagram.name,
            tree=ProbabilityTree(
                root=root,
                max_depth=depth,
                branch_factor=bf,
                total_nodes=total_nodes,
                paths=tuple(paths),
            ),
            transitions=tuple(transitions),
            recommended_path=tuple(recommended),
            summary=summary,
        )

    @staticmethod
    def _build_tree(
        hexagram: Hexagram,
        analysis: RuleAnalysisResult | None,
        max_depth: int,
        branch_factor: int,
        cumulative_prob: float,
        current_depth: int,
    ) -> EvolutionNode:
        """递归构建概率树"""
        if current_depth >= max_depth or cumulative_prob < 0.01:
            return EvolutionNode(
                hexagram_name=hexagram.name,
                depth=current_depth,
                probability=round(cumulative_prob, 4),
                transition_trigger="",
                relation="",
                children=(),
                trend="平稳",
                element_strength=50.0,
            )

        # 获取所有可能的转移
        transitions = EvolutionEngine._get_possible_transitions(
            hexagram, analysis, current_depth
        )

        # 限制分支数
        transitions = transitions[:branch_factor]

        children = []
        for trans in transitions:
            try:
                child_hex = HexagramEngine.get_by_name(trans.to_state)
                child_prob = cumulative_prob * trans.probability

                child = EvolutionEngine._build_tree(
                    child_hex,
                    None,  # 子节点不再有原始分析
                    max_depth,
                    branch_factor,
                    child_prob,
                    current_depth + 1,
                )

                # 创建带转移信息的子节点
                child_with_info = EvolutionNode(
                    hexagram_name=child.hexagram_name,
                    depth=child.depth,
                    probability=child.probability,
                    transition_trigger=trans.trigger,
                    relation=trans.relation,
                    children=child.children,
                    trend=child.trend,
                    element_strength=child.element_strength,
                )
                children.append(child_with_info)
            except (ValueError, IndexError):
                continue

        # 计算趋势
        trend = EvolutionEngine._compute_trend(hexagram, children)

        # 计算五行力量
        element_strength = EvolutionEngine._compute_element_strength(hexagram)

        return EvolutionNode(
            hexagram_name=hexagram.name,
            depth=current_depth,
            probability=round(cumulative_prob, 4),
            transition_trigger="",
            relation="root" if current_depth == 0 else "",
            children=tuple(children),
            trend=trend,
            element_strength=element_strength,
        )

    @staticmethod
    def _get_possible_transitions(
        hexagram: Hexagram,
        analysis: RuleAnalysisResult | None,
        depth: int,
    ) -> list[StateTransition]:
        """获取所有可能的状态转移"""
        transitions = []

        # 1. 变卦路径（动爻驱动）
        if analysis and analysis.moving_lines:
            try:
                changed = HexagramEngine.get_changed(
                    hexagram, analysis.moving_lines
                )
                prob = max(
                    DEFAULT_PROBABILITIES.changed_min,
                    DEFAULT_PROBABILITIES.changed_base - len(analysis.moving_lines) * DEFAULT_PROBABILITIES.changed_per_moving_penalty,
                )
                transitions.append(StateTransition(
                    from_state=hexagram.name,
                    to_state=changed.name,
                    trigger=f"动爻变化（{'、'.join(str(p) for p in analysis.moving_lines)}爻）",
                    probability=prob,
                    relation="变卦",
                    element_change=EvolutionEngine._describe_element_change(
                        hexagram, changed
                    ),
                ))
            except (ValueError, IndexError):
                pass

        # 2. 综卦路径
        try:
            reversed_h = HexagramEngine.get_reversed(hexagram)
            transitions.append(StateTransition(
                from_state=hexagram.name,
                to_state=reversed_h.name,
                trigger="视角转换",
                probability=DEFAULT_PROBABILITIES.reversed_prob,
                relation="综卦",
                element_change=EvolutionEngine._describe_element_change(
                    hexagram, reversed_h
                ),
            ))
        except (ValueError, IndexError):
            pass

        # 3. 错卦路径
        try:
            opposite = HexagramEngine.get_opposite(hexagram)
            transitions.append(StateTransition(
                from_state=hexagram.name,
                to_state=opposite.name,
                trigger="对立面",
                probability=DEFAULT_PROBABILITIES.opposite_prob,
                relation="错卦",
                element_change=EvolutionEngine._describe_element_change(
                    hexagram, opposite
                ),
            ))
        except (ValueError, IndexError):
            pass

        # 4. 互卦路径
        try:
            interlock = HexagramEngine.get_interlock(hexagram)
            transitions.append(StateTransition(
                from_state=hexagram.name,
                to_state=interlock.name,
                trigger="内在本质",
                probability=DEFAULT_PROBABILITIES.interlock_prob,
                relation="互卦",
                element_change=EvolutionEngine._describe_element_change(
                    hexagram, interlock
                ),
            ))
        except (ValueError, IndexError):
            pass

        # 按概率排序
        transitions.sort(key=lambda t: t.probability, reverse=True)

        return transitions

    @staticmethod
    def _describe_element_change(from_hex: Hexagram, to_hex: Hexagram) -> str:
        """描述五行变化"""
        from_elem = from_hex.element.value
        to_elem = to_hex.element.value
        if from_elem == to_elem:
            return f"五行不变（{from_elem}）"

        try:
            relation = ElementEngine.get_relation(
                Element(from_elem), Element(to_elem)
            )
            return f"{from_elem}→{to_elem}（{relation}）"
        except Exception:
            logger.debug("element_relation_lookup_failed", from_elem=from_elem, to_elem=to_elem, exc_info=True)
            return f"{from_elem}→{to_elem}"

    @staticmethod
    def _compute_trend(
        hexagram: Hexagram,
        children: list[EvolutionNode],
    ) -> Literal["上升", "下降", "平稳", "转折"]:
        """计算趋势"""
        if not children:
            return "平稳"

        yang_count = sum(
            1 for line in hexagram.lines
            if line.yin_yang == YinYang.YANG
        )

        # 基于子节点的平均五行力量判断趋势
        avg_strength = sum(c.element_strength for c in children) / len(children)

        if avg_strength > 60:
            return "上升"
        elif avg_strength < 40:
            return "下降"
        elif len(children) >= 3:
            return "转折"
        return "平稳"

    @staticmethod
    def _compute_element_strength(hexagram: Hexagram) -> float:
        """计算五行力量值"""
        yang_count = sum(
            1 for line in hexagram.lines
            if line.yin_yang == YinYang.YANG
        )
        return round(yang_count / 6 * 100, 1)

    @staticmethod
    def _count_nodes(node: EvolutionNode) -> int:
        """统计节点数"""
        count = 1
        for child in node.children:
            count += EvolutionEngine._count_nodes(child)
        return count

    @staticmethod
    def _collect_paths(
        node: EvolutionNode,
        current_path: list[str] | None = None,
    ) -> list[list[str]]:
        """收集所有路径"""
        if current_path is None:
            current_path = []

        path = current_path + [node.hexagram_name]

        if not node.children:
            return [path]

        all_paths = []
        for child in node.children:
            all_paths.extend(EvolutionEngine._collect_paths(child, path))

        return all_paths

    @staticmethod
    def _collect_transitions(node: EvolutionNode) -> list[StateTransition]:
        """收集所有转移"""
        transitions = []
        for child in node.children:
            transitions.append(StateTransition(
                from_state=node.hexagram_name,
                to_state=child.hexagram_name,
                trigger=child.transition_trigger,
                probability=child.probability,
                relation=child.relation,
                element_change="",
            ))
            transitions.extend(EvolutionEngine._collect_transitions(child))
        return transitions

    @staticmethod
    def _select_recommended_path(
        paths: list[list[str]],
        root: EvolutionNode,
    ) -> list[str]:
        """选择推荐路径

        策略：选择概率最高且趋势最有利的路径。
        """
        if not paths:
            return [root.hexagram_name]

        def score_path(path: list[str]) -> float:
            # 找到路径末端节点
            node = root
            for name in path[1:]:
                for child in node.children:
                    if child.hexagram_name == name:
                        node = child
                        break

            score = node.probability * 0.6
            trend_bonus = {
                "上升": 0.3, "转折": 0.2,
                "平稳": 0.1, "下降": 0.0,
            }
            score += trend_bonus.get(node.trend, 0)
            return score

        return max(paths, key=score_path)

    @staticmethod
    def _build_summary(
        source: str,
        root: EvolutionNode,
        paths: list[list[str]],
        recommended: list[str],
    ) -> str:
        """构建推演总结"""
        parts = []
        parts.append(f"从{source}出发，深度推演生成{len(paths)}条路径：")

        for i, path in enumerate(paths[:5], 1):  # 最多显示5条
            marker = " ★" if path == recommended else ""
            parts.append(f"  {i}. {' → '.join(path)}{marker}")

        if len(paths) > 5:
            parts.append(f"  ...还有{len(paths) - 5}条路径")

        parts.append(f"推荐路径：{' → '.join(recommended)}")

        return "\n".join(parts)
