"""统一记忆引擎

整合四层记忆架构的统一入口。
负责存储、召回、衰减、压缩、用户变化模型生成。
"""
from __future__ import annotations

import re
import time
import uuid
import logging
import threading
from collections import Counter

from ai.memory.types import (
    MemoryType, EmotionalState, UserMemory, Pattern,
    RiskIndicator, EmotionalTrajectory, UserChangeModel,
    MemoryRecall, UserMemoryProfile,
)
from ai.memory.working import WorkingMemory
from ai.memory.episodic import EpisodicMemory
from ai.memory.semantic import SemanticMemory
from ai.memory.procedural import ProceduralMemory

logger = logging.getLogger(__name__)

# 压缩阈值
_COMPRESS_IMPORTANCE_THRESHOLD = 0.3
_COMPRESS_ACCESS_THRESHOLD = 5

# 中文停用词（与 procedural._extract_keywords 共用）
_STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就",
    "不", "人", "都", "一", "上", "也", "很", "到",
    "说", "要", "去", "你", "会", "着", "没有", "看",
    "好", "自己", "这", "他", "她", "们", "什么",
    "吗", "呢", "吧", "啊", "怎么", "如何", "请问",
    "请", "问", "想", "能", "可以", "帮", "相关",
    "概念", "记忆", "用户", "分析",
}


