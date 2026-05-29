"""AI解释模块

将规则分析结果翻译成通俗易懂的自然语言解释。

核心组件：
- LLMClient: LLM API客户端
- AIInterpreter: AI解释器
- PromptBuilder: Prompt构建器
- KnowledgeBase: 易经知识库（RAG）
- SafetyChecker: 输出安全检查
"""

from ai.llm_client import (
    LLMClient,
    LLMConfig,
    LLMError,
    LLMAuthError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
)
from ai.interpreter import AIInterpreter
from ai.prompt_builder import PromptBuilder
from ai.config import LLM_CONFIGS, DEFAULT_LLM, get_default_config
from ai.knowledge_base import KnowledgeBase
from ai.knowledge_graph import KnowledgeGraph, KnowledgeGraphBuilder
from ai.rag_fusion import RAGFusion
from ai.model_router import ModelRouter, ModelTier
from ai.safety_checker import check_safety, SafetyCheckResult, DISCLAIMER
from ai.multi_model import MultiModelCollaborator, ModelHealthMonitor
from ai.cache import MultiLevelCache, LRUCache, CacheKeyBuilder, RateLimiter
from ai.evaluation.evaluator import AutoEvaluator, EvalResult, EvalCase
from ai.evaluation.ab_testing import ABTestManager, Experiment
from ai.prompt_manager.version_control import PromptVersionControl, PromptVersion
from ai.prompt_manager.registry import PromptRegistry, PromptTemplate
from ai.reasoning.deep_reasoning import DeepReasoningEngine
from ai.reasoning.probability_tree import ProbabilityTreeEngine
from ai.reasoning.types import (
    StepType,
    ConfidenceLevel,
    ReasoningStep,
    ReasoningChain,
    TreeBranch,
    TreeNode,
    ProbabilityTree,
)
from ai.memory.engine import MemoryEngine
from ai.memory.working import WorkingMemory
from ai.memory.episodic import EpisodicMemory
from ai.memory.semantic import SemanticMemory
from ai.memory.procedural import ProceduralMemory
from ai.memory.types import (
    MemoryType,
    EmotionalState,
    PatternType,
    UserMemory,
    Pattern,
    RiskIndicator,
    EmotionalTrajectory,
    UserChangeModel,
    MemoryRecall,
    UserMemoryProfile,
)
from ai.observation import (
    ObservationAgent,
    PatternDetector,
    AnomalyDetector,
    TrendReporter,
    ObservationConfig,
)
from ai.plugins import (
    PluginRegistry,
    PluginManager,
    PluginType,
    HookPoint,
    PluginInfo,
)
from ai.i18n import (
    Translator,
    PromptTemplateManager,
    Language,
    load_builtin_templates,
)
from ai.api_platform import (
    APIKeyManager,
    APIRateLimiter,
    APIPermission,
)
from ai.analytics import (
    EventTracker,
    EventType,
)
from ai.enterprise import (
    TenantManager,
    Role,
    Permission,
)

__all__ = [
    # 客户端
    "LLMClient",
    "LLMConfig",
    # 异常
    "LLMError",
    "LLMAuthError",
    "LLMRateLimitError",
    "LLMResponseError",
    "LLMTimeoutError",
    # 解释器
    "AIInterpreter",
    # Prompt
    "PromptBuilder",
    # 知识库
    "KnowledgeBase",
    # 知识图谱
    "KnowledgeGraph",
    "KnowledgeGraphBuilder",
    # RAG融合
    "RAGFusion",
    # 模型路由
    "ModelRouter",
    "ModelTier",
    # 安全检查
    "check_safety",
    "SafetyCheckResult",
    "DISCLAIMER",
    # 配置
    "LLM_CONFIGS",
    "DEFAULT_LLM",
    "get_default_config",
    # 多模型协同
    "MultiModelCollaborator",
    "ModelHealthMonitor",
    # 缓存
    "MultiLevelCache",
    "LRUCache",
    "CacheKeyBuilder",
    "RateLimiter",
    # 评估
    "AutoEvaluator",
    "EvalResult",
    "EvalCase",
    "ABTestManager",
    "Experiment",
    # Prompt管理
    "PromptVersionControl",
    "PromptVersion",
    "PromptRegistry",
    "PromptTemplate",
    # 深度推演
    "DeepReasoningEngine",
    "ProbabilityTreeEngine",
    "StepType",
    "ConfidenceLevel",
    "ReasoningStep",
    "ReasoningChain",
    "TreeBranch",
    "TreeNode",
    "ProbabilityTree",
    # 记忆系统
    "MemoryEngine",
    "WorkingMemory",
    "EpisodicMemory",
    "SemanticMemory",
    "ProceduralMemory",
    "MemoryType",
    "EmotionalState",
    "PatternType",
    "UserMemory",
    "Pattern",
    "RiskIndicator",
    "EmotionalTrajectory",
    "UserChangeModel",
    "MemoryRecall",
    "UserMemoryProfile",
    # 观察Agent
    "ObservationAgent",
    "PatternDetector",
    "AnomalyDetector",
    "TrendReporter",
    "ObservationConfig",
    # 插件系统
    "PluginRegistry",
    "PluginManager",
    "PluginType",
    "HookPoint",
    "PluginInfo",
    # 国际化
    "Translator",
    "PromptTemplateManager",
    "Language",
    "load_builtin_templates",
    # API平台
    "APIKeyManager",
    "APIRateLimiter",
    "APIPermission",
    # 数据分析
    "EventTracker",
    "EventType",
    # 企业版
    "TenantManager",
    "Role",
    "Permission",
]
