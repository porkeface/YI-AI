"""日辰分析（长生十二宫）单元测试

测试用神在日辰的生命周期状态（生旺墓绝空）。
依据《卜筮正宗》："日辰为六爻之主宰"。
"""

from __future__ import annotations

import unittest

from foundation.types import (
    Element,
    Hexagram,
    Line,
    SixRelation,
    SixSpirit,
    YinYang,
)
from foundation.element_engine import ElementEngine
from foundation.gan_zhi_engine import GanZhiEngine
from foundation.hexagram_engine import HexagramEngine
from foundation.six_relation_engine import SixRelationEngine
from rule_engine.wang_shuai_analyzer import (
    DayBranchAnalysis,
    LifecycleStage,
    WangShuaiAnalyzer,
    YongShenLifecycle,
)


def _create_hexagram_with_relations(
    hexagram: Hexagram,
    moving_positions: tuple[int, ...] = (),
    shi_position: int = 6,
    ying_position: int = 3,
) -> Hexagram:
    """创建带有完整六亲和世应信息的卦"""
    najia = GanZhiEngine.get_najia(hexagram.name)
    line_elements: list[Element] = []
    for gz in najia:
        branch = gz[1]
        elem = ElementEngine.get_element_by_branch(branch)
        line_elements.append(elem)

    relations = SixRelationEngine.assign(hexagram.element, line_elements)

    new_lines = []
    for i, line in enumerate(hexagram.lines):
        pos = i + 1
        new_lines.append(Line(
            position=pos,
            yin_yang=line.yin_yang,
            is_moving=(pos in moving_positions),
            element=line_elements[i],
            six_relation=relations[i],
            six_spirit=SixSpirit.QINGLONG,
            gan_zhi=najia[i],
            is_shi=(pos == shi_position),
            is_ying=(pos == ying_position),
        ))

    return Hexagram(
        id=hexagram.id,
        name=hexagram.name,
        upper_trigram=hexagram.upper_trigram,
        lower_trigram=hexagram.lower_trigram,
        lines=tuple(new_lines),  # type: ignore[arg-type]
        element=hexagram.element,
        judgment=hexagram.judgment,
        image=hexagram.image,
    )


class TestWangShuaiDayBranch(unittest.TestCase):
    """旺衰分析器日辰分析测试"""

    def setUp(self) -> None:
        """设置测试数据"""
        self.qian = HexagramEngine.get_by_name("乾为天")
        self.qian_with_relations = _create_hexagram_with_relations(
            self.qian, shi_position=6
        )

    def test_analyze_day_branch_returns_result(self) -> None:
        """analyze_day_branch 返回 DayBranchAnalysis"""
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.qian_with_relations, SixRelation.WEALTH, "子"
        )
        self.assertIsInstance(result, DayBranchAnalysis)
        self.assertEqual(result.day_branch, "子")
        self.assertEqual(result.day_element, Element.WATER)
        self.assertIsInstance(result.yong_shen_lifecycle, YongShenLifecycle)
        self.assertIsInstance(result.lifecycle_stage, LifecycleStage)
        self.assertTrue(len(result.description) > 0)

    def test_analyze_with_day_branch_param(self) -> None:
        """analyze 方法支持 day_branch 参数"""
        result = WangShuaiAnalyzer.analyze(
            self.qian_with_relations, SixRelation.WEALTH, "寅", day_branch="子"
        )
        self.assertIsNotNone(result.day_branch_analysis)
        self.assertEqual(result.day_branch_analysis.day_branch, "子")  # type: ignore[union-attr]


class TestWoodLifecycle(unittest.TestCase):
    """木的长生十二宫测试

    木长生在亥，帝旺在卯，墓在未，绝在申。
    """

    def setUp(self) -> None:
        """设置木五行的测试卦"""
        # 乾卦属金，金克木为妻财 -> 妻财爻五行属木
        qian = HexagramEngine.get_by_name("乾为天")
        self.qian_with_relations = _create_hexagram_with_relations(
            qian, shi_position=6
        )

    def test_wood_di_wang_at_mao(self) -> None:
        """木帝旺在卯"""
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.qian_with_relations, SixRelation.WEALTH, "卯"
        )
        self.assertEqual(result.yong_shen_lifecycle, YongShenLifecycle.WANG)
        self.assertEqual(result.lifecycle_stage, LifecycleStage.DI_WANG)

    def test_wood_mu_at_wei(self) -> None:
        """木墓在未"""
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.qian_with_relations, SixRelation.WEALTH, "未"
        )
        self.assertEqual(result.yong_shen_lifecycle, YongShenLifecycle.MU)
        self.assertEqual(result.lifecycle_stage, LifecycleStage.MU)

    def test_wood_jue_at_shen(self) -> None:
        """木绝在申"""
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.qian_with_relations, SixRelation.WEALTH, "申"
        )
        self.assertEqual(result.yong_shen_lifecycle, YongShenLifecycle.JUE)
        self.assertEqual(result.lifecycle_stage, LifecycleStage.JUE)

    def test_wood_sheng_at_hai(self) -> None:
        """木长生在亥（属SHENG类）"""
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.qian_with_relations, SixRelation.WEALTH, "亥"
        )
        self.assertEqual(result.yong_shen_lifecycle, YongShenLifecycle.SHENG)
        self.assertEqual(result.lifecycle_stage, LifecycleStage.CHANG_SHENG)


