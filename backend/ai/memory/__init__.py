"""记忆系统模块

四层长期记忆架构：工作记忆、情景记忆、语义记忆、程序记忆。
"""
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
from ai.memory.working import WorkingMemory
from ai.memory.episodic import EpisodicMemory
from ai.memory.semantic import SemanticMemory
from ai.memory.procedural import ProceduralMemory
from ai.memory.engine import MemoryEngine

__all__ = [
    # 类型
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
    # 引擎
    "WorkingMemory",
    "EpisodicMemory",
    "SemanticMemory",
    "ProceduralMemory",
    "MemoryEngine",
]
