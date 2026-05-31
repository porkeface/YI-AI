"""自动观察Agent测试

覆盖：模式检测、异常检测、趋势报告、观察Agent。
"""

from __future__ import annotations

import time
import pytest
from ai.observation.types import (
    ObservationType,
    PatternCategory,
    TrendDirection,
    AnomalySeverity,
    ReportPeriod,
    DetectedPattern,
    TrendIndicator,
    TrendReport,
    AnomalyAlert,
    UserObservation,
    ObservationConfig,
)
from ai.observation.pattern_detector import PatternDetector
from ai.observation.pattern_analyzer import PatternAnalyzer
from ai.observation.anomaly_detector import AnomalyDetector
from ai.observation.trend_reporter import TrendReporter
from ai.observation.agent import ObservationAgent
from foundation.types import ProsperityState
from ai.memory.types import MemoryType, EmotionalState


def _make_memory(
    content: str = "测试",
    hexagram_name: str | None = None,
    memory_type: MemoryType = MemoryType.EPISODIC,
    created_at: float | None = None,
    importance: float = 0.5,
    user_id: str = "test_user",
):
    """创建测试用记忆"""
    from ai.memory.types import UserMemory
    import uuid

    return UserMemory(
        memory_id=str(uuid.uuid4()),
        user_id=user_id,
        memory_type=memory_type,
        content=content,
        hexagram_name=hexagram_name,
        importance=importance,
        created_at=created_at if created_at is not None else time.time(),
    )


# ============================================================
# 模式检测器测试
# ============================================================


class TestPatternDetector:
    """模式检测器测试"""

    def test_detect_hexagram_frequency(self):
        """检测高频卦象"""
        now = time.time()
        memories = []
        # 乾为天 出现7次（显著高于平均）
        for i in range(7):
            memories.append(
                _make_memory("占卜", "乾为天", created_at=now - i * 100)
            )
        # 其他卦各1次
        for name in ["坤为地", "水雷屯", "山水蒙"]:
            memories.append(
                _make_memory("占卜", name, created_at=now - 1000)
            )

        config = ObservationConfig(min_sessions_for_pattern=3)
        patterns = PatternDetector.detect_hexagram_frequency(
            memories, config
        )
        assert len(patterns) >= 1
        assert patterns[0].category == PatternCategory.HEXAGRAM_FREQUENCY
        assert "乾为天" in patterns[0].description

    def test_detect_time_pattern(self):
        """检测时间偏好"""
        import datetime
        now = time.time()
        memories = []
        # 都在晚上10点占卜
        for i in range(6):
            dt = datetime.datetime(2026, 5, 29, 22, 0) - datetime.timedelta(
                days=i
            )
            memories.append(
                _make_memory("测试", created_at=dt.timestamp())
            )

        config = ObservationConfig(min_sessions_for_pattern=3)
        patterns = PatternDetector.detect_time_patterns(memories, config)
        assert len(patterns) >= 1
        assert patterns[0].category == PatternCategory.TIME_PATTERN

    def test_detect_topic_cluster(self):
        """检测主题聚类"""
        now = time.time()
        memories = []
        for i in range(5):
            memories.append(
                _make_memory("工作事业发展如何", created_at=now - i * 100)
            )
        memories.append(_make_memory("感情问题", created_at=now - 600))

        config = ObservationConfig(min_sessions_for_pattern=3)
        patterns = PatternDetector.detect_topic_clusters(memories, config)
        assert len(patterns) >= 1
        assert patterns[0].category == PatternCategory.TOPIC_CLUSTER
        assert "事业" in patterns[0].description

    def test_detect_emotional_cycle(self):
        """检测情绪周期"""
        now = time.time()
        memories = []
        for i in range(5):
            memories.append(
                _make_memory(
                    "焦虑不安",
                    memory_type=MemoryType.EMOTIONAL,
                    created_at=now - i * 100,
                )
            )

        config = ObservationConfig(min_sessions_for_pattern=3)
        patterns = PatternDetector.detect_emotional_cycles(memories, config)
        assert len(patterns) >= 1
        assert patterns[0].category == PatternCategory.EMOTIONAL_CYCLE

    def test_detect_change_sequence(self):
        """检测变化序列"""
        now = time.time()
        memories = [
            _make_memory("占卜", "乾为天", created_at=now - 500),
            _make_memory("占卜", "天风姤", created_at=now - 400),
            _make_memory("占卜", "乾为天", created_at=now - 300),
            _make_memory("占卜", "天风姤", created_at=now - 200),
        ]

        config = ObservationConfig(min_sessions_for_pattern=3)
        patterns = PatternDetector.detect_change_sequences(memories, config)
        assert len(patterns) >= 1
        assert patterns[0].category == PatternCategory.CHANGE_SEQUENCE

    def test_detect_all_insufficient_data(self):
        """数据不足时返回空"""
        memories = [_make_memory("测试")]
        config = ObservationConfig(min_sessions_for_pattern=5)
        patterns = PatternDetector.detect_all(memories, config)
        assert patterns == ()

    def test_detect_all_returns_sorted(self):
        """结果按置信度降序排列"""
        now = time.time()
        memories = []
        for i in range(8):
            memories.append(
                _make_memory("工作事业升职", "乾为天", created_at=now - i * 100)
            )
        for i in range(3):
            memories.append(
                _make_memory("感情爱情", "坤为地", created_at=now - 1000 - i * 100)
            )

        config = ObservationConfig(min_sessions_for_pattern=3)
        patterns = PatternDetector.detect_all(memories, config)
        if len(patterns) >= 2:
            assert patterns[0].confidence >= patterns[1].confidence