class MemoryEngine:
    """统一记忆引擎

    全部 classmethod，无实例化。
    整合四层记忆，提供统一的存储、召回、衰减、压缩接口。
    """

    @classmethod
    def store(
        cls,
        user_id: str,
        content: str,
        hexagram_name: str | None = None,
        importance: float = 0.5,
        session_id: str | None = None,
    ) -> UserMemory:
        """存储记忆

        所有记忆写入 L2 情景记忆，同时更新关联层。

        Args:
            user_id: 用户ID
            content: 记忆内容
            hexagram_name: 关联卦名
            importance: 重要度 0.0-1.0
            session_id: 会话ID（用于工作记忆）

        Returns:
            创建的记忆对象
        """
        # L2 情景记忆（所有类型都记录）
        memory = EpisodicMemory.store(
            user_id=user_id,
            content=content,
            hexagram_name=hexagram_name,
            importance=importance,
        )

        # L1 工作记忆（更新当前会话）
        if session_id:
            WorkingMemory.update_session(
                session_id=session_id,
                data={
                    "last_memory": content,
                    "current_hexagram": hexagram_name,
                },
                user_id=user_id,
            )

        # L4 程序记忆（记录行为）
        ProceduralMemory.record_session(
            user_id=user_id,
            hexagram_name=hexagram_name,
            question=content,
        )

        # L3 语义记忆（提取概念）
        keywords = _extract_concepts(content)
        if keywords:
            SemanticMemory.add_concept(
                user_id=user_id,
                concept=keywords[0],
                related_concepts=tuple(keywords[1:4]) if len(keywords) > 1 else (),
            )

        logger.info(
            "记忆存储完成: user=%s, hex=%s",
            user_id, hexagram_name,
        )
        return memory

    @classmethod
    def recall(
        cls,
        user_id: str,
        query: str,
        session_id: str | None = None,
        limit: int = 10,
    ) -> MemoryRecall:
        """混合召回

        从四层记忆中召回相关内容，加权融合排序。

        Args:
            user_id: 用户ID
            query: 查询文本
            session_id: 会话ID
            limit: 返回数量

        Returns:
            记忆召回结果
        """
        all_memories: list[tuple[float, UserMemory]] = []

        # L1 工作记忆
        if session_id:
            session_data = WorkingMemory.get_session(session_id)
            if session_data:
                recent_hex = session_data.get("current_hexagram")
                if recent_hex:
                    wm = UserMemory(
                        memory_id=str(uuid.uuid4()),
                        user_id=user_id,
                        memory_type=MemoryType.WORKING,
                        content=f"当前会话卦象: {recent_hex}",
                        hexagram_name=recent_hex,
                        importance=0.8,
                        access_count=0,
                        last_accessed=time.time(),
                        created_at=time.time(),
                        decay_factor=1.0,
                    )
                    all_memories.append((0.9, wm))

        # L2 情景记忆
        episodic_results = EpisodicMemory.recall(user_id, query, limit=limit)
        for mem in episodic_results:
            score = mem.importance * mem.decay_factor
            all_memories.append((score, mem))

        # L3 语义记忆
        semantic_concepts = SemanticMemory.recall(user_id, query)
        for concept in semantic_concepts[:5]:
            sm = UserMemory(
                memory_id=str(uuid.uuid4()),
                user_id=user_id,
                memory_type=MemoryType.SEMANTIC,
                content=f"相关概念: {concept}",
                importance=0.4,
                access_count=0,
                last_accessed=time.time(),
                created_at=time.time(),
                decay_factor=1.0,
            )
            all_memories.append((0.3, sm))

        # L4 程序记忆
        patterns = ProceduralMemory.get_patterns(user_id)
        for pattern in patterns[:3]:
            pm = UserMemory(
                memory_id=str(uuid.uuid4()),
                user_id=user_id,
                memory_type=MemoryType.PROCEDURAL,
                content=f"行为模式: {pattern.description}",
                importance=pattern.confidence,
                access_count=0,
                last_accessed=time.time(),
                created_at=time.time(),
                decay_factor=1.0,
            )
            all_memories.append((pattern.confidence * 0.5, pm))

        # 按得分排序
        all_memories.sort(key=lambda x: x[0], reverse=True)
        top = all_memories[:limit]

        memories = tuple(m for _, m in top)
        scores = tuple(s for s, _ in top)
        context_text = _assemble_context(memories)

        logger.info(
            "记忆召回完成: user=%s, query=%s, results=%d",
            user_id, query[:20], len(memories),
        )

        return MemoryRecall(
            memories=memories,
            relevance_scores=scores,
            context_text=context_text,
            total_count=len(memories),
        )

    @classmethod
    def get_change_model(cls, user_id: str) -> UserChangeModel:
        """获取用户变化模型

        汇总四层记忆，生成用户长期变化趋势。

        Args:
            user_id: 用户ID

        Returns:
            用户变化模型
        """
        # 高频卦象
        hex_freq = ProceduralMemory.get_frequent_hexagrams(user_id, limit=10)

        # 长期主题
        themes = ProceduralMemory.get_question_themes(user_id)

        # 行为模式
        patterns = ProceduralMemory.get_patterns(user_id)

        # 风险指标
        risk_indicators = _assess_risks(user_id, themes, hex_freq)

        # 情绪轨迹（简化：从最近情景记忆推断）
        emotional = _build_emotional_trajectory(user_id)

        # [M4 修复] 使用公开接口获取统计
        total_sessions, last_active = ProceduralMemory.get_session_stats(user_id)

        return UserChangeModel(
            user_id=user_id,
            long_term_themes=themes,
            recurring_patterns=patterns,
            emotional_trajectory=emotional,
            hexagram_frequency=hex_freq,
            risk_indicators=risk_indicators,
            total_sessions=total_sessions,
            last_active=last_active,
        )

    @classmethod
    def get_user_profile(cls, user_id: str) -> UserMemoryProfile:
        """获取用户记忆档案

        Args:
            user_id: 用户ID

        Returns:
            用户记忆档案
        """
        episodic_count = EpisodicMemory.count(user_id)
        semantic_concepts = SemanticMemory.get_user_concepts(user_id)
        patterns = ProceduralMemory.get_patterns(user_id)
        change_model = cls.get_change_model(user_id)

        return UserMemoryProfile(
            user_id=user_id,
            working_memory=None,
            episodic_count=episodic_count,
            semantic_concepts=semantic_concepts,
            procedural_patterns=patterns,
            change_model=change_model,
        )

    @classmethod
    def compress_memories(cls, user_id: str) -> int:
        """记忆压缩

        合并低重要度、高频访问的记忆为主题记忆。
        [H1] 使用 get_compressible 在锁内读取。
        [M1] 先存后删，避免崩溃时数据丢失。

        Args:
            user_id: 用户ID

        Returns:
            压缩的记忆数
        """
        # [H1] 在锁内获取可压缩记忆
        to_compress = EpisodicMemory.get_compressible(
            user_id,
            _COMPRESS_IMPORTANCE_THRESHOLD,
            _COMPRESS_ACCESS_THRESHOLD,
        )

        if len(to_compress) < 3:
            return 0

        # 提取共同主题
        all_content = " ".join(m.content for m in to_compress)
        concepts = _extract_concepts(all_content)
        if not concepts:
            return 0

        top_concepts = concepts[:5]
        summary = f"综合主题: {', '.join(top_concepts)}"

        # [M1] 先存后删，避免崩溃时数据丢失
        EpisodicMemory.store(
            user_id=user_id,
            content=summary,
            importance=0.6,
        )

        # 然后再删除原始记忆
        compress_ids = {m.memory_id for m in to_compress}
        EpisodicMemory.remove_by_ids(compress_ids)

        # 更新语义记忆
        SemanticMemory.add_concept(
            user_id=user_id,
            concept=top_concepts[0],
            related_concepts=tuple(top_concepts[1:]),
        )

        logger.info(
            "记忆压缩完成: user=%s, compressed=%d, theme=%s",
            user_id, len(to_compress), top_concepts[0],
        )
        return len(to_compress)

    @classmethod
    def decay_all(cls, user_id: str) -> dict[str, int]:
        """全量衰减

        对所有记忆层执行时间衰减。

        Args:
            user_id: 用户ID

        Returns:
            各层衰减的记忆数
        """
        return {
            "episodic": EpisodicMemory.apply_decay_all(user_id),
            "semantic": SemanticMemory.apply_decay_all(user_id),
        }

    @classmethod
    def reset(cls) -> None:
        """重置所有数据（测试用）"""
        WorkingMemory.reset()
        EpisodicMemory.reset()
        SemanticMemory.reset()
        ProceduralMemory.reset()


