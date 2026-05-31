"""规则引擎共享类型定义

存放 inference_engine 和 evolution_engine 共用的数据类型，
避免重复定义。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InferenceProbabilities:
    """推演概率配置

    将推演引擎中使用的概率值集中管理，便于调优和一致性保证。

    Attributes:
        changed_base: 变卦路径基础概率（动爻数为0时的理论概率）
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