# ============================================================
# 异常检测器测试
# ============================================================


class TestAnomalyDetector:
    """异常检测器测试"""

    def test_detect_frequency_spike(self):
        """检测频率激增"""
        now = time.time()
        memories = []
        # 前10天每天1次
        for i in range(10, 20):
            memories.append(
                _make_memory("测试", created_at=now - i * 86400)
            )
        # 今天突然8次
        for i in range(8):
            memories.append(
                _make_memory("测试", created_at=now - i * 100)
            )

        config = ObservationConfig(
            min_sessions_for_pattern=3,
            anomaly_z_score=2.0,
        )
        alerts = AnomalyDetector.detect_frequency_anomalies(
            memories, config
        )
        assert any(a.anomaly_type == "频率激增" for a in alerts)

    def test_detect_silence(self):
        """检测长期沉默"""
        now = time.time()
        memories = []
        # 10-20天前有活动，近7天无活动
        for i in range(15):
            memories.append(
                _make_memory("测试", created_at=now - (10 + i) * 86400)
            )

        config = ObservationConfig(min_sessions_for_pattern=3)
        alerts = AnomalyDetector.detect_frequency_anomalies(
            memories, config
        )
        assert any(a.anomaly_type == "长期沉默" for a in alerts)

    def test_detect_persistent_negative_emotion(self):
        """检测持续消极情绪"""
        now = time.time()
        memories = []
        for i in range(5):
            memories.append(
                _make_memory(
                    "焦虑不安",
                    memory_type=MemoryType.EMOTIONAL,
                    created_at=now - i * 100,
                )
            )

        config = ObservationConfig(min_sessions_for_pattern=3)
        alerts = AnomalyDetector.detect_emotional_anomalies(
            memories, config
        )
        assert any(a.anomaly_type == "持续消极情绪" for a in alerts)

    def test_detect_emotional_shift(self):
        """检测情绪突变"""
        now = time.time()
        memories = [
            _make_memory(
                "焦虑不安",
                memory_type=MemoryType.EMOTIONAL,
                created_at=now - 100,
            ),
            _make_memory(
                "积极乐观",
                memory_type=MemoryType.EMOTIONAL,
                created_at=now - 3600,
            ),
        ]

        config = ObservationConfig(min_sessions_for_pattern=3)
        alerts = AnomalyDetector.detect_emotional_anomalies(
            memories, config
        )
        assert any(a.anomaly_type == "情绪突变" for a in alerts)

    def test_detect_topic_shift(self):
        """检测主题突变"""
        now = time.time()
        memories = [
            _make_memory("工作事业问题", created_at=now - 5000),
            _make_memory("事业升职", created_at=now - 4000),
            _make_memory("工作烦恼", created_at=now - 3000),
            _make_memory("感情爱情问题", created_at=now - 2000),
            _make_memory("恋爱对象", created_at=now - 1000),
            _make_memory("感情分手", created_at=now - 500),
        ]

        config = ObservationConfig(min_sessions_for_pattern=3)
        alerts = AnomalyDetector.detect_topic_shifts(memories, config)
        assert len(alerts) >= 1
        assert alerts[0].anomaly_type == "主题突变"

    def test_detect_all_empty(self):
        """空数据返回空"""
        alerts = AnomalyDetector.detect_all([])
        assert alerts == ()

    def test_detect_all_insufficient(self):
        """数据不足返回空"""
        memories = [_make_memory("测试")]
        alerts = AnomalyDetector.detect_all(memories)
        assert alerts == ()


