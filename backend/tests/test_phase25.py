"""
Phase 2.5 测试用例
覆盖: 评估框架、A/B测试、Prompt管理、缓存、频率限制
"""
import pytest
import asyncio
import time

# 评估框架
from ai.evaluation.evaluator import AutoEvaluator, EvalCase, EvalDimension, EvalResult
from ai.evaluation.ab_testing import ABTestManager, Experiment, ExperimentStatus, Variant, ExperimentVariant

# Prompt管理
from ai.prompt_manager.version_control import PromptVersionControl
from ai.prompt_manager.registry import PromptRegistry, PromptCategory, PromptTier

# 缓存
from ai.cache import LRUCache, MultiLevelCache, CacheKeyBuilder, RateLimiter, _MISSING


# ============================================================
# 评估框架测试
# ============================================================

class TestAutoEvaluator:
    """自动化评估器测试"""

    def test_register_case(self):
        """测试注册评估用例"""
        evaluator = AutoEvaluator()
        case = EvalCase(
            case_id="test_001",
            dimension=EvalDimension.SAFETY,
            input_data={"query": "test"},
            forbidden_patterns=("一定会",),
        )
        evaluator.register_case(case)
        assert len(evaluator._eval_cases[EvalDimension.SAFETY]) == 1

    def test_register_cases_batch(self):
        """测试批量注册"""
        evaluator = AutoEvaluator()
        cases = evaluator.get_default_eval_cases()
        evaluator.register_cases(cases)
        assert len(evaluator._eval_cases[EvalDimension.SAFETY]) == 2
        assert len(evaluator._eval_cases[EvalDimension.QUALITY]) == 2

    @pytest.mark.asyncio
    async def test_evaluate_case_safety_pass(self):
        """测试安全评估-通过"""
        evaluator = AutoEvaluator()
        case = EvalCase(
            case_id="safety_pass",
            dimension=EvalDimension.SAFETY,
            input_data={"query": "test"},
            forbidden_patterns=("一定会", "必然"),
        )

        async def pipeline(data: dict) -> str:
            return "这是一个仅供参考的分析结果"

        result = await evaluator.evaluate_case(case, pipeline)
        assert result.passed
        assert result.score > 0.5

    @pytest.mark.asyncio
    async def test_evaluate_case_safety_fail(self):
        """测试安全评估-不通过（包含禁止词）"""
        evaluator = AutoEvaluator()
        case = EvalCase(
            case_id="safety_fail",
            dimension=EvalDimension.SAFETY,
            input_data={"query": "test"},
            forbidden_patterns=("一定会", "必然", "保证", "绝对"),
        )

        async def pipeline(data: dict) -> str:
            return "你一定会成功，必然发财"

        result = await evaluator.evaluate_case(case, pipeline)
        assert result.score < 0.5

    @pytest.mark.asyncio
    async def test_evaluate_case_structure(self):
        """测试结构完整性评估"""
        evaluator = AutoEvaluator()
        case = EvalCase(
            case_id="struct_001",
            dimension=EvalDimension.STRUCTURE,
            input_data={"query": "test"},
            required_sections=("卦象", "变化", "建议"),
        )

        async def pipeline(data: dict) -> str:
            return "卦象分析：乾卦代表刚健。变化趋势：持续上升。建议：保持积极。"

        result = await evaluator.evaluate_case(case, pipeline)
        assert result.score >= 0.6

    @pytest.mark.asyncio
    async def test_run_evaluation(self):
        """测试完整评估流程"""
        evaluator = AutoEvaluator()
        evaluator.register_cases(evaluator.get_default_eval_cases())

        async def pipeline(data: dict) -> str:
            return "卦象分析仅供参考。这是一个安全的解释。"

        report = await evaluator.run_evaluation(pipeline)
        assert report.total_cases > 0
        assert 0 <= report.overall_score <= 1
        assert report.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_evaluate_case_error_handling(self):
        """测试评估异常处理"""
        evaluator = AutoEvaluator()
        case = EvalCase(
            case_id="error_001",
            dimension=EvalDimension.QUALITY,
            input_data={"query": "test"},
        )

        async def pipeline(data: dict) -> str:
            raise RuntimeError("Pipeline error")

        result = await evaluator.evaluate_case(case, pipeline)
        assert result.score == 0.0
        assert "error" in result.details


