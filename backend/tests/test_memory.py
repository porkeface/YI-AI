"""记忆系统测试

覆盖四层记忆架构 + 统一引擎 + Agent工作流集成。
"""
import time
import pytest


# ============================================================================
# 辅助函数
# ============================================================================

def _reset_all():
    """重置所有记忆层数据"""
    from ai.memory.engine import MemoryEngine
    MemoryEngine.reset()


# ============================================================================
# L1 工作记忆测试
# ============================================================================

class TestWorkingMemory:
    """工作记忆测试"""

    def setup_method(self):
        from ai.memory.working import WorkingMemory
        WorkingMemory.reset()

    def test_get_session_empty(self):
        """空会话返回 None"""
        from ai.memory.working import WorkingMemory
        result = WorkingMemory.get_session("nonexistent")
        assert result is None

    def test_update_and_get_session(self):
        """更新后可获取"""
        from ai.memory.working import WorkingMemory
        WorkingMemory.update_session("s1", {"key": "value"}, user_id="u1")
        result = WorkingMemory.get_session("s1")
        assert result is not None
        assert result["key"] == "value"

    def test_update_session_merges(self):
        """更新会话时合并数据"""
        from ai.memory.working import WorkingMemory
        WorkingMemory.update_session("s1", {"a": 1})
        WorkingMemory.update_session("s1", {"b": 2})
        result = WorkingMemory.get_session("s1")
        assert result["a"] == 1
        assert result["b"] == 2

    def test_clear_session(self):
        """清除会话"""
        from ai.memory.working import WorkingMemory
        WorkingMemory.update_session("s1", {"key": "value"})
        assert WorkingMemory.clear_session("s1") is True
        assert WorkingMemory.get_session("s1") is None

    def test_clear_nonexistent_session(self):
        """清除不存在的会话返回 False"""
        from ai.memory.working import WorkingMemory
        assert WorkingMemory.clear_session("nonexistent") is False

    def test_session_expiry(self):
        """会话过期后不可获取"""
        from ai.memory.working import WorkingMemory
        WorkingMemory.update_session("s1", {"key": "value"}, ttl=0)
        time.sleep(0.01)
        result = WorkingMemory.get_session("s1")
        assert result is None

    def test_get_recent_hexagrams(self):
        """获取最近卦象"""
        from ai.memory.working import WorkingMemory
        WorkingMemory.update_session("s1", {"current_hexagram": "乾"}, user_id="u1")
        WorkingMemory.update_session("s2", {"current_hexagram": "坤"}, user_id="u1")
        hexagrams = WorkingMemory.get_recent_hexagrams("u1")
        assert "乾" in hexagrams
        assert "坤" in hexagrams

    def test_get_recent_hexagrams_dedup(self):
        """最近卦象去重"""
        from ai.memory.working import WorkingMemory
        WorkingMemory.update_session("s1", {"current_hexagram": "乾"}, user_id="u1")
        WorkingMemory.update_session("s2", {"current_hexagram": "乾"}, user_id="u1")
        hexagrams = WorkingMemory.get_recent_hexagrams("u1")
        assert hexagrams.count("乾") == 1

    def test_cleanup_expired(self):
        """清理过期会话"""
        from ai.memory.working import WorkingMemory
        WorkingMemory.update_session("s1", {"key": "v1"}, ttl=0)
        WorkingMemory.update_session("s2", {"key": "v2"}, ttl=3600)
        time.sleep(0.01)
        count = WorkingMemory.cleanup_expired()
        assert count == 1
        assert WorkingMemory.get_session("s2") is not None


# ============================================================================
# L2 情景记忆测试
# ============================================================================