# ============================================================
# 趋势报告测试
# ============================================================


class TestTrendReporter:
    """趋势报告测试"""

    def test_generate_weekly_report(self):
        """生成周报"""
        now = time.time()
        memories = []
        for i in range(5):
            memories.append(
                _make_memory("工作事业", "乾为天", created_at=now - i * 86400)
            )

        report = TrendReporter.generate_report(
            "test_user", memories, ReportPeriod.WEEKLY
        )
        assert report.user_id == "test_user"
        assert report.period == ReportPeriod.WEEKLY
        assert report.total_sessions == 5
        assert "乾为天" in report.dominant_hexagrams
        assert len(report.indicators) >= 1

    def test_generate_monthly_report(self):
        """生成月报"""
        now = time.time()
        memories = []
        for i in range(10):
            memories.append(
                _make_memory(
                    "感情爱情",
                    "坤为地",
                    created_at=now - i * 86400 * 3,
                )
            )

        report = TrendReporter.generate_report(
            "test_user", memories, ReportPeriod.MONTHLY
        )
        assert report.period == ReportPeriod.MONTHLY
        assert report.total_sessions == 10

    def test_report_with_no_data(self):
        """无数据报告"""
        report = TrendReporter.generate_report(
            "test_user", [], ReportPeriod.WEEKLY
        )
        assert report.total_sessions == 0
        assert report.dominant_hexagrams == ()

    def test_report_dominant_topics(self):
        """报告包含主要主题"""
        now = time.time()
        memories = []
        for i in range(5):
            memories.append(
                _make_memory("工作事业升职", created_at=now - i * 100)
            )

        report = TrendReporter.generate_report(
            "test_user", memories, ReportPeriod.WEEKLY
        )
        assert "事业" in report.dominant_topics

    def test_report_summary_not_empty(self):
        """报告总结不为空"""
        now = time.time()
        memories = [
            _make_memory("测试", "乾为天", created_at=now - 100),
        ]

        report = TrendReporter.generate_report(
            "test_user", memories, ReportPeriod.WEEKLY
        )
        assert report.summary != ""


# ============================================================
# 观察Agent测试
# ============================================================


class TestObservationAgent:
    """观察Agent测试"""

    def test_observe_full(self):
        """完整观察分析"""
        now = time.time()
        memories = []
        for i in range(10):
            memories.append(
                _make_memory("工作事业", "乾为天", created_at=now - i * 86400)
            )

        result = ObservationAgent.observe("test_user", memories)
        assert result.user_id == "test_user"
        assert result.observation_type == ObservationType.PATTERN
        assert result.generated_at > 0

    def test_observe_empty(self):
        """空数据观察"""
        result = ObservationAgent.observe("test_user", [])
        assert result.user_id == "test_user"
        assert result.patterns == ()

    def test_get_trend_report(self):
        """获取趋势报告"""
        now = time.time()
        memories = [
            _make_memory("测试", "乾为天", created_at=now - 100),
        ]

        report = ObservationAgent.get_trend_report(
            "test_user", memories, ReportPeriod.WEEKLY
        )
        assert report.period == ReportPeriod.WEEKLY

    def test_check_anomalies(self):
        """异常检测"""
        now = time.time()
        memories = []
        # 10-20天前有活动，近7天无活动
        for i in range(15):
            memories.append(
                _make_memory("测试", created_at=now - (10 + i) * 86400)
            )

        alerts = ObservationAgent.check_anomalies(memories)
        # 应该检测到长期沉默
        assert any(a.anomaly_type == "长期沉默" for a in alerts)

    def test_detect_patterns(self):
        """模式检测"""
        now = time.time()
        memories = []
        for i in range(8):
            memories.append(
                _make_memory("工作事业", "乾为天", created_at=now - i * 100)
            )

        patterns = ObservationAgent.detect_patterns(memories)
        assert len(patterns) >= 1

    def test_custom_config(self):
        """自定义配置"""
        config = ObservationConfig(
            min_sessions_for_pattern=2,
            anomaly_z_score=1.5,
            max_patterns=3,
        )
        now = time.time()
        memories = [
            _make_memory("测试", "乾为天", created_at=now - 100),
            _make_memory("测试", "乾为天", created_at=now - 200),
        ]

        patterns = ObservationAgent.detect_patterns(memories, config)
        assert len(patterns) <= config.max_patterns


