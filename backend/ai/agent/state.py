"""Agent工作流状态定义"""
from __future__ import annotations
from typing import TypedDict, Annotated, Literal
from dataclasses import dataclass, field


class AgentState(TypedDict, total=False):
    """Agent工作流状态

    流经所有节点的共享状态。
    """
    # 输入
    user_query: str                          # 用户原始问题
    hexagram_data: dict | None               # 卦象结构化数据
    session_id: str                          # 会话ID
    user_id: str                             # 用户ID

    # 意图分类结果
    intent: str                              # divination/trend/learn/evolution
    entities: dict                           # 提取的实体
    confidence: float                        # 意图分类置信度

    # 规则引擎结果
    rule_analysis: dict | None               # 规则分析结果

    # RAG检索结果
    rag_context: str | None                  # 融合后的上下文

    # 中间结果
    interpretation_draft: str                # AI解释草稿
    risk_flags: list[str]                    # 风险标记
    sentiment: str                           # 用户情绪判断

    # 记忆系统
    user_memory: dict | None                 # 记忆召回结果
    conversation_history: list[dict]         # 会话历史

    # 推演结果
    inference_result: dict | None            # 推演结果

    # 输出
    final_response: str                      # 最终回复
    response_metadata: dict                  # 元数据

    # 控制流
    current_step: str                        # 当前执行步骤
    errors: list[str]                        # 错误记录
    retry_count: int                         # 重试计数


@dataclass(frozen=True)
class AgentConfig:
    """Agent配置"""
    max_retries: int = 2
    timeout_seconds: int = 30
    enable_evolution: bool = True
    enable_memory: bool = True   # Phase 2 M2.4
    safety_check: bool = True
