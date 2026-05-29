"""多模型并行协同系统

实现4模型并行调用、结果融合、健康监控、动态权重。

架构：
- ParallelCaller: 并行调用多个模型
- ResultFuser: 融合多个模型的结果
- ModelHealthMonitor: 模型健康监控
- DynamicWeightBalancer: 动态权重调整
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Awaitable, Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelCallResult:
    """单个模型调用结果"""
    model_id: str
    tier: str
    response: str
    latency_ms: float
    tokens_used: int
    cost_usd: float
    success: bool
    error: str | None = None


@dataclass(frozen=True)
class FusedResult:
    """融合结果"""
    fused_response: str
    model_results: tuple[ModelCallResult, ...]
    fusion_method: str
    confidence: float
    total_cost_usd: float
    total_latency_ms: float


@dataclass
class ModelHealth:
    """模型健康状态"""
    model_id: str
    success_count: int = 0
    failure_count: int = 0
    total_latency_ms: float = 0.0
    last_success_time: float = 0.0
    last_failure_time: float = 0.0
    health_score: float = 1.0  # 0.0-1.0

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total

    @property
    def avg_latency_ms(self) -> float:
        if self.success_count == 0:
            return 0.0
        return self.total_latency_ms / self.success_count


class ModelHealthMonitor:
    """模型健康监控

    跟踪每个模型的成功率、延迟、错误率。
    """

    def __init__(self):
        self._health: dict[str, ModelHealth] = {}

    def record_success(self, model_id: str, latency_ms: float) -> None:
        """记录成功调用"""
        if model_id not in self._health:
            self._health[model_id] = ModelHealth(model_id=model_id)

        health = self._health[model_id]
        health.success_count += 1
        health.total_latency_ms += latency_ms
        health.last_success_time = time.time()
        health.health_score = min(1.0, health.health_score + 0.05)

    def record_failure(self, model_id: str, error: str) -> None:
        """记录失败调用"""
        if model_id not in self._health:
            self._health[model_id] = ModelHealth(model_id=model_id)

        health = self._health[model_id]
        health.failure_count += 1
        health.last_failure_time = time.time()
        health.health_score = max(0.0, health.health_score - 0.2)

    def get_health(self, model_id: str) -> ModelHealth:
        """获取模型健康状态"""
        if model_id not in self._health:
            self._health[model_id] = ModelHealth(model_id=model_id)
        return self._health[model_id]

    def get_all_health(self) -> dict[str, ModelHealth]:
        """获取所有模型健康状态"""
        return dict(self._health)

    def is_model_healthy(self, model_id: str, threshold: float = 0.3) -> bool:
        """检查模型是否健康"""
        health = self.get_health(model_id)
        return health.health_score >= threshold


class DynamicWeightBalancer:
    """动态权重平衡器

    根据模型健康状态和历史表现动态调整权重。
    """

    def __init__(self, monitor: ModelHealthMonitor):
        self.monitor = monitor
        self._base_weights: dict[str, float] = {}

    def set_base_weights(self, weights: dict[str, float]) -> None:
        """设置基础权重"""
        self._base_weights = dict(weights)

    def get_dynamic_weights(self, model_ids: list[str]) -> dict[str, float]:
        """获取动态调整后的权重

        Args:
            model_ids: 参与的模型ID列表

        Returns:
            调整后的权重字典
        """
        if not model_ids:
            return {}

        # 获取基础权重
        weights = {}
        for mid in model_ids:
            base = self._base_weights.get(mid, 1.0)
            health = self.monitor.get_health(mid)

            # 根据健康分数调整权重
            adjusted = base * health.health_score

            # 根据延迟调整（延迟越高，权重越低）
            if health.avg_latency_ms > 0:
                latency_factor = min(1.0, 1000.0 / health.avg_latency_ms)
                adjusted *= latency_factor

            weights[mid] = max(0.01, adjusted)  # 最小权重0.01

        # 归一化
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return weights


class ParallelCaller:
    """并行调用器

    并行调用多个模型，支持超时和降级。
    """

    def __init__(
        self,
        monitor: ModelHealthMonitor | None = None,
        timeout_seconds: float = 30.0,
    ):
        self.monitor = monitor or ModelHealthMonitor()
        self.timeout = timeout_seconds

    async def call_parallel(
        self,
        calls: list[tuple[str, Callable[[], Awaitable[str]]]],
    ) -> list[ModelCallResult]:
        """并行调用多个模型

        Args:
            calls: [(model_id, call_fn), ...] 列表

        Returns:
            调用结果列表
        """
        async def _single_call(
            model_id: str,
            call_fn: Callable[[], Awaitable[str]],
        ) -> ModelCallResult:
            start = time.monotonic()
            try:
                response = await asyncio.wait_for(
                    call_fn(), timeout=self.timeout
                )
                latency = (time.monotonic() - start) * 1000
                self.monitor.record_success(model_id, latency)
                return ModelCallResult(
                    model_id=model_id,
                    tier="",
                    response=response,
                    latency_ms=latency,
                    tokens_used=0,
                    cost_usd=0.0,
                    success=True,
                )
            except asyncio.TimeoutError:
                latency = (time.monotonic() - start) * 1000
                self.monitor.record_failure(model_id, "timeout")
                return ModelCallResult(
                    model_id=model_id,
                    tier="",
                    response="",
                    latency_ms=latency,
                    tokens_used=0,
                    cost_usd=0.0,
                    success=False,
                    error="timeout",
                )
            except Exception as e:
                latency = (time.monotonic() - start) * 1000
                self.monitor.record_failure(model_id, str(e))
                return ModelCallResult(
                    model_id=model_id,
                    tier="",
                    response="",
                    latency_ms=latency,
                    tokens_used=0,
                    cost_usd=0.0,
                    success=False,
                    error=str(e),
                )

        tasks = [_single_call(mid, fn) for mid, fn in calls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results = []
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"parallel_call_exception: {r}")
            elif isinstance(r, ModelCallResult):
                final_results.append(r)

        return final_results


class ResultFuser:
    """结果融合器

    融合多个模型的输出为一个最佳结果。
    """

    @staticmethod
    def fuse_by_confidence(results: list[ModelCallResult]) -> FusedResult:
        """按置信度融合

        选择成功调用中延迟最低的结果作为主结果。
        """
        successful = [r for r in results if r.success]

        if not successful:
            return FusedResult(
                fused_response="所有模型调用失败",
                model_results=tuple(results),
                fusion_method="fallback",
                confidence=0.0,
                total_cost_usd=sum(r.cost_usd for r in results),
                total_latency_ms=max((r.latency_ms for r in results), default=0),
            )

        # 选择延迟最低的
        best = min(successful, key=lambda r: r.latency_ms)

        return FusedResult(
            fused_response=best.response,
            model_results=tuple(results),
            fusion_method="best_latency",
            confidence=0.8,
            total_cost_usd=sum(r.cost_usd for r in results),
            total_latency_ms=max(r.latency_ms for r in results),
        )

    @staticmethod
    def fuse_by_voting(results: list[ModelCallResult]) -> FusedResult:
        """投票融合

        多个模型的结果取最长（信息量最大）的。
        """
        successful = [r for r in results if r.success]

        if not successful:
            return FusedResult(
                fused_response="所有模型调用失败",
                model_results=tuple(results),
                fusion_method="fallback",
                confidence=0.0,
                total_cost_usd=sum(r.cost_usd for r in results),
                total_latency_ms=max((r.latency_ms for r in results), default=0),
            )

        # 选择最长的响应（信息量最大）
        best = max(successful, key=lambda r: len(r.response))

        return FusedResult(
            fused_response=best.response,
            model_results=tuple(results),
            fusion_method="longest_response",
            confidence=0.7,
            total_cost_usd=sum(r.cost_usd for r in results),
            total_latency_ms=max(r.latency_ms for r in results),
        )


class MultiModelCollaborator:
    """多模型协同器

    高层接口，管理多模型并行调用的完整流程。
    """

    def __init__(self):
        self.monitor = ModelHealthMonitor()
        self.balancer = DynamicWeightBalancer(self.monitor)
        self.caller = ParallelCaller(self.monitor)
        self.fuser = ResultFuser()

    async def collaborate(
        self,
        prompt: str,
        models: list[tuple[str, Callable[[], Awaitable[str]]]],
        fusion_method: str = "confidence",
    ) -> FusedResult:
        """执行多模型协同

        Args:
            prompt: 输入prompt（用于日志）
            models: [(model_id, call_fn), ...]
            fusion_method: 融合方法 ("confidence" | "voting")

        Returns:
            融合结果
        """
        logger.info(
            "multi_model_collaborate",
            model_count=len(models),
            fusion_method=fusion_method,
        )

        # 并行调用
        results = await self.caller.call_parallel(models)

        # 融合结果
        if fusion_method == "voting":
            fused = self.fuser.fuse_by_voting(results)
        else:
            fused = self.fuser.fuse_by_confidence(results)

        logger.info(
            "multi_model_fused",
            fusion_method=fused.fusion_method,
            confidence=fused.confidence,
            successful_count=sum(1 for r in results if r.success),
            total_count=len(results),
        )

        return fused

    def get_health_report(self) -> dict:
        """获取健康报告"""
        all_health = self.monitor.get_all_health()
        return {
            model_id: {
                "health_score": h.health_score,
                "success_rate": h.success_rate,
                "avg_latency_ms": h.avg_latency_ms,
                "total_calls": h.success_count + h.failure_count,
            }
            for model_id, h in all_health.items()
        }