class TestEvalResult:
    """评估结果测试"""

    def test_passed_threshold(self):
        """测试通过阈值"""
        result = EvalResult(
            case_id="test",
            dimension=EvalDimension.QUALITY,
            score=0.7,
            details={},
        )
        assert result.passed

    def test_failed_threshold(self):
        """测试未通过阈值"""
        result = EvalResult(
            case_id="test",
            dimension=EvalDimension.QUALITY,
            score=0.3,
            details={},
        )
        assert not result.passed


# ============================================================
# A/B 测试测试
# ============================================================

class TestABTestManager:
    """A/B 测试管理器测试"""

    def test_create_experiment(self):
        """测试创建实验"""
        manager = ABTestManager()
        exp = Experiment(
            experiment_id="exp_001",
            name="Prompt v1 vs v2",
            description="Test new prompt",
            variant_a=ExperimentVariant(variant_id=Variant.A, prompt_id="v1"),
            variant_b=ExperimentVariant(variant_id=Variant.B, prompt_id="v2"),
        )
        manager.create_experiment(exp)
        assert manager.get_experiment("exp_001") is not None

    def test_assign_variant_deterministic(self):
        """测试变体分配的确定性"""
        manager = ABTestManager()
        exp = Experiment(
            experiment_id="exp_002",
            name="Test",
            description="Test",
            variant_a=ExperimentVariant(variant_id=Variant.A),
            variant_b=ExperimentVariant(variant_id=Variant.B),
            status=ExperimentStatus.RUNNING,
        )
        exp.status = ExperimentStatus.RUNNING
        manager.create_experiment(exp)
        manager.start_experiment("exp_002")

        # 同一用户应始终获得同一变体
        v1 = manager.assign_variant("exp_002", "user_123")
        v2 = manager.assign_variant("exp_002", "user_123")
        assert v1 == v2

    def test_assign_variant_distribution(self):
        """测试变体分配的分布"""
        manager = ABTestManager()
        exp = Experiment(
            experiment_id="exp_003",
            name="Test",
            description="Test",
            variant_a=ExperimentVariant(variant_id=Variant.A),
            variant_b=ExperimentVariant(variant_id=Variant.B),
            traffic_split=0.5,
            status=ExperimentStatus.RUNNING,
        )
        manager.create_experiment(exp)
        manager.start_experiment("exp_003")

        # 大样本测试分布
        a_count = sum(
            1 for i in range(1000)
            if manager.assign_variant("exp_003", f"user_{i}") == Variant.A
        )
        # 允许 10% 偏差
        assert 400 < a_count < 600

    def test_record_and_report(self):
        """测试记录结果和生成报告"""
        from ai.evaluation.ab_testing import ExperimentResult

        manager = ABTestManager()
        exp = Experiment(
            experiment_id="exp_004",
            name="Test",
            description="Test",
            variant_a=ExperimentVariant(variant_id=Variant.A),
            variant_b=ExperimentVariant(variant_id=Variant.B),
            metrics=["score"],
            status=ExperimentStatus.RUNNING,
        )
        manager.create_experiment(exp)
        manager.start_experiment("exp_004")

        # 记录结果
        for i in range(50):
            manager.record_result(ExperimentResult(
                experiment_id="exp_004",
                variant=Variant.A,
                user_id=f"user_a_{i}",
                metrics={"score": 0.7},
            ))
            manager.record_result(ExperimentResult(
                experiment_id="exp_004",
                variant=Variant.B,
                user_id=f"user_b_{i}",
                metrics={"score": 0.5},
            ))

        report = manager.get_report("exp_004")
        assert report is not None
        assert report.variant_a_count == 50
        assert report.variant_b_count == 50

    def test_list_experiments(self):
        """测试列出实验"""
        manager = ABTestManager()
        exp = Experiment(
            experiment_id="exp_005",
            name="Test",
            description="Test",
            variant_a=ExperimentVariant(variant_id=Variant.A),
            variant_b=ExperimentVariant(variant_id=Variant.B),
        )
        manager.create_experiment(exp)
        assert len(manager.list_experiments()) >= 1


# ============================================================
# Prompt 管理测试
# ============================================================

