"""
Prompt 注册中心
管理 Prompt 模板的注册、查询、分类
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class PromptCategory(str, Enum):
    """Prompt 分类"""
    INTENT = "intent"                # 意图分类
    INTERPRETATION = "interpretation"  # 卦象解释
    TREND = "trend"                  # 趋势分析
    EVOLUTION = "evolution"          # 推演模拟
    MEMORY = "memory"                # 记忆相关
    SAFETY = "safety"                # 安全检查
    SYSTEM = "system"                # 系统级
    SYNTHESIS = "synthesis"          # 结果合成


class PromptTier(str, Enum):
    """Prompt 对应的模型层级"""
    TIER_1 = "tier_1"    # 轻量推理
    TIER_2 = "tier_2"    # 标准解释
    TIER_3 = "tier_3"    # 深度分析
    TIER_4 = "tier_4"    # 推演规划


@dataclass(frozen=True)
class PromptTemplate:
    """Prompt 模板"""
    prompt_id: str
    category: PromptCategory
    tier: PromptTier
    system_prompt: str
    user_prompt: str
    variables: tuple[str, ...] = ()
    description: str = ""
    model_preference: tuple[str, ...] = ()
    max_tokens: int = 2000
    temperature: float = 0.7
    version: str = "1.0.0"
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class PromptRegistry:
    """
    Prompt 注册中心
    - 模板注册与查询
    - 按分类/层级筛选
    - 模板渲染（变量替换）
    """

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}
        self._category_index: dict[PromptCategory, list[str]] = {c: [] for c in PromptCategory}
        self._tier_index: dict[PromptTier, list[str]] = {t: [] for t in PromptTier}

    def register(self, template: PromptTemplate) -> None:
        """注册模板"""
        self._templates[template.prompt_id] = template

        # 更新索引
        if template.prompt_id not in self._category_index[template.category]:
            self._category_index[template.category].append(template.prompt_id)
        if template.prompt_id not in self._tier_index[template.tier]:
            self._tier_index[template.tier].append(template.prompt_id)

    def get(self, prompt_id: str) -> PromptTemplate | None:
        """获取模板"""
        return self._templates.get(prompt_id)

    def get_by_category(self, category: PromptCategory) -> list[PromptTemplate]:
        """按分类获取"""
        ids = self._category_index.get(category, [])
        return [self._templates[tid] for tid in ids if tid in self._templates]

    def get_by_tier(self, tier: PromptTier) -> list[PromptTemplate]:
        """按层级获取"""
        ids = self._tier_index.get(tier, [])
        return [self._templates[tid] for tid in ids if tid in self._templates]

    def render(self, prompt_id: str, variables: dict[str, str]) -> tuple[str, str]:
        """
        渲染模板（变量替换）
        返回 (system_prompt, user_prompt)
        """
        template = self._templates.get(prompt_id)
        if not template:
            raise ValueError(f"Template not found: {prompt_id}")

        system = template.system_prompt
        user = template.user_prompt

        for key, value in variables.items():
            placeholder = "{" + key + "}"
            system = system.replace(placeholder, value)
            user = user.replace(placeholder, value)

        return system, user

    def list_all(self) -> list[PromptTemplate]:
        """列出所有模板"""
        return list(self._templates.values())

    def search(self, keyword: str) -> list[PromptTemplate]:
        """关键词搜索"""
        results = []
        for t in self._templates.values():
            if (
                keyword.lower() in t.prompt_id.lower()
                or keyword.lower() in t.description.lower()
                or keyword.lower() in " ".join(t.tags).lower()
            ):
                results.append(t)
        return results

    def register_defaults(self) -> None:
        """注册默认模板"""
        # 意图分类
        self.register(PromptTemplate(
            prompt_id="intent_classify_v1",
            category=PromptCategory.INTENT,
            tier=PromptTier.TIER_1,
            system_prompt="你是易学AI系统的意图分类器。分析用户查询，返回JSON格式的分类结果。",
            user_prompt="""分析以下用户查询，返回JSON:
1. intent: divination | trend_analysis | learning | evolution_simulation
2. entities: 提取的实体（卦名、五行、时间等）
3. confidence: 分类置信度 (0-1)

用户查询: {query}""",
            variables=("query",),
            description="意图分类Prompt",
            max_tokens=500,
            temperature=0.1,
            tags=("intent", "classification"),
        ))

        # 卦象解释
        self.register(PromptTemplate(
            prompt_id="hexagram_interpret_v1",
            category=PromptCategory.INTERPRETATION,
            tier=PromptTier.TIER_2,
            system_prompt="""你是 YI-AI 易学解释系统。将规则引擎的确定性分析结果翻译为用户可理解的自然语言解释。

核心原则:
1. 规则优先 - 基于规则引擎结果，不自行推导
2. 不确定性标记 - 信息有限时明确说明
3. 禁止确定性承诺 - 不使用"一定"、"必然"等词语
4. 现代语义 - 用现代语言解释，保留专业术语并附带解释
5. 变化视角 - 强调"状态变化"而非"结果预测" """,
            user_prompt="""## 用户问题
{query}

## 卦象数据
{hexagram_data}

## 规则引擎分析结果
{rule_results}

{rag_context}

{user_memory}

请基于以上规则引擎的结果，为用户提供易懂的解释。强调这是对当前状态的分析，而非对未来的预测。
末尾添加免责声明。""",
            variables=("query", "hexagram_data", "rule_results", "rag_context", "user_memory"),
            description="卦象解释核心Prompt",
            model_preference=("qwen-max", "deepseek-chat"),
            max_tokens=2000,
            temperature=0.7,
            tags=("interpretation", "core"),
        ))

        # 趋势分析
        self.register(PromptTemplate(
            prompt_id="trend_analysis_v1",
            category=PromptCategory.TREND,
            tier=PromptTier.TIER_3,
            system_prompt="你是易学趋势分析师。基于用户的历史卦象数据，分析长期变化趋势。",
            user_prompt="""## 用户历史卦象
{history}

## 当前卦象
{current_hexagram}

## 分析要求
请分析用户近期的卦象变化趋势，识别:
1. 反复出现的主题
2. 情绪变化轨迹
3. 五行偏向变化
4. 关键转折点

注意: 这是状态分析，不是预测。""",
            variables=("history", "current_hexagram"),
            description="趋势分析Prompt",
            max_tokens=3000,
            temperature=0.7,
            tags=("trend", "analysis"),
        ))

        # 安全检查
        self.register(PromptTemplate(
            prompt_id="safety_fix_v1",
            category=PromptCategory.SAFETY,
            tier=PromptTier.TIER_1,
            system_prompt="你是安全修正器。修正包含不当内容的易学解释。",
            user_prompt="""以下解释存在安全问题，请修正:
问题: {issues}
原始解释: {original}

修正要求:
1. 移除确定性承诺
2. 添加不确定性标记
3. 保留分析价值""",
            variables=("issues", "original"),
            description="安全修正Prompt",
            max_tokens=1000,
            temperature=0.3,
            tags=("safety", "fix"),
        ))
