"""深度推演引擎 - 类型定义

枚举和不可变数据类定义。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class StepType(str, Enum):
    """推理步骤类型"""
    ANALYZE = "分析"
    INFER = "推断"
    COMPARE = "比对"
    DEDUCE = "演绎"
    SYNTHESIZE = "综合"
    PREDICT = "预测"
    VALIDATE = "验证"
    BRANCH = "分支"
    REFINE = "精炼"
    CONCLUDE = "结论"


class ConfidenceLevel(str, Enum):
    """置信度等级"""
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"
    SPECULATIVE = "推测"


@dataclass(frozen=True)
class ReasoningStep:
    """单步推理记录"""
    step_number: int
    step_type: StepType
    input_state: str
    logic: str
    output_state: str
    confidence: ConfidenceLevel
    element_changes: tuple[str, ...]
    related_hexagrams: tuple[str, ...]


@dataclass(frozen=True)
class ReasoningChain:
    """推理链"""
    steps: tuple[ReasoningStep, ...]
    initial_hexagram: str
    final_hexagram: str | None
    branch_points: tuple[int, ...]
    overall_confidence: ConfidenceLevel
    conclusion: str
    probability_distribution: tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class TreeBranch:
    """概率树分支"""
    element_change: str
    probability: float
    description: str


@dataclass(frozen=True)
class TreeNode:
    """概率树节点"""
    hexagram_name: str
    depth: int
    branches: tuple[TreeBranch, ...]
    children: tuple["TreeNode", ...]
    cumulative_probability: float
    verdict: str
    score: int


@dataclass(frozen=True)
class ProbabilityTree:
    """概率推演树"""
    root: TreeNode
    max_depth: int
    branch_factor: int
    total_paths: int
    expected_value: float
    risk_assessment: str