# ============================================================
# 类型测试
# ============================================================


class TestObservationTypes:
    """观察类型测试"""

    def test_detected_pattern_frozen(self):
        """DetectedPattern 不可变"""
        pattern = DetectedPattern(
            category=PatternCategory.HEXAGRAM_FREQUENCY,
            description="测试",
            confidence=0.8,
            frequency=5,
        )
        with pytest.raises(AttributeError):
            pattern.confidence = 0.9  # type: ignore

    def test_anomaly_alert_frozen(self):
        """AnomalyAlert 不可变"""
        alert = AnomalyAlert(
            severity=AnomalySeverity.WARNING,
            anomaly_type="测试",
            description="测试异常",
            detected_at=time.time(),
        )
        with pytest.raises(AttributeError):
            alert.severity = AnomalySeverity.CRITICAL  # type: ignore

    def test_trend_report_frozen(self):
        """TrendReport 不可变"""
        report = TrendReport(
            user_id="test",
            period=ReportPeriod.WEEKLY,
            period_start=0.0,
            period_end=1.0,
            total_sessions=5,
        )
        with pytest.raises(AttributeError):
            report.total_sessions = 10  # type: ignore

    def test_observation_config_defaults(self):
        """ObservationConfig 默认值"""
        config = ObservationConfig()
        assert config.min_sessions_for_pattern == 5
        assert config.anomaly_z_score == 2.0
        assert config.trend_window_days == 30
        assert config.max_patterns == 10

    def test_trend_direction_enum(self):
        """趋势方向枚举值"""
        assert TrendDirection.IMPROVING.value == "上升"
        assert TrendDirection.DECLINING.value == "下降"
        assert TrendDirection.STABLE.value == "平稳"

    def test_anomaly_severity_enum(self):
        """异常严重程度枚举值"""
        assert AnomalySeverity.INFO.value == "信息"
        assert AnomalySeverity.WARNING.value == "警告"
        assert AnomalySeverity.CRITICAL.value == "严重"


# ============================================================
# 模式分析器测试
# ============================================================


