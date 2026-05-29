"""概率推演树

基于五行生克关系构建概率推演树，每步最多3个分支。
支持路径枚举、期望值计算和风险评估。
"""
from __future__ import annotations

from foundation.types import Element, Hexagram, ProsperityState
from foundation.hexagram_engine import HexagramEngine
from foundation.element_engine import ElementEngine

from ai.reasoning.types import TreeBranch, TreeNode, ProbabilityTree

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
_DEFAULT_PROBS: tuple[float, float, float] = (0.60, 0.25, 0.15)
_PROSPERITY_PROBS: dict[ProsperityState, tuple[float, float, float]] = {
    ProsperityState.WANG: (0.65, 0.20, 0.15),
    ProsperityState.XIANG: (0.60, 0.25, 0.15),
    ProsperityState.XIU: (0.50, 0.30, 0.20),
    ProsperityState.QIU: (0.40, 0.40, 0.20),
    ProsperityState.SI: (0.35, 0.45, 0.20),
}
_PROSPERITY_BONUS: dict[ProsperityState, int] = {
    ProsperityState.WANG: 20, ProsperityState.XIANG: 12,
    ProsperityState.XIU: 0, ProsperityState.QIU: -12,
    ProsperityState.SI: -20,
}
_REL_BONUS: dict[str, int] = {
    "生": 8, "被生": 8, "克": -5, "被克": -5, "同": 3,
}