class TestFireLifecycle(unittest.TestCase):
    """火的长生十二宫测试

    火长生在寅，帝旺在午，墓在戌，绝在亥。
    """

    def setUp(self) -> None:
        """设置火五行的测试卦"""
        # 坤卦属土，火生土 -> 父母爻五行属火
        kun = HexagramEngine.get_by_name("坤为地")
        self.kun_with_relations = _create_hexagram_with_relations(
            kun, shi_position=6
        )

    def test_fire_di_wang_at_wu(self) -> None:
        """火帝旺在午"""
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.kun_with_relations, SixRelation.PARENT, "午"
        )
        self.assertEqual(result.yong_shen_lifecycle, YongShenLifecycle.WANG)
        self.assertEqual(result.lifecycle_stage, LifecycleStage.DI_WANG)

    def test_fire_mu_at_xu(self) -> None:
        """火墓在戌"""
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.kun_with_relations, SixRelation.PARENT, "戌"
        )
        self.assertEqual(result.yong_shen_lifecycle, YongShenLifecycle.MU)
        self.assertEqual(result.lifecycle_stage, LifecycleStage.MU)

    def test_fire_jue_at_hai(self) -> None:
        """火绝在亥"""
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.kun_with_relations, SixRelation.PARENT, "亥"
        )
        self.assertEqual(result.yong_shen_lifecycle, YongShenLifecycle.JUE)
        self.assertEqual(result.lifecycle_stage, LifecycleStage.JUE)

    def test_fire_sheng_at_yin(self) -> None:
        """火长生在寅（属SHENG类）"""
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.kun_with_relations, SixRelation.PARENT, "寅"
        )
        self.assertEqual(result.yong_shen_lifecycle, YongShenLifecycle.SHENG)
        self.assertEqual(result.lifecycle_stage, LifecycleStage.CHANG_SHENG)


class TestMetalLifecycle(unittest.TestCase):
    """金的长生十二宫测试

    金长生在巳，帝旺在酉，墓在丑，绝在寅。
    """

    def setUp(self) -> None:
        """设置金五行的测试卦"""
        # 乾卦属金，金同金 -> 兄弟爻五行属金
        qian = HexagramEngine.get_by_name("乾为天")
        self.qian_with_relations = _create_hexagram_with_relations(
            qian, shi_position=6
        )

    def test_metal_di_wang_at_you(self) -> None:
        """金帝旺在酉"""
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.qian_with_relations, SixRelation.BROTHER, "酉"
        )
        self.assertEqual(result.yong_shen_lifecycle, YongShenLifecycle.WANG)
        self.assertEqual(result.lifecycle_stage, LifecycleStage.DI_WANG)

    def test_metal_mu_at_chou(self) -> None:
        """金墓在丑"""
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.qian_with_relations, SixRelation.BROTHER, "丑"
        )
        self.assertEqual(result.yong_shen_lifecycle, YongShenLifecycle.MU)
        self.assertEqual(result.lifecycle_stage, LifecycleStage.MU)

    def test_metal_jue_at_yin(self) -> None:
        """金绝在寅"""
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.qian_with_relations, SixRelation.BROTHER, "寅"
        )
        self.assertEqual(result.yong_shen_lifecycle, YongShenLifecycle.JUE)
        self.assertEqual(result.lifecycle_stage, LifecycleStage.JUE)


