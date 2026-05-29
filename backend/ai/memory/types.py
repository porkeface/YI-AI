"""记忆系统类型定义

四层记忆架构的不可变数据类型。
遵循项目规范：frozen dataclass、tuple 代替 list、中文枚举值。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


# ============================================================================
# 枚举
# ============================================================================

class MemoryType(str, Enum):
    """记忆类型"""
    WORKING = "工作"       # 当前会话上下文
    EPISODIC = "情景"      # 具体占卜事件
    SEMANTIC = "语义"      # 知识概念关系
    PROCEDURAL = "程序"    # 行为模式习惯
    EMOTIONAL = "情绪"     # 情绪轨迹


class EmotionalState(str, Enum):
    """情绪状态"""
    POSITIVE = "积极"
    NEUTRAL = "中性"
    ANXIOUS = "焦虑"
    CONFUSED = "困惑"
    HOPEFUL = "期待"
    WORRIED = "担忧"


class PatternType(str, Enum):
    """行为模式类型"""
    FREQUENT_HEXAGRAM = "高频卦象"
    RECURRING_THEME = "反复主题"
    QUESTION_STYLE = "提问风格"
    TIME_PATTERN = "时间规律"
    EMOTIONAL_CYCLE = "情绪周期"


# ============================================================================
# 记忆数据
# ============================================================================

@dataclass(frozen=True)
class UserMemory:
    """单条用户记忆

    所有记忆层的统一数据结构。
    """
    memory_id: str                    # 唯一标识
    user_id: str                      # 用户ID
    memory_type: MemoryType           # 记忆类型
    content: str                      # 记忆内容
    hexagram_name: str | None = None  # 关联卦名
    importance: float = 0.5           # 重要度 0.0-1.0
    access_count: int = 0             # 访问次数
    last_accessed: float = 0.0        # 最后访问时间戳
    created_at: float = 0.0           # 创建时间戳
    decay_factor: float = 1.0         # 衰减系数 0.0-1.0


@dataclass(frozen=True)
class Pattern:
    """行为模式"""
    pattern_type: PatternType         # 模式类型
    description: str                  # 模式描述
    frequency: int = 0                # 出现频率
    confidence: float = 0.5           # 置信度 0.0-1.0
    first_seen: float = 0.0           # 首次发现时间戳
    last_seen: float = 0.0            # 最近出现时间戳


@dataclass(frozen=True)
class RiskIndicator:
    """风险指标"""
    indicator: str                    # 指标名称
    level: str = "低"                 # 风险等级: 低/中/高
    description: str = ""             # 描述
    frequency: int = 0                # 出现次数


@dataclass(frozen=True)
class EmotionalTrajectory:
    """情绪轨迹"""
    states: tuple[tuple[float, EmotionalState], ...] = ()  # (时间戳, 状态) 序列
    dominant_state: EmotionalState = EmotionalState.NEUTRAL
    stability: float = 0.5           # 情绪稳定性 0.0-1.0


@dataclass(frozen=True)
class UserChangeModel:
    """用户变化模型

    汇总用户的长期变化趋势。
    """
    user_id: str
    long_term_themes: tuple[str, ...] = ()            # 长期关注主题
    recurring_patterns: tuple[Pattern, ...] = ()      # 反复出现的模式
    emotional_trajectory: EmotionalTrajectory | None = None
    hexagram_frequency: tuple[tuple[str, float], ...] = ()  # (卦名, 频率)
    risk_indicators: tuple[RiskIndicator, ...] = ()
    total_sessions: int = 0
    last_active: float = 0.0


@dataclass(frozen=True)
class MemoryRecall:
    """记忆召回结果"""
    memories: tuple[UserMemory, ...] = ()
    relevance_scores: tuple[float, ...] = ()
    context_text: str = ""            # 组装后的上下文文本
    total_count: int = 0


@dataclass(frozen=True)
class UserMemoryProfile:
    """用户记忆档案

    完整的用户记忆快照。
    """
    user_id: str
    working_memory: dict | None = None       # 当前会话上下文（浅冻结：引用不可变，内容可变）
    episodic_count: int = 0                  # 情景记忆条数
    semantic_concepts: tuple[str, ...] = ()  # 语义概念列表
    procedural_patterns: tuple[Pattern, ...] = ()  # 行为模式
    change_model: UserChangeModel | None = None