class TestPromptVersionControl:
    """Prompt 版本控制测试"""

    def test_register_version(self):
        """测试注册版本"""
        vc = PromptVersionControl()
        v = vc.register_version(
            prompt_id="test_prompt",
            version="1.0.0",
            system_prompt="You are a helpful assistant.",
            user_prompt="Hello {name}",
            variables=["name"],
        )
        assert v.version == "1.0.0"
        assert v.content_hash is not None

    def test_get_active_version(self):
        """测试获取活跃版本"""
        vc = PromptVersionControl()
        vc.register_version("p1", "1.0.0", "sys1", "user1")
        vc.register_version("p1", "2.0.0", "sys2", "user2")

        active = vc.get_active_version("p1")
        assert active is not None
        assert active.version == "1.0.0"  # 第一个版本自动设为活跃

    def test_set_active(self):
        """测试设置活跃版本"""
        vc = PromptVersionControl()
        vc.register_version("p1", "1.0.0", "sys1", "user1")
        vc.register_version("p1", "2.0.0", "sys2", "user2")

        assert vc.set_active("p1", "2.0.0")
        active = vc.get_active_version("p1")
        assert active.version == "2.0.0"

    def test_rollback(self):
        """测试版本回滚"""
        vc = PromptVersionControl()
        vc.register_version("p1", "1.0.0", "sys1", "user1")
        vc.register_version("p1", "2.0.0", "sys2", "user2")
        vc.set_active("p1", "2.0.0")

        rolled = vc.rollback("p1", "1.0.0")
        assert rolled is not None
        assert rolled.version == "1.0.0"

        active = vc.get_active_version("p1")
        assert active.version == "1.0.0"

    def test_compare_versions(self):
        """测试版本对比"""
        vc = PromptVersionControl()
        vc.register_version("p1", "1.0.0", "System v1", "User v1")
        vc.register_version("p1", "2.0.0", "System v2", "User v2")

        diff = vc.compare_versions("p1", "1.0.0", "2.0.0")
        assert diff is not None
        assert diff.system_prompt_changes["changed"]
        assert diff.user_prompt_changes["changed"]

    def test_update_eval_score(self):
        """测试更新评估分数"""
        vc = PromptVersionControl()
        vc.register_version("p1", "1.0.0", "sys1", "user1")

        assert vc.update_eval_score("p1", "1.0.0", 0.85)
        v = vc.get_version("p1", "1.0.0")
        assert v.eval_score == 0.85

    def test_export_import_snapshot(self):
        """测试导出导入快照"""
        vc = PromptVersionControl()
        vc.register_version("p1", "1.0.0", "sys1", "user1", metadata={"tags": ["test"]})
        vc.update_eval_score("p1", "1.0.0", 0.9)

        snapshot = vc.export_snapshot("p1")
        assert snapshot["prompt_id"] == "p1"
        assert len(snapshot["versions"]) == 1

        # 导入到新实例
        vc2 = PromptVersionControl()
        vc2.import_snapshot(snapshot)
        v = vc2.get_version("p1", "1.0.0")
        assert v is not None
        assert v.eval_score == 0.9


class TestPromptRegistry:
    """Prompt 注册中心测试"""

    def test_register_and_get(self):
        """测试注册和获取"""
        from ai.prompt_manager.registry import PromptTemplate

        registry = PromptRegistry()
        template = PromptTemplate(
            prompt_id="test_v1",
            category=PromptCategory.INTERPRETATION,
            tier=PromptTier.TIER_2,
            system_prompt="You are an interpreter.",
            user_prompt="Interpret: {query}",
            variables=("query",),
        )
        registry.register(template)

        got = registry.get("test_v1")
        assert got is not None
        assert got.prompt_id == "test_v1"

    def test_get_by_category(self):
        """测试按分类获取"""
        registry = PromptRegistry()
        registry.register_defaults()

        intent_prompts = registry.get_by_category(PromptCategory.INTENT)
        assert len(intent_prompts) >= 1

        interp_prompts = registry.get_by_category(PromptCategory.INTERPRETATION)
        assert len(interp_prompts) >= 1

    def test_get_by_tier(self):
        """测试按层级获取"""
        registry = PromptRegistry()
        registry.register_defaults()

        tier1 = registry.get_by_tier(PromptTier.TIER_1)
        assert len(tier1) >= 1

    def test_render(self):
        """测试模板渲染"""
        from ai.prompt_manager.registry import PromptTemplate

        registry = PromptRegistry()
        registry.register(PromptTemplate(
            prompt_id="render_test",
            category=PromptCategory.INTENT,
            tier=PromptTier.TIER_1,
            system_prompt="System: {version}",
            user_prompt="Query: {query}",
            variables=("version", "query"),
        ))

        sys, user = registry.render("render_test", {"version": "1.0", "query": "test"})
        assert "1.0" in sys
        assert "test" in user

    def test_search(self):
        """测试搜索"""
        registry = PromptRegistry()
        registry.register_defaults()

        results = registry.search("intent")
        assert len(results) >= 1

    def test_register_defaults(self):
        """测试注册默认模板"""
        registry = PromptRegistry()
        registry.register_defaults()

        all_templates = registry.list_all()
        assert len(all_templates) >= 3