class TestEpisodicMemory:
    """情景记忆测试"""

    def setup_method(self):
        from ai.memory.episodic import EpisodicMemory
        EpisodicMemory.reset()

    def test_store_and_recall(self):
        """存储后可召回"""
        from ai.memory.episodic import EpisodicMemory
        EpisodicMemory.store("u1", "占卜事业问题", hexagram_name="乾")
        results = EpisodicMemory.recall("u1", "事业")
        assert len(results) > 0
        assert results[0].hexagram_name == "乾"

    def test_recall_by_user(self):
        """只召回指定用户的记忆"""
        from ai.memory.episodic import EpisodicMemory
        EpisodicMemory.store("u1", "用户1的记忆")
        EpisodicMemory.store("u2", "用户2的记忆")
        results = EpisodicMemory.recall("u1", "记忆")
        assert all(m.user_id == "u1" for m in results)

    def test_recall_empty(self):
        """无匹配返回空"""
        from ai.memory.episodic import EpisodicMemory
        EpisodicMemory.store("u1", "事业问题")
        results = EpisodicMemory.recall("u1", "爱情")
        assert len(results) == 0

    def test_recall_limit(self):
        """召回数量限制"""
        from ai.memory.episodic import EpisodicMemory
        for i in range(20):
            EpisodicMemory.store("u1", f"记忆{i} 关键词")
        results = EpisodicMemory.recall("u1", "关键词", limit=5)
        assert len(results) <= 5

    def test_get_user_history(self):
        """获取用户历史"""
        from ai.memory.episodic import EpisodicMemory
        for i in range(5):
            EpisodicMemory.store("u1", f"历史记录{i}")
        history = EpisodicMemory.get_user_history("u1", limit=3)
        assert len(history) == 3

    def test_get_by_hexagram(self):
        """按卦名获取记忆"""
        from ai.memory.episodic import EpisodicMemory
        EpisodicMemory.store("u1", "乾卦记忆", hexagram_name="乾")
        EpisodicMemory.store("u1", "坤卦记忆", hexagram_name="坤")
        results = EpisodicMemory.get_by_hexagram("u1", "乾")
        assert len(results) == 1
        assert results[0].hexagram_name == "乾"

    def test_count(self):
        """统计记忆条数"""
        from ai.memory.episodic import EpisodicMemory
        EpisodicMemory.store("u1", "记忆1")
        EpisodicMemory.store("u1", "记忆2")
        EpisodicMemory.store("u2", "记忆3")
        assert EpisodicMemory.count("u1") == 2
        assert EpisodicMemory.count() == 3

    def test_decay(self):
        """时间衰减"""
        from ai.memory.episodic import EpisodicMemory
        from ai.memory.types import UserMemory
        mem = EpisodicMemory.store("u1", "测试记忆")
        # 模拟 60 天前的访问时间
        old_mem = UserMemory(
            memory_id=mem.memory_id,
            user_id=mem.user_id,
            memory_type=mem.memory_type,
            content=mem.content,
            hexagram_name=mem.hexagram_name,
            importance=mem.importance,
            access_count=mem.access_count,
            last_accessed=time.time() - 86400 * 60,
            created_at=mem.created_at,
            decay_factor=1.0,
        )
        # [M3] 使用公开的测试辅助方法替换
        from ai.memory.episodic import EpisodicMemory as EM
        EM.replace_for_test([old_mem])

        decayed = EM.apply_decay_all("u1")
        assert decayed == 1
        # 衰减后系数应小于 1
        assert EM._store[0].decay_factor < 1.0


# ============================================================================
# L3 语义记忆测试
# ============================================================================