def _assemble_context(memories: tuple[UserMemory, ...]) -> str:
    """将召回的记忆组装为上下文文本

    Args:
        memories: 记忆列表

    Returns:
        格式化的上下文文本
    """
    if not memories:
        return ""

    sections: list[str] = []
    sections.append("## 用户记忆上下文")

    # 按类型分组
    by_type: dict[str, list[str]] = {}
    for mem in memories:
        type_name = mem.memory_type.value
        if type_name not in by_type:
            by_type[type_name] = []
        by_type[type_name].append(mem.content)

    for type_name, contents in by_type.items():
        sections.append(f"### {type_name}记忆")
        for content in contents[:5]:
            sections.append(f"- {content}")

    return "\n".join(sections)


def _assess_risks(
    user_id: str,
    themes: tuple[str, ...],
    hex_freq: tuple[tuple[str, float], ...],
) -> tuple[RiskIndicator, ...]:
    """评估风险指标"""
    risks: list[RiskIndicator] = []

    anxiety_keywords = {"焦虑", "担心", "害怕", "恐惧", "不安", "压力", "烦恼"}
    for theme in themes:
        if theme in anxiety_keywords:
            risks.append(RiskIndicator(
                indicator="焦虑倾向",
                level="中",
                description=f"用户频繁关注焦虑相关主题: {theme}",
                frequency=1,
            ))
            break

    for hex_name, freq in hex_freq:
        if freq > 0.3:
            risks.append(RiskIndicator(
                indicator="过度依赖",
                level="中",
                description=f"用户过度依赖 {hex_name} 卦（频率 {freq:.0%}）",
                frequency=int(freq * 100),
            ))

    return tuple(risks)


def _build_emotional_trajectory(user_id: str) -> EmotionalTrajectory | None:
    """构建情绪轨迹"""
    history = EpisodicMemory.get_user_history(user_id, limit=20)
    if not history:
        return None

    states: list[tuple[float, EmotionalState]] = []
    for mem in history:
        state = _infer_emotion(mem.content)
        states.append((mem.created_at, state))

    if not states:
        return None

    state_counts = Counter(s for _, s in states)
    dominant = state_counts.most_common(1)[0][0]
    stability = state_counts.most_common(1)[0][1] / len(states)

    return EmotionalTrajectory(
        states=tuple(states),
        dominant_state=dominant,
        stability=stability,
    )


def _extract_concepts(text: str) -> list[str]:
    """从文本中提取概念关键词"""
    words = re.split(r'[\s,，。、；：！？\?\.!;:\-\(\)\[\]]+', text)
    return [w for w in words if len(w) >= 2 and w not in _STOP_WORDS]


def _infer_emotion(content: str) -> EmotionalState:
    """从文本推断情绪状态

    [M2 修复] 覆盖所有 EmotionalState 枚举值。
    """
    positive_words = {"顺利", "好", "吉", "利", "成功", "满意", "高兴", "开心"}
    anxiety_words = {"焦虑", "担心", "害怕", "恐惧", "不安", "压力", "烦恼"}
    hopeful_words = {"希望", "期待", "想要", "追求", "目标", "梦想"}
    worried_words = {"担忧", "忧虑", "紧张", "忐忑"}
    confused_words = {"困惑", "迷茫", "不知道", "不确定", "犹豫"}

    content_lower = content.lower()

    for w in positive_words:
        if w in content_lower:
            return EmotionalState.POSITIVE
    for w in anxiety_words:
        if w in content_lower:
            return EmotionalState.ANXIOUS
    for w in worried_words:
        if w in content_lower:
            return EmotionalState.WORRIED
    for w in hopeful_words:
        if w in content_lower:
            return EmotionalState.HOPEFUL
    for w in confused_words:
        if w in content_lower:
            return EmotionalState.CONFUSED

    return EmotionalState.NEUTRAL