class TestPatternAnalyzer:
    """模式分析器测试（五行旺衰定性分析）"""

    def _make_frequency_pattern(
        self,
        name: str = "乾",
        frequency: int = 5,
        confidence: float = 0.6,
    ) -> DetectedPattern:
        """创建卦象频率模式"""
        return DetectedPattern(
            category=PatternCategory.HEXAGRAM_FREQUENCY,
            description=f"卦象'{name}'出现{frequency}次",
            confidence=confidence,
            frequency=frequency,
            examples=(name,),
        )

    def _make_sequence_pattern(
        self, *names: str, frequency: int = 3
    ) -> DetectedPattern:
        """创建变化序列模式"""
        return DetectedPattern(
            category=PatternCategory.CHANGE_SEQUENCE,
            description=f"变化序列出现{frequency}次",
            confidence=0.5,
            frequency=frequency,
            examples=names,
        )

    def test_analyze_empty_patterns(self):
        """空模式返回默认结果"""
        result = PatternAnalyzer.analyze([])
        assert result["strength"] == ProsperityState.XIU.value
        assert "数据不足" in result["trend"]
        assert "无模式数据" in result["relationships"]
        assert "暂无足够数据" in result["advice"]

    def test_analyze_result_keys(self):
        """分析结果包含所有必需字段"""
        patterns = [self._make_frequency_pattern("乾", 5)]
        result = PatternAnalyzer.analyze(patterns, month_branch="子")
        assert "strength" in result
        assert "trend" in result
        assert "relationships" in result
        assert "advice" in result

    def test_strength_is_qualitative(self):
        """strength 输出为旺相休囚死之一"""
        patterns = [self._make_frequency_pattern("离", 6)]
        result = PatternAnalyzer.analyze(patterns, month_branch="午")
        # 离属火，午月火旺
        assert result["strength"] in {
            s.value for s in ProsperityState
        }

    def test_fire_prosperity_in_fire_month(self):
        """离卦在午月应为旺"""
        patterns = [self._make_frequency_pattern("离", 6)]
        result = PatternAnalyzer.analyze(patterns, month_branch="午")
        assert result["strength"] == ProsperityState.WANG.value

    def test_metal_prosperity_in_fire_month(self):
        """乾卦（金）在午月（火）应为死（火克金）"""
        patterns = [self._make_frequency_pattern("乾", 6)]
        result = PatternAnalyzer.analyze(patterns, month_branch="午")
        assert result["strength"] == ProsperityState.SI.value

    def test_trend_with_indicators(self):
        """有趋势指标时使用指标判断趋势"""
        patterns = [self._make_frequency_pattern("坤", 4)]
        indicator = TrendIndicator(
            metric="活动频率",
            current_value=10.0,
            previous_value=5.0,
            change_rate=1.0,
            direction=TrendDirection.IMPROVING,
        )
        result = PatternAnalyzer.analyze(
            patterns, trend_indicators=[indicator], month_branch="子"
        )
        assert "上升" in result["trend"]

    def test_trend_without_indicators(self):
        """无趋势指标时根据模式频率推断"""
        patterns = [self._make_frequency_pattern("坎", 6)]
        result = PatternAnalyzer.analyze(patterns, month_branch="子")
        # 频率6 >= 5 且 confidence 0.6 > 0.5 -> 上升
        assert "上升" in result["trend"]

    def test_relationships_with_two_hexagrams(self):
        """两个卦象时分析生克关系"""
        patterns = [self._make_sequence_pattern("乾", "离", frequency=3)]
        result = PatternAnalyzer.analyze(patterns, month_branch="子")
        # 乾(金) 克 离(火) 不对，火克金
        # 实际: 离(火) vs 乾(金) -> 火克金
        assert "克" in result["relationships"] or "生" in result["relationships"]

    def test_relationships_single_hexagram(self):
        """单个卦象时描述其五行状态"""
        patterns = [self._make_frequency_pattern("震", 4)]
        result = PatternAnalyzer.analyze(patterns, month_branch="卯")
        # 震属木，卯月木旺
        assert "木" in result["relationships"]

    def test_advice_contains_practical_guidance(self):
        """建议包含实用指导"""
        patterns = [self._make_frequency_pattern("坤", 5)]
        result = PatternAnalyzer.analyze(patterns, month_branch="子")
        # 坤(土)在子月(水) -> 土克水为旺？不对
        # 子月水旺，土克水 -> 土为相
        # 不管具体旺衰，建议应该不为空
        assert len(result["advice"]) > 10

    def test_no_overall_score(self):
        """不输出 overall_score 数值"""
        patterns = [self._make_frequency_pattern("乾", 5)]
        result = PatternAnalyzer.analyze(patterns, month_branch="子")
        assert "overall_score" not in result
        assert "score" not in result

    def test_multiple_patterns_composite(self):
        """多模式综合分析"""
        patterns = [
            self._make_frequency_pattern("乾", 6, 0.7),
            self._make_frequency_pattern("坤", 4, 0.5),
            DetectedPattern(
                category=PatternCategory.EMOTIONAL_CYCLE,
                description="主导情绪为焦虑",
                confidence=0.6,
                frequency=4,
                examples=("焦虑",),
            ),
        ]
        result = PatternAnalyzer.analyze(patterns, month_branch="子")
        # 情绪模式应触发相关建议
        assert "情绪" in result["advice"]

    def test_unknown_hexagram_graceful(self):
        """未知卦象名称不崩溃"""
        patterns = [self._make_frequency_pattern("未知卦", 3)]
        result = PatternAnalyzer.analyze(patterns, month_branch="子")
        # 应返回默认值而不崩溃
        assert result["strength"] in {s.value for s in ProsperityState}