# ============================================================
# 缓存测试
# ============================================================

class TestLRUCache:
    """LRU 缓存测试"""

    def test_basic_set_get(self):
        """测试基本读写"""
        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_cache_miss(self):
        """测试缓存未命中"""
        cache = LRUCache()
        assert cache.get("nonexistent") is _MISSING

    def test_ttl_expiry(self):
        """测试 TTL 过期"""
        cache = LRUCache()
        cache.set("key1", "value1", ttl=0.1)
        time.sleep(0.15)
        assert cache.get("key1") is _MISSING

    def test_eviction(self):
        """测试淘汰策略"""
        cache = LRUCache(max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # 应淘汰 "a"

        assert cache.get("a") is _MISSING
        assert cache.get("d") == 4

    def test_lru_order(self):
        """测试 LRU 顺序"""
        cache = LRUCache(max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.get("a")  # 访问 "a"，使其变为最近使用
        cache.set("d", 4)  # 应淘汰 "b"（最久未使用）

        assert cache.get("a") == 1
        assert cache.get("b") is _MISSING

    def test_delete(self):
        """测试删除"""
        cache = LRUCache()
        cache.set("key1", "value1")
        assert cache.delete("key1")
        assert cache.get("key1") is _MISSING

    def test_clear(self):
        """测试清空"""
        cache = LRUCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.size == 0

    def test_stats(self):
        """测试统计"""
        cache = LRUCache()
        cache.set("a", 1)
        cache.get("a")       # hit
        cache.get("b")       # miss
        cache.get("a")       # hit

        assert cache.stats.hits == 2
        assert cache.stats.misses == 1
        assert cache.stats.hit_rate == pytest.approx(2/3)


class TestCacheKeyBuilder:
    """缓存键构建器测试"""

    def test_hexagram_key(self):
        assert CacheKeyBuilder.hexagram("乾") == "hexagram:乾:full"

    def test_interpretation_key(self):
        key1 = CacheKeyBuilder.interpretation("乾", "事业", {})
        key2 = CacheKeyBuilder.interpretation("乾", "感情", {})
        assert key1 != key2

    def test_embedding_key(self):
        key = CacheKeyBuilder.embedding("test text")
        assert key.startswith("cache:embedding:")

    def test_user_keys(self):
        assert CacheKeyBuilder.user_profile("u1") == "user:u1:profile"
        assert CacheKeyBuilder.user_recent("u1") == "user:u1:recent"


class TestRateLimiter:
    """频率限制器测试"""

    def test_within_limit(self):
        """测试限制内"""
        limiter = RateLimiter()
        allowed, remaining = limiter.check("user1", max_count=5, window_seconds=60)
        assert allowed
        assert remaining == 4

    def test_exceed_limit(self):
        """测试超出限制"""
        limiter = RateLimiter()
        for _ in range(5):
            limiter.check("user1", max_count=5, window_seconds=60)

        allowed, remaining = limiter.check("user1", max_count=5, window_seconds=60)
        assert not allowed
        assert remaining == 0

    def test_different_keys(self):
        """测试不同key独立限制"""
        limiter = RateLimiter()
        for _ in range(5):
            limiter.check("user1", max_count=5, window_seconds=60)

        allowed, _ = limiter.check("user2", max_count=5, window_seconds=60)
        assert allowed


# ============================================================
# 多级缓存测试
# ============================================================

class TestMultiLevelCache:
    """多级缓存测试"""

    @pytest.mark.asyncio
    async def test_l1_cache_only(self):
        """测试仅L1缓存（无Redis）"""
        cache = MultiLevelCache(l1_max_size=100)
        await cache.set("key1", {"data": "value1"})
        result = await cache.get("key1")
        assert result == {"data": "value1"}

    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """测试缓存未命中"""
        cache = MultiLevelCache()
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self):
        """测试删除"""
        cache = MultiLevelCache()
        await cache.set("key1", "value1")
        await cache.delete("key1")
        result = await cache.get("key1")
        assert result is None
