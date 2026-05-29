"""
A/B 测试管理器
支持 Prompt 版本对比、模型配置对比、流量分配
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ExperimentStatus(str, Enum):
    """实验状态"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class Variant(str, Enum):
    """变体"""
    A = "a"
    B = "b"


@dataclass(frozen=True)
class ExperimentVariant:
    """实验变体配置"""
    variant_id: Variant
    prompt_id: str | None = None
    model_id: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    custom_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Experiment:
    """A/B 测试实验"""
    experiment_id: str
    name: str
    description: str
    variant_a: ExperimentVariant
    variant_b: ExperimentVariant
    traffic_split: float = 0.5  # variant_a 的流量比例
    metrics: list[str] = field(default_factory=lambda: ["safety_score", "fluency", "relevance"])
    min_samples: int = 100
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: str | None = None
    ended_at: str | None = None


@dataclass(frozen=True)
class ExperimentResult:
    """实验结果"""
    experiment_id: str
    variant: Variant
    user_id: str
    metrics: dict[str, float]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ExperimentReport:
    """实验报告"""
    experiment_id: str
    variant_a_scores: dict[str, float]
    variant_b_scores: dict[str, float]
    variant_a_count: int
    variant_b_count: int
    winner: Variant | None
    confidence: float  # 置信度 0-1
    recommendation: str


class ABTestManager:
    """
    A/B 测试管理器
    - 确定性变体分配（基于用户ID哈希）
    - 多指标对比
    - 自动胜负判定
    """

    def __init__(self) -> None:
        self._experiments: dict[str, Experiment] = {}
        self._results: dict[str, list[ExperimentResult]] = {}

    def create_experiment(self, experiment: Experiment) -> None:
        """创建实验"""
        self._experiments[experiment.experiment_id] = experiment
        self._results[experiment.experiment_id] = []

    def start_experiment(self, experiment_id: str) -> None:
        """启动实验"""
        exp = self._experiments.get(experiment_id)
        if exp:
            exp.status = ExperimentStatus.RUNNING
            exp.started_at = datetime.now(timezone.utc).isoformat()

    def stop_experiment(self, experiment_id: str) -> None:
        """停止实验"""
        exp = self._experiments.get(experiment_id)
        if exp:
            exp.status = ExperimentStatus.COMPLETED
            exp.ended_at = datetime.now(timezone.utc).isoformat()

    def assign_variant(self, experiment_id: str, user_id: str) -> Variant:
        """
        确定性分配变体
        基于 experiment_id + user_id 的哈希，保证同一用户始终看到同一变体
        """
        exp = self._experiments.get(experiment_id)
        if not exp or exp.status != ExperimentStatus.RUNNING:
            return Variant.A  # 默认返回 A

        hash_input = f"{experiment_id}:{user_id}"
        hash_val = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        threshold = hash_val / 0xFFFFFFFF

        return Variant.A if threshold < exp.traffic_split else Variant.B

    def get_variant_config(self, experiment_id: str, variant: Variant) -> ExperimentVariant | None:
        """获取变体配置"""
        exp = self._experiments.get(experiment_id)
        if not exp:
            return None
        return exp.variant_a if variant == Variant.A else exp.variant_b

    def record_result(self, result: ExperimentResult) -> None:
        """记录实验结果"""
        if result.experiment_id in self._results:
            self._results[result.experiment_id].append(result)

    def get_report(self, experiment_id: str) -> ExperimentReport | None:
        """生成实验报告"""
        exp = self._experiments.get(experiment_id)
        if not exp:
            return None

        results = self._results.get(experiment_id, [])
        a_results = [r for r in results if r.variant == Variant.A]
        b_results = [r for r in results if r.variant == Variant.B]

        # 聚合各指标
        a_scores = self._aggregate_metrics(a_results, exp.metrics)
        b_scores = self._aggregate_metrics(b_results, exp.metrics)

        # 判定胜负
        winner, confidence = self._determine_winner(a_scores, b_scores, len(a_results), len(b_results))

        # 生成建议
        recommendation = self._generate_recommendation(exp, a_scores, b_scores, winner, confidence)

        return ExperimentReport(
            experiment_id=experiment_id,
            variant_a_scores=a_scores,
            variant_b_scores=b_scores,
            variant_a_count=len(a_results),
            variant_b_count=len(b_results),
            winner=winner,
            confidence=confidence,
            recommendation=recommendation,
        )

    def _aggregate_metrics(
        self,
        results: list[ExperimentResult],
        metrics: list[str],
    ) -> dict[str, float]:
        """聚合指标均值"""
        if not results:
            return {m: 0.0 for m in metrics}

        agg: dict[str, float] = {}
        for m in metrics:
            values = [r.metrics.get(m, 0.0) for r in results]
            agg[m] = sum(values) / len(values) if values else 0.0
        return agg

    def _determine_winner(
        self,
        a_scores: dict[str, float],
        b_scores: dict[str, float],
        a_count: int,
        b_count: int,
    ) -> tuple[Variant | None, float]:
        """
        判定胜负
        使用简化的效果量(effect size)方法
        """
        if a_count < 30 or b_count < 30:
            return None, 0.0  # 样本不足

        a_total = sum(a_scores.values())
        b_total = sum(b_scores.values())

        if a_total == 0 and b_total == 0:
            return None, 0.0

        diff = abs(a_total - b_total)
        avg = (a_total + b_total) / 2

        if avg == 0:
            return None, 0.0

        effect_size = diff / avg

        # 效果量阈值: 5% 以上差异才判定
        if effect_size < 0.05:
            return None, min(effect_size / 0.05, 1.0)

        winner = Variant.A if a_total > b_total else Variant.B
        confidence = min(effect_size / 0.2, 1.0)  # 20%差异时置信度为1

        return winner, confidence

    def _generate_recommendation(
        self,
        exp: Experiment,
        a_scores: dict[str, float],
        b_scores: dict[str, float],
        winner: Variant | None,
        confidence: float,
    ) -> str:
        """生成推荐建议"""
        if winner is None:
            if confidence < 0.3:
                return "样本不足或差异不显著，建议继续收集数据"
            return "两组表现接近，建议从具体指标维度分析"

        winner_name = "A" if winner == Variant.A else "B"
        winner_config = exp.variant_a if winner == Variant.A else exp.variant_b

        parts = [f"推荐变体 {winner_name}"]
        if winner_config.prompt_id:
            parts.append(f"Prompt: {winner_config.prompt_id}")
        if winner_config.model_id:
            parts.append(f"模型: {winner_config.model_id}")
        parts.append(f"置信度: {confidence:.1%}")

        return " | ".join(parts)

    def list_experiments(self, status: ExperimentStatus | None = None) -> list[Experiment]:
        """列出实验"""
        experiments = list(self._experiments.values())
        if status:
            experiments = [e for e in experiments if e.status == status]
        return experiments

    def get_experiment(self, experiment_id: str) -> Experiment | None:
        """获取实验详情"""
        return self._experiments.get(experiment_id)