class TestSemanticMemory:
    """语义记忆测试"""

    def setup_method(self):
        from ai.memory.semantic import SemanticMemory
        SemanticMemory.reset()

    def test_add_and_get_related(self):
        """添加概念后可获取关联"""
        from ai.memory.semantic import SemanticMemory
        SemanticMemory.add_concept("u1", "事业", ("工作", "升职"))
        related = SemanticMemory.get_related("u1", "事业")
        assert "工作" in related
        assert "升职" in related

    def test_bidirectional_relation(self):
        """关联是双向的"""
        from ai.memory.semantic import SemanticMemory
        SemanticMemory.add_concept("u1", "事业", ("工作",))
        related = SemanticMemory.get_related("u1", "工作")
        assert "事业" in related

    def test_get_user_concepts(self):
        """获取用户概念列表"""
        from ai.memory.semantic import SemanticMemory
        SemanticMemory.add_concept("u1", "事业")
        SemanticMemory.add_concept("u1", "爱情")
        concepts = SemanticMemory.get_user_concepts("u1")
        assert "事业" in concepts
        assert "爱情" in concepts

    def test_recall_by_query(self):
        """基于查询召回概念"""
        from ai.memory.semantic import SemanticMemory
        SemanticMemory.add_concept("u1", "事业发展", ("升职", "加薪"))
        SemanticMemory.add_concept("u1", "感情问题", ("恋爱", "分手"))
        results = SemanticMemory.recall("u1", "我想升职")
        assert "事业发展" in results

    def test_count(self):
        """统计概念数量"""
        from ai.memory.semantic import SemanticMemory
        SemanticMemory.add_concept("u1", "概念A")
        SemanticMemory.add_concept("u1", "概念B")
        assert SemanticMemory.count("u1") == 2

    def test_decay(self):
        """语义记忆衰减"""
        from ai.memory.semantic import SemanticMemory
        SemanticMemory.add_concept("u1", "旧概念")
        # 模拟长时间未访问
        graph = SemanticMemory._graphs["u1"]
        for node in graph.values():
            node["last_accessed"] = time.time() - 86400 * 200
            node["access_count"] = 1
        count = SemanticMemory.apply_decay_all("u1")
        assert count > 0


# ============================================================================
# L4 程序记忆测试
# ============================================================================

class TestProceduralMemory:
    """程序记忆测试"""

    def setup_method(self):
        from ai.memory.procedural import ProceduralMemory
        ProceduralMemory.reset()

    def test_record_session(self):
        """记录会话"""
        from ai.memory.procedural import ProceduralMemory
        ProceduralMemory.record_session("u1", hexagram_name="乾", question="事业问题")
        freq = ProceduralMemory.get_frequent_hexagrams("u1")
        assert len(freq) > 0
        assert freq[0][0] == "乾"

    def test_frequent_hexagrams(self):
        """高频卦象统计"""
        from ai.memory.procedural import ProceduralMemory
        for _ in range(5):
            ProceduralMemory.record_session("u1", hexagram_name="乾")
        ProceduralMemory.record_session("u1", hexagram_name="坤")
        freq = ProceduralMemory.get_frequent_hexagrams("u1")
        assert freq[0][0] == "乾"
        assert freq[0][1] > freq[1][1]

    def test_question_themes(self):
        """问题主题提取"""
        from ai.memory.procedural import ProceduralMemory
        ProceduralMemory.record_session("u1", question="事业发展如何")
        ProceduralMemory.record_session("u1", question="工作前景怎样")
        themes = ProceduralMemory.get_question_themes("u1")
        assert len(themes) > 0

    def test_patterns_high_freq_hexagram(self):
        """高频卦象模式识别"""
        from ai.memory.procedural import ProceduralMemory
        for _ in range(10):
            ProceduralMemory.record_session("u1", hexagram_name="乾")
        ProceduralMemory.record_session("u1", hexagram_name="坤")
        patterns = ProceduralMemory.get_patterns("u1")
        hex_patterns = [p for p in patterns if p.pattern_type.value == "高频卦象"]
        assert len(hex_patterns) > 0

    def test_patterns_recurring_theme(self):
        """反复主题模式识别"""
        from ai.memory.procedural import ProceduralMemory
        for word in ["事业", "工作", "升职", "加薪", "跳槽"]:
            ProceduralMemory.record_session("u1", question=f"关于{word}的问题")
        patterns = ProceduralMemory.get_patterns("u1")
        theme_patterns = [p for p in patterns if p.pattern_type.value == "反复主题"]
        assert len(theme_patterns) > 0

    def test_profile_summary(self):
        """档案摘要"""
        from ai.memory.procedural import ProceduralMemory
        ProceduralMemory.record_session("u1", hexagram_name="乾", question="事业问题")
        summary = ProceduralMemory.get_profile_summary("u1")
        assert summary["total_sessions"] == 1
        assert len(summary["frequent_hexagrams"]) > 0