class TestWaterLifecycle(unittest.TestCase):
    """水的长生十二宫测试

    水长生在申，帝旺在子，墓在辰，绝在巳。
    """

    def setUp(self) -> None:
        """设置水五行的测试卦"""
        # 乾卦属金，金生水 -> 子孙爻五行属水
        qian = HexagramEngine.get_by_name("乾为天")
        self.qian_with_relations = _create_hexagram_with_relations(
            qian, shi_position=6
        )

    def test_water_di_wang_at_zi(self) -> None:
        """水帝旺在子"""
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.qian_with_relations, SixRelation.CHILDREN, "子"
        )
        self.assertEqual(result.yong_shen_lifecycle, YongShenLifecycle.WANG)
        self.assertEqual(result.lifecycle_stage, LifecycleStage.DI_WANG)

    def test_water_mu_at_chen(self) -> None:
        """水墓在辰"""
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.qian_with_relations, SixRelation.CHILDREN, "辰"
        )
        self.assertEqual(result.yong_shen_lifecycle, YongShenLifecycle.MU)
        self.assertEqual(result.lifecycle_stage, LifecycleStage.MU)

    def test_water_jue_at_si(self) -> None:
        """水绝在巳"""
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.qian_with_relations, SixRelation.CHILDREN, "巳"
        )
        self.assertEqual(result.yong_shen_lifecycle, YongShenLifecycle.JUE)
        self.assertEqual(result.lifecycle_stage, LifecycleStage.JUE)


class TestLifecycleFull(unittest.TestCase):
    """长生十二宫完整阶段覆盖测试

    验证每个五行在所有12个地支上的生命周期状态正确。
    """

    def _get_lifecycle(self, element: Element, branch: str) -> YongShenLifecycle:
        """辅助方法：获取五行在指定地支的生命周期"""
        from rule_engine.wang_shuai_analyzer import _get_lifecycle
        return _get_lifecycle(element, branch)

    def test_wood_all_branches(self) -> None:
        """木在12地支的完整生命周期"""
        expected = {
            "亥": YongShenLifecycle.SHENG,   # 长生
            "子": YongShenLifecycle.SHENG,   # 沐浴
            "丑": YongShenLifecycle.SHENG,   # 冠带
            "寅": YongShenLifecycle.SHENG,   # 临官
            "卯": YongShenLifecycle.WANG,    # 帝旺
            "辰": YongShenLifecycle.SHENG,   # 衰
            "巳": YongShenLifecycle.SHENG,   # 病
            "午": YongShenLifecycle.SHENG,   # 死
            "未": YongShenLifecycle.MU,      # 墓
            "申": YongShenLifecycle.JUE,     # 绝
            "酉": YongShenLifecycle.SHENG,   # 胎
            "戌": YongShenLifecycle.SHENG,   # 养
        }
        for branch, lifecycle in expected.items():
            self.assertEqual(
                self._get_lifecycle(Element.WOOD, branch),
                lifecycle,
                f"木在{branch}应为{lifecycle.value}",
            )

    def test_fire_all_branches(self) -> None:
        """火在12地支的完整生命周期"""
        expected = {
            "寅": YongShenLifecycle.SHENG,   # 长生
            "卯": YongShenLifecycle.SHENG,   # 沐浴
            "辰": YongShenLifecycle.SHENG,   # 冠带
            "巳": YongShenLifecycle.SHENG,   # 临官
            "午": YongShenLifecycle.WANG,    # 帝旺
            "未": YongShenLifecycle.SHENG,   # 衰
            "申": YongShenLifecycle.SHENG,   # 病
            "酉": YongShenLifecycle.SHENG,   # 死
            "戌": YongShenLifecycle.MU,      # 墓
            "亥": YongShenLifecycle.JUE,     # 绝
            "子": YongShenLifecycle.SHENG,   # 胎
            "丑": YongShenLifecycle.SHENG,   # 养
        }
        for branch, lifecycle in expected.items():
            self.assertEqual(
                self._get_lifecycle(Element.FIRE, branch),
                lifecycle,
                f"火在{branch}应为{lifecycle.value}",
            )


class TestDayBranchDescriptions(unittest.TestCase):
    """日辰分析描述文本测试"""

    def setUp(self) -> None:
        qian = HexagramEngine.get_by_name("乾为天")
        self.qian_with_relations = _create_hexagram_with_relations(
            qian, shi_position=6
        )

    def test_wang_description(self) -> None:
        """帝旺描述包含"最旺" """
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.qian_with_relations, SixRelation.CHILDREN, "子"
        )
        self.assertIn("旺", result.description)

    def test_mu_description(self) -> None:
        """墓描述包含"受困" """
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.qian_with_relations, SixRelation.CHILDREN, "辰"
        )
        self.assertIn("困", result.description)

    def test_jue_description(self) -> None:
        """绝描述包含"无力" """
        result = WangShuaiAnalyzer.analyze_day_branch(
            self.qian_with_relations, SixRelation.CHILDREN, "巳"
        )
        self.assertIn("无力", result.description)


if __name__ == "__main__":
    unittest.main()