class ProbabilityTreeEngine:
    """概率推演树引擎

    从当前卦开始，每步基于五行变化方向产生最多3个分支:
    1. 生扶方向 (被生) - 最可能路径 (60%)
    2. 克制方向 (被克) - 次可能路径 (25%)
    3. 比和方向 (同类) - 最小可能路径 (15%)
    """

    @classmethod
    def build_tree(
        cls, hexagram_name: str, question_type: str,
        month_branch: str = "子", max_depth: int = 10,
    ) -> ProbabilityTree:
        """构建概率推演树。

        从当前卦开始，每步产生3个分支（生扶/克制/比和），直到达到最大深度。
        低概率分支(累积概率<0.01)会被剪枝。

        Args:
            hexagram_name: 卦名（如"乾为天"）
            question_type: 问题类型
            month_branch: 月份地支
            max_depth: 最大深度

        Returns:
            完整的概率推演树
        """
        HexagramEngine.get_by_name(hexagram_name)
        root = cls._build_node(hexagram_name, 0, 1.0, month_branch, max_depth)
        pruned = cls._prune_node(root, 0.01)
        total_paths = cls._count_paths(pruned)
        ev = cls._compute_expected_value(pruned)
        risk = cls._assess_risk(pruned, ev)
        return ProbabilityTree(
            root=pruned, max_depth=max_depth, branch_factor=3,
            total_paths=total_paths, expected_value=ev, risk_assessment=risk,
        )

    @classmethod
    def _build_node(
        cls, hexagram_name: str, depth: int,
        cumulative_prob: float, month_branch: str, max_depth: int,
    ) -> TreeNode:
        """递归构建概率树节点。"""
        score = cls._compute_score(hexagram_name, month_branch)
        verdict = cls._compute_verdict(score)

        if depth >= max_depth or cumulative_prob < 0.005:
            return TreeNode(
                hexagram_name=hexagram_name, depth=depth,
                branches=(), children=(),
                cumulative_probability=round(cumulative_prob, 6),
                verdict=verdict, score=score,
            )

        branches = cls._generate_branches(hexagram_name, month_branch)
        children: list[TreeNode] = []
        for i, branch in enumerate(branches):
            child_hex = cls._get_changed_hexagram(hexagram_name, i)
            child = cls._build_node(
                child_hex, depth + 1,
                cumulative_prob * branch.probability,
                month_branch, max_depth,
            )
            children.append(child)

        return TreeNode(
            hexagram_name=hexagram_name, depth=depth,
            branches=branches, children=tuple(children),
            cumulative_probability=round(cumulative_prob, 6),
            verdict=verdict, score=score,
        )

    @classmethod
    def _generate_branches(
        cls, hexagram_name: str, month_branch: str,
    ) -> tuple[TreeBranch, ...]:
        """生成3个分支: 生扶(60%)、克制(25%)、比和(15%)。"""
        try:
            hexagram = HexagramEngine.get_by_name(hexagram_name)
        except ValueError:
            return ()
        h_elem = hexagram.element
        gen = _GENERATES.get(h_elem, h_elem)
        over = _OVERCOMES.get(h_elem, h_elem)

        try:
            prosperity = ElementEngine.judge_prosperity(h_elem, month_branch)
        except ValueError:
            prosperity = ProsperityState.XIU
        probs = _PROSPERITY_PROBS.get(prosperity, _DEFAULT_PROBS)

        return (
            TreeBranch(
                element_change=f"{h_elem.value}生{gen.value}",
                probability=probs[0],
                description=f"生扶:{h_elem.value}生{gen.value}，顺势发展"),
            TreeBranch(
                element_change=f"{h_elem.value}克{over.value}",
                probability=probs[1],
                description=f"克制:{h_elem.value}克{over.value}，受制约"),
            TreeBranch(
                element_change=f"{h_elem.value}比和{h_elem.value}",
                probability=probs[2],
                description=f"比和:{h_elem.value}比和，维持现状"),
        )

    @classmethod
    def _get_changed_hexagram(cls, hexagram_name: str, branch_idx: int) -> str:
        """根据分支索引获取变化后的卦名。"""
        try:
            hexagram = HexagramEngine.get_by_name(hexagram_name)
        except ValueError:
            return hexagram_name
        try:
            if branch_idx == 0:
                result = HexagramEngine.get_changed(hexagram, (1,))
            elif branch_idx == 1:
                result = HexagramEngine.get_opposite(hexagram)
            else:
                result = HexagramEngine.get_interlock(hexagram)
            return result.name
        except (ValueError, KeyError):
            return hexagram_name

    @classmethod
    def _compute_score(cls, hexagram_name: str, month_branch: str) -> int:
        """计算卦象得分(0-100)。"""
        try:
            hexagram = HexagramEngine.get_by_name(hexagram_name)
        except ValueError:
            return 50
        h_elem = hexagram.element
        u_elem = hexagram.upper_trigram.element
        l_elem = hexagram.lower_trigram.element
        score = 50
        try:
            pros = ElementEngine.judge_prosperity(h_elem, month_branch)
            score += _PROSPERITY_BONUS.get(pros, 0)
        except ValueError:
            pass
        rel = ElementEngine.get_relation(l_elem, u_elem)
        score += _REL_BONUS.get(rel, 0)
        return max(0, min(100, score))

    @classmethod
    def _compute_verdict(cls, score: int) -> str:
        """根据得分判定吉/凶/平。"""
        if score >= 65:
            return "吉"
        if score <= 35:
            return "凶"
        return "平"

    @classmethod
    def _count_paths(cls, node: TreeNode) -> int:
        """统计从节点到叶子的路径数。"""
        if not node.children:
            return 1
        return sum(cls._count_paths(c) for c in node.children)

    @classmethod
    def _compute_expected_value(cls, node: TreeNode) -> float:
        """计算树的期望值(加权平均所有叶子得分)。"""
        leaves = cls._collect_leaves(node)
        if not leaves:
            return float(node.score)
        total_w = sum(l.cumulative_probability for l in leaves)
        if total_w == 0:
            return float(node.score)
        return round(
            sum(l.score * l.cumulative_probability for l in leaves) / total_w, 2)

    @classmethod
    def _collect_leaves(cls, node: TreeNode) -> list[TreeNode]:
        """收集所有叶子节点。"""
        if not node.children:
            return [node]
        result: list[TreeNode] = []
        for c in node.children:
            result.extend(cls._collect_leaves(c))
        return result

    @classmethod
    def _assess_risk(cls, node: TreeNode, expected_value: float) -> str:
        """评估风险等级。"""
        leaves = cls._collect_leaves(node)
        if not leaves:
            return "数据不足，无法评估风险"
        total = len(leaves)
        ji = sum(1 for l in leaves if l.verdict == "吉")
        xiong = sum(1 for l in leaves if l.verdict == "凶")
        ping = total - ji - xiong
        ji_r = ji / total if total > 0 else 0
        xiong_r = xiong / total if total > 0 else 0
        scores = [l.score for l in leaves]
        mean = sum(scores) / len(scores) if scores else 50
        var = sum((s - mean) ** 2 for s in scores) / len(scores) if scores else 0
        std = var ** 0.5

        if expected_value >= 65 and ji_r >= 0.5:
            level, advice = "低风险", "多数路径指向吉，可积极把握"
        elif expected_value <= 35 and xiong_r >= 0.5:
            level, advice = "高风险", "多数路径指向凶，宜守不宜进"
        elif std > 20:
            level, advice = "中高风险", "结果波动大，需谨慎决策"
        elif std > 10:
            level, advice = "中等风险", "有一定不确定性，建议稳步推进"
        else:
            level, advice = "低风险", "结果较为稳定，可按计划行事"

        return (
            f"{level}。期望值:{expected_value:.1f}分。"
            f"吉{ji}/{total} 凶{xiong}/{total} 平{ping}/{total}。"
            f"标准差:{std:.1f}。{advice}。")

    @classmethod
    def _prune_node(cls, node: TreeNode, threshold: float) -> TreeNode:
        """剪枝低概率节点。"""
        if not node.children:
            return node
        pruned_children: list[TreeNode] = []
        pruned_branches: list[TreeBranch] = []
        for i, child in enumerate(node.children):
            if child.cumulative_probability >= threshold:
                pruned_children.append(cls._prune_node(child, threshold))
                if i < len(node.branches):
                    pruned_branches.append(node.branches[i])
        return TreeNode(
            hexagram_name=node.hexagram_name, depth=node.depth,
            branches=tuple(pruned_branches), children=tuple(pruned_children),
            cumulative_probability=node.cumulative_probability,
            verdict=node.verdict, score=node.score,
        )

    @classmethod
    def enumerate_paths(
        cls, tree: ProbabilityTree,
    ) -> list[tuple[tuple[str, ...], float, str, int]]:
        """枚举所有从根到叶的路径。

        Returns:
            路径列表: (卦名序列, 累积概率, 吉凶, 得分)
        """
        paths: list[tuple[tuple[str, ...], float, str, int]] = []
        cls._collect_paths(tree.root, [tree.root.hexagram_name], paths)
        return paths

    @classmethod
    def _collect_paths(
        cls, node: TreeNode, current: list[str],
        result: list[tuple[tuple[str, ...], float, str, int]],
    ) -> None:
        if not node.children:
            result.append((
                tuple(current), node.cumulative_probability,
                node.verdict, node.score,
            ))
            return
        for child in node.children:
            cls._collect_paths(child, current + [child.hexagram_name], result)

    @classmethod
    def get_top_paths(
        cls, tree: ProbabilityTree, n: int = 5,
    ) -> list[tuple[tuple[str, ...], float, str, int]]:
        """获取概率最高的前N条路径。"""
        all_paths = cls.enumerate_paths(tree)
        all_paths.sort(key=lambda p: p[1], reverse=True)
        return all_paths[:n]