# ============================================================================
# 统一记忆引擎测试
# ============================================================================

class TestMemoryEngine:
    """统一记忆引擎测试"""

    def setup_method(self):
        from ai.memory.engine import MemoryEngine
        MemoryEngine.reset()

    def test_store_creates_memory(self):
        """存储创建记忆"""
        from ai.memory.engine import MemoryEngine
        mem = MemoryEngine.store("u1", "测试内容", hexagram_name="乾")
        assert mem.user_id == "u1"
        assert mem.hexagram_name == "乾"

    def test_store_updates_all_layers(self):
        """存储同时更新多层"""
        from ai.memory.engine import MemoryEngine
        from ai.memory.episodic import EpisodicMemory
        from ai.memory.procedural import ProceduralMemory
        MemoryEngine.store(
            "u1", "事业发展问题",
            hexagram_name="乾",
            session_id="s1",
        )
        assert EpisodicMemory.count("u1") > 0
        assert len(ProceduralMemory.get_frequent_hexagrams("u1")) > 0

    def test_recall_returns_results(self):
        """召回返回结果"""
        from ai.memory.engine import MemoryEngine
        MemoryEngine.store("u1", "事业发展的建议", hexagram_name="乾")
        result = MemoryEngine.recall("u1", "事业")
        assert result.total_count > 0
        assert len(result.context_text) > 0

    def test_recall_empty_user(self):
        """无记忆用户召回返回空"""
        from ai.memory.engine import MemoryEngine
        result = MemoryEngine.recall("new_user", "测试")
        assert result.total_count == 0

    def test_recall_with_session(self):
        """带会话的召回"""
        from ai.memory.engine import MemoryEngine
        from ai.memory.working import WorkingMemory
        WorkingMemory.update_session("s1", {"current_hexagram": "乾"}, user_id="u1")
        result = MemoryEngine.recall("u1", "测试", session_id="s1")
        # 工作记忆应被召回
        assert any(m.content.startswith("当前会话") for m in result.memories)

    def test_get_change_model(self):
        """获取用户变化模型"""
        from ai.memory.engine import MemoryEngine
        for i in range(5):
            MemoryEngine.store("u1", f"记忆{i}", hexagram_name="乾")
        model = MemoryEngine.get_change_model("u1")
        assert model.user_id == "u1"
        assert model.total_sessions > 0

    def test_compress_memories(self):
        """记忆压缩 — 低重要度+高访问的记忆被合并"""
        from ai.memory.engine import MemoryEngine
        from ai.memory.episodic import EpisodicMemory
        # 创建 5 条低重要度、高访问的记忆（满足压缩条件）
        for i in range(5):
            mem = EpisodicMemory.store("u1", f"事业发展的建议{i} 占卜结果", importance=0.2)
            # 模拟高访问次数
            for _ in range(6):
                EpisodicMemory._update_access(mem)

        compressed = MemoryEngine.compress_memories("u1")
        assert compressed >= 3  # 至少 3 条被压缩

    def test_decay_all(self):
        """全量衰减"""
        from ai.memory.engine import MemoryEngine
        MemoryEngine.store("u1", "测试记忆")
        result = MemoryEngine.decay_all("u1")
        assert "episodic" in result
        assert "semantic" in result

    def test_get_user_profile(self):
        """获取用户档案"""
        from ai.memory.engine import MemoryEngine
        MemoryEngine.store("u1", "事业发展", hexagram_name="乾")
        profile = MemoryEngine.get_user_profile("u1")
        assert profile.user_id == "u1"
        assert profile.episodic_count > 0

    def test_context_assembly(self):
        """上下文组装"""
        from ai.memory.engine import MemoryEngine
        MemoryEngine.store("u1", "事业问题", hexagram_name="乾")
        MemoryEngine.store("u1", "感情困惑", hexagram_name="坤")
        result = MemoryEngine.recall("u1", "事业 感情")
        assert "用户记忆上下文" in result.context_text


