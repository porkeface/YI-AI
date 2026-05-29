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
]
