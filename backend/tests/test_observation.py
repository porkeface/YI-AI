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
from ai.observation.anomaly_detector import AnomalyDetector
from ai.observation.trend_reporter import TrendReporter
from ai.observation.agent import ObservationAgent
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