# ============================================================================
# Agent 工作流集成测试
# ============================================================================

class TestMemoryIntegration:
    """Agent 工作流集成测试"""

    def setup_method(self):
        from ai.memory.engine import MemoryEngine
        MemoryEngine.reset()

    def test_workflow_has_memory_nodes(self):
        """工作流包含记忆节点"""
        from ai.agent.workflow import AgentWorkflow
        from ai.agent.state import AgentConfig
        config = AgentConfig(enable_memory=True)
        workflow = AgentWorkflow.build_default(config)
        assert "retrieve_memory" in workflow._nodes
        assert "store_memory" in workflow._nodes

    def test_workflow_memory_disabled(self):
        """[H3] 记忆禁用时工作流不含记忆节点"""
        from ai.agent.workflow import AgentWorkflow
        from ai.agent.state import AgentConfig
        config = AgentConfig(enable_memory=False)
        workflow = AgentWorkflow.build_default(config)
        # 记忆节点不应存在
        assert "retrieve_memory" not in workflow._nodes
        assert "store_memory" not in workflow._nodes

    @pytest.mark.asyncio
    async def test_retrieve_memory_node(self):
        """记忆召回节点执行"""
        from ai.agent.workflow import _retrieve_memory
        # 预存记忆
        from ai.memory.engine import MemoryEngine
        MemoryEngine.store("u1", "事业发展的建议", hexagram_name="乾")

        state = {
            "user_id": "u1",
            "user_query": "事业如何",
            "session_id": "s1",
        }
        result = _retrieve_memory(state)
        assert result["user_memory"] is not None
        assert result["user_memory"]["memory_count"] > 0

    @pytest.mark.asyncio
    async def test_store_memory_node(self):
        """记忆存储节点执行"""
        from ai.agent.workflow import _store_memory
        from ai.memory.episodic import EpisodicMemory

        state = {
            "user_id": "u1",
            "user_query": "事业问题",
            "final_response": "事业发展顺利",
            "hexagram_data": {"name": "乾"},
            "session_id": "s1",
            "risk_flags": [],
        }
        _store_memory(state)
        assert EpisodicMemory.count("u1") > 0

    @pytest.mark.asyncio
    async def test_store_memory_skips_empty(self):
        """空内容不存储"""
        from ai.agent.workflow import _store_memory
        from ai.memory.episodic import EpisodicMemory

        state = {
            "user_id": "u1",
            "user_query": "",
            "final_response": "",
        }
        _store_memory(state)
        assert EpisodicMemory.count("u1") == 0


# ============================================================================
# 工具函数测试 (L8)
# ============================================================================

