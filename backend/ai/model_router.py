"""多模型路由模块

4-Tier模型路由系统，根据任务复杂度选择合适的LLM模型，
实现成本优化和质量平衡。

Tier 1 (快速): 简单问答、格式化 → qwen-turbo (最便宜)
Tier 2 (标准): 一般卦象解释 → deepseek-chat (默认)
Tier 3 (深度): 复杂卦象、多爻联动 → deepseek-chat + 高temperature
Tier 4 (专家): 多卦对比、推演分析 → deepseek-reasoner (最强)

路由策略：
- 默认 Tier 2
- 简单问题（单关键词命中）→ Tier 1
- 复杂问题（多动爻、变卦、特殊卦）→ Tier 3
- 推演/对比类问题 → Tier 4
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

from foundation.types import Hexagram, RuleAnalysisResult

logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    """模型层级"""
    TIER_1_FAST = "tier1"       # 快速/便宜
    TIER_2_STANDARD = "tier2"   # 标准/默认
    TIER_3_DEEP = "tier3"       # 深度分析
    TIER_4_EXPERT = "tier4"     # 专家级


@dataclass(frozen=True)
class TierConfig:
    """层级配置

    Attributes:
        tier: 层级标识
        provider: LLM提供商
        model: 模型名称
        max_tokens: 最大生成token数
        temperature: 温度参数
        cost_per_1k_tokens: 每1000token的成本(元)
        description: 层级描述
    """
    tier: ModelTier
    provider: str
    model: str
    max_tokens: int
    temperature: float
    cost_per_1k_tokens: float
    description: str


# 4-Tier配置表
TIER_CONFIGS: dict[ModelTier, TierConfig] = {
    ModelTier.TIER_1_FAST: TierConfig(
        tier=ModelTier.TIER_1_FAST,
        provider="qwen",
        model="qwen-turbo",
        max_tokens=800,
        temperature=0.5,
        cost_per_1k_tokens=0.002,
        description="快速响应，简单问题",
    ),
    ModelTier.TIER_2_STANDARD: TierConfig(
        tier=ModelTier.TIER_2_STANDARD,
        provider="deepseek",
        model="deepseek-chat",
        max_tokens=2000,
        temperature=0.7,
        cost_per_1k_tokens=0.002,
        description="标准解释，日常使用",
    ),
    ModelTier.TIER_3_DEEP: TierConfig(
        tier=ModelTier.TIER_3_DEEP,
        provider="deepseek",
        model="deepseek-chat",
        max_tokens=3000,
        temperature=0.8,
        cost_per_1k_tokens=0.002,
        description="深度分析，复杂卦象",
    ),
    ModelTier.TIER_4_EXPERT: TierConfig(
        tier=ModelTier.TIER_4_EXPERT,
        provider="deepseek",
        model="deepseek-reasoner",
        max_tokens=4000,
        temperature=0.6,
        cost_per_1k_tokens=0.008,
        description="专家级推理，多卦对比",
    ),
}


# 问题复杂度关键词
_SIMPLE_KEYWORDS: tuple[str, ...] = (
    "什么意思", "怎么解", "好不好", "怎么样", "行不行",
    "可以吗", "能吗", "好吗", "顺利吗",
)

_COMPLEX_KEYWORDS: tuple[str, ...] = (
    "对比", "比较", "推演", "变化", "趋势分析",
    "长期", "综合分析", "多方面", "整体运势",
)


@dataclass(frozen=True)
class RoutingDecision:
    """路由决策结果

    Attributes:
        tier: 选定的层级
        config: 层级配置
        reason: 选择原因
        complexity_score: 复杂度评分 (0-100)
    """
    tier: ModelTier
    config: TierConfig
    reason: str
    complexity_score: int


class ModelRouter:
    """多模型路由器

    根据问题内容和卦象特征自动选择最合适的模型层级。
    """

    @staticmethod
    def route(
        question: str,
        hexagram: Hexagram,
        analysis: RuleAnalysisResult,
    ) -> RoutingDecision:
        """路由决策

        综合评估问题复杂度，选择合适的模型层级。

        评估维度：
        1. 问题文本复杂度（关键词、长度）
        2. 卦象复杂度（动爻数量、是否有变卦）
        3. 分析复杂度（关系数量、置信度）

        Args:
            question: 用户问题
            hexagram: 卦象数据
            analysis: 规则分析结果

        Returns:
            路由决策结果
        """
        score = ModelRouter._compute_complexity(
            question, hexagram, analysis
        )

        tier = ModelRouter._score_to_tier(score)
        config = TIER_CONFIGS[tier]
        reason = ModelRouter._build_reason(tier, score, hexagram, analysis)

        logger.info(
            "model_routing_decision",
            tier=tier.value,
            score=score,
            reason=reason,
        )

        return RoutingDecision(
            tier=tier,
            config=config,
            reason=reason,
            complexity_score=score,
        )

    @staticmethod
    def _compute_complexity(
        question: str,
        hexagram: Hexagram,
        analysis: RuleAnalysisResult,
    ) -> int:
        """计算复杂度评分 (0-100)

        Args:
            question: 用户问题
            hexagram: 卦象数据
            analysis: 规则分析结果

        Returns:
            复杂度评分
        """
        score = 30  # 基础分

        # 1. 问题长度
        if len(question) > 30:
            score += 10
        if len(question) > 60:
            score += 10

        # 2. 简单关键词（降分）
        simple_hits = sum(
            1 for kw in _SIMPLE_KEYWORDS if kw in question
        )
        score -= simple_hits * 8

        # 3. 复杂关键词（加分）
        complex_hits = sum(
            1 for kw in _COMPLEX_KEYWORDS if kw in question
        )
        score += complex_hits * 12

        # 4. 动爻数量
        moving_count = len(analysis.moving_lines)
        if moving_count >= 3:
            score += 20
        elif moving_count >= 2:
            score += 10

        # 5. 分析置信度低（需要更深入分析）
        if analysis.verdict.confidence < 50:
            score += 10

        # 6. 关系描述多（复杂卦象）
        if len(analysis.relationships) >= 4:
            score += 10

        return max(0, min(100, score))

    @staticmethod
    def _score_to_tier(score: int) -> ModelTier:
        """根据分数确定层级

        Args:
            score: 复杂度评分

        Returns:
            模型层级
        """
        if score <= 25:
            return ModelTier.TIER_1_FAST
        elif score <= 55:
            return ModelTier.TIER_2_STANDARD
        elif score <= 80:
            return ModelTier.TIER_3_DEEP
        else:
            return ModelTier.TIER_4_EXPERT

    @staticmethod
    def _build_reason(
        tier: ModelTier,
        score: int,
        hexagram: Hexagram,
        analysis: RuleAnalysisResult,
    ) -> str:
        """构建路由原因说明

        Args:
            tier: 选定层级
            score: 复杂度评分
            hexagram: 卦象数据
            analysis: 规则分析结果

        Returns:
            原因说明文本
        """
        parts: list[str] = []

        moving_count = len(analysis.moving_lines)

        if tier == ModelTier.TIER_1_FAST:
            parts.append("问题简单明确")
        elif tier == ModelTier.TIER_2_STANDARD:
            parts.append("常规卦象解释")
        elif tier == ModelTier.TIER_3_DEEP:
            if moving_count >= 3:
                parts.append(f"多动爻({moving_count}个)")
            if analysis.verdict.confidence < 50:
                parts.append("置信度较低需深入分析")
            parts.append("复杂度较高")
        else:
            parts.append("多维度深度推理")

        return "，".join(parts)

    @staticmethod
    def get_tier_config(tier: ModelTier) -> TierConfig:
        """获取指定层级的配置

        Args:
            tier: 模型层级

        Returns:
            层级配置

        Raises:
            ValueError: 未知的层级
        """
        config = TIER_CONFIGS.get(tier)
        if config is None:
            raise ValueError(f"未知的模型层级: {tier}")
        return config