class TestUtilityFunctions:
    """工具函数测试"""

    def test_keyword_match_basic(self):
        """关键词匹配基本功能"""
        from ai.memory.episodic import _keyword_match
        score = _keyword_match("事业 发展", "关于事业发展的建议")
        assert score > 0

    def test_keyword_match_no_match(self):
        """无匹配返回 0"""
        from ai.memory.episodic import _keyword_match
        score = _keyword_match("爱情", "关于事业发展的建议")
        assert score == 0.0

    def test_keyword_match_empty_query(self):
        """空查询返回 0"""
        from ai.memory.episodic import _keyword_match
        score = _keyword_match("", "关于事业发展的建议")
        assert score == 0.0

    def test_keyword_match_empty_content(self):
        """空内容返回 0"""
        from ai.memory.episodic import _keyword_match
        score = _keyword_match("事业", "")
        assert score == 0.0

    def test_infer_emotion_positive(self):
        """积极情绪推断"""
        from ai.memory.engine import _infer_emotion
        from ai.memory.types import EmotionalState
        assert _infer_emotion("事业顺利，非常满意") == EmotionalState.POSITIVE

    def test_infer_emotion_anxious(self):
        """焦虑情绪推断"""
        from ai.memory.engine import _infer_emotion
        from ai.memory.types import EmotionalState
        assert _infer_emotion("非常焦虑，压力很大") == EmotionalState.ANXIOUS

    def test_infer_emotion_worried(self):
        """担忧情绪推断"""
        from ai.memory.engine import _infer_emotion
        from ai.memory.types import EmotionalState
        assert _infer_emotion("非常担忧未来") == EmotionalState.WORRIED

    def test_infer_emotion_hopeful(self):
        """期待情绪推断"""
        from ai.memory.engine import _infer_emotion
        from ai.memory.types import EmotionalState
        assert _infer_emotion("期待新的目标") == EmotionalState.HOPEFUL

    def test_infer_emotion_confused(self):
        """困惑情绪推断"""
        from ai.memory.engine import _infer_emotion
        from ai.memory.types import EmotionalState
        assert _infer_emotion("非常困惑，犹豫不决") == EmotionalState.CONFUSED

    def test_infer_emotion_neutral(self):
        """中性情绪推断"""
        from ai.memory.engine import _infer_emotion
        from ai.memory.types import EmotionalState
        assert _infer_emotion("今天天气不错") == EmotionalState.NEUTRAL

    def test_assemble_context_with_memories(self):
        """上下文组装有记忆"""
        from ai.memory.engine import _assemble_context
        from ai.memory.types import UserMemory, MemoryType
        import uuid, time
        mem = UserMemory(
            memory_id=str(uuid.uuid4()),
            user_id="u1",
            memory_type=MemoryType.EPISODIC,
            content="测试内容",
            importance=0.5,
            access_count=0,
            last_accessed=time.time(),
            created_at=time.time(),
            decay_factor=1.0,
        )
        result = _assemble_context((mem,))
        assert "用户记忆上下文" in result
        assert "测试内容" in result

    def test_assemble_context_empty(self):
        """空记忆上下文"""
        from ai.memory.engine import _assemble_context
        assert _assemble_context(()) == ""

    def test_assess_risks_anxiety(self):
        """焦虑风险评估"""
        from ai.memory.engine import _assess_risks
        risks = _assess_risks("u1", ("焦虑", "压力"), ())
        assert len(risks) > 0
        assert risks[0].indicator == "焦虑倾向"

    def test_assess_risks_overuse(self):
        """过度依赖风险评估"""
        from ai.memory.engine import _assess_risks
        risks = _assess_risks("u1", (), (("乾", 0.5),))
        assert len(risks) > 0
        assert risks[0].indicator == "过度依赖"

    def test_assess_risks_none(self):
        """无风险"""
        from ai.memory.engine import _assess_risks
        risks = _assess_risks("u1", ("事业",), (("乾", 0.1),))
        assert len(risks) == 0

    def test_safe_truncate_short(self):
        """短文本不截断"""
        from ai.agent.workflow import _safe_truncate
        assert _safe_truncate("短文本", 100) == "短文本"

    def test_safe_truncate_at_punctuation(self):
        """在标点处截断"""
        from ai.agent.workflow import _safe_truncate
        result = _safe_truncate("这是第一句。这是第二句。这是第三句。", 15)
        assert result.endswith("。")
        assert len(result) <= 15

    def test_safe_truncate_no_punctuation(self):
        """无标点时硬截断"""
        from ai.agent.workflow import _safe_truncate
        result = _safe_truncate("这是一段很长的文本没有标点符号", 10)
        assert len(result) == 10
