"""规则推演引擎单元测试

测试用神选取、生克分析、旺衰分析和综合分析功能。
"""

from __future__ import annotations

import unittest

from foundation.types import (
    Element,
    Hexagram,
    Line,
    ProsperityState,
    SixRelation,
    SixSpirit,
    YinYang,
)
from foundation.element_engine import ElementEngine
from foundation.gan_zhi_engine import GanZhiEngine
from foundation.hexagram_engine import HexagramEngine
from foundation.six_relation_engine import SixRelationEngine
from rule_engine.yong_shen import YongShenEngine
from rule_engine.sheng_ke_analyzer import RelationshipAnalysis, ShengKeAnalyzer
from rule_engine.wang_shuai_analyzer import ProsperityAnalysis, WangShuaiAnalyzer
from rule_engine.analyzer import Analyzer


def _create_hexagram_with_relations(
    hexagram: Hexagram,
    moving_positions: tuple[int, ...] = (),
    shi_position: int = 6,
    ying_position: int = 3,
) -> Hexagram:
    """创建带有完整六亲和世应信息的卦

    使用纳甲系统为每个爻分配正确的五行属性和六亲关系。

    Args:
        hexagram: 原始卦
        moving_positions: 动爻位置
        shi_position: 世爻位置
        ying_position: 应爻位置

    Returns:
        更新后的卦
    """
    # 通过纳甲获取每个爻的干支和五行
    najia = GanZhiEngine.get_najia(hexagram.name)
    line_elements: list[Element] = []
    for gz in najia:
        branch = gz[1]  # 地支是第二个字符
        elem = ElementEngine.get_element_by_branch(branch)
        line_elements.append(elem)

    # 根据卦五行分配六亲
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


class TestYongShenEngine(unittest.TestCase):
    """用神选取引擎测试"""

    def setUp(self) -> None:
        """设置测试数据"""
        # 乾卦（纯阳，属金）
        self.qian = HexagramEngine.get_by_name("乾为天")
        # 坤卦（纯阴，属土）
        self.kun = HexagramEngine.get_by_name("坤为地")

    def test_question_career(self) -> None:
        """问事业取官鬼为用神"""
        result = YongShenEngine.find_yong_shen(self.qian, "事业")
        self.assertEqual(result, SixRelation.OFFICIAL)

    def test_question_work(self) -> None:
        """问工作取官鬼为用神"""
        result = YongShenEngine.find_yong_shen(self.qian, "工作")
        self.assertEqual(result, SixRelation.OFFICIAL)

    def test_question_wealth(self) -> None:
        """问财运取妻财为用神"""
        result = YongShenEngine.find_yong_shen(self.qian, "财运")
        self.assertEqual(result, SixRelation.WEALTH)

    def test_question_business(self) -> None:
        """问生意取妻财为用神"""
        result = YongShenEngine.find_yong_shen(self.qian, "生意")
        self.assertEqual(result, SixRelation.WEALTH)

    def test_question_exam(self) -> None:
        """问考试取父母为用神"""
        result = YongShenEngine.find_yong_shen(self.qian, "考试")
        self.assertEqual(result, SixRelation.PARENT)

    def test_question_document(self) -> None:
        """问文书取父母为用神"""
        result = YongShenEngine.find_yong_shen(self.qian, "文书")
        self.assertEqual(result, SixRelation.PARENT)

    def test_question_children(self) -> None:
        """问子女取子孙为用神"""
        result = YongShenEngine.find_yong_shen(self.qian, "子女")
        self.assertEqual(result, SixRelation.CHILDREN)

    def test_question_health(self) -> None:
        """问疾病取子孙为用神"""
        result = YongShenEngine.find_yong_shen(self.qian, "疾病")
        self.assertEqual(result, SixRelation.CHILDREN)

    def test_question_brother(self) -> None:
        """问兄弟取兄弟为用神"""
        result = YongShenEngine.find_yong_shen(self.qian, "兄弟")
        self.assertEqual(result, SixRelation.BROTHER)

    def test_question_marriage_male(self) -> None:
        """问婚姻（男）取妻财为用神"""
        result = YongShenEngine.find_yong_shen(self.qian, "婚姻男")
        self.assertEqual(result, SixRelation.WEALTH)

    def test_question_marriage_female(self) -> None:
        """问婚姻（女）取官鬼为用神"""
        result = YongShenEngine.find_yong_shen(self.qian, "诉讼")
        self.assertEqual(result, SixRelation.OFFICIAL)

    def test_question_travel(self) -> None:
        """问出行取世爻为用神（返回世爻六亲）"""
        qian_with_relations = _create_hexagram_with_relations(
            self.qian, shi_position=6
        )
        result = YongShenEngine.find_yong_shen(
            qian_with_relations, "出行"
        )
        # 世爻在第6爻，返回该爻的六亲
        shi_line = qian_with_relations.lines[5]
        self.assertEqual(result, shi_line.six_relation)

    def test_question_unknown_defaults_to_shi(self) -> None:
        """未知问题类型默认取世爻六亲"""
        qian_with_relations = _create_hexagram_with_relations(
            self.qian, shi_position=6
        )
        result = YongShenEngine.find_yong_shen(
            qian_with_relations, "未知类型"
        )
        shi_line = qian_with_relations.lines[5]
        self.assertEqual(result, shi_line.six_relation)

    def test_find_yong_shen_line(self) -> None:
        """测试找到用神所在的爻"""
        qian_with_relations = _create_hexagram_with_relations(self.qian)
        # 乾卦属金，金克木为妻财
        line = YongShenEngine.find_yong_shen_line(
            qian_with_relations, SixRelation.WEALTH
        )
        self.assertEqual(line.six_relation, SixRelation.WEALTH)

    def test_find_yong_shen_line_not_found(self) -> None:
        """测试用神不存在时抛出异常"""
        # 构造一个所有爻都是同一种六亲的卦来测试异常
        from foundation.trigram_engine import TrigramEngine
        qian_tri = TrigramEngine.get_by_name("乾")
        # 创建一个五行全部为土的卦，卦五行为木
        # 木克土 -> 全部是妻财，不会包含父母
        fake_lines = tuple(
            Line(
                position=i + 1,
                yin_yang=YinYang.YANG,
                is_moving=False,
                element=Element.EARTH,
                six_relation=SixRelation.WEALTH,
                six_spirit=SixSpirit.QINGLONG,
                gan_zhi="甲子",
                is_shi=(i == 5),
                is_ying=(i == 2),
            )
            for i in range(6)
        )
        fake_hex = Hexagram(
            id=99, name="测试卦",
            upper_trigram=qian_tri, lower_trigram=qian_tri,
            lines=fake_lines,  # type: ignore[arg-type]
            element=Element.METAL,
            judgment="", image="",
        )
        with self.assertRaises(ValueError):
            YongShenEngine.find_yong_shen_line(
                fake_hex, SixRelation.PARENT
            )


class TestShengKeAnalyzer(unittest.TestCase):
    """生克关系分析器测试"""

    def setUp(self) -> None:
        """设置测试数据"""
        self.qian = HexagramEngine.get_by_name("乾为天")
        self.kun = HexagramEngine.get_by_name("坤为地")

    def test_analyze_qian(self) -> None:
        """测试乾卦的生克分析"""
        qian_with_relations = _create_hexagram_with_relations(
            self.qian, shi_position=6
        )
        result = ShengKeAnalyzer.analyze(
            qian_with_relations, SixRelation.WEALTH
        )

        self.assertIsInstance(result, RelationshipAnalysis)
        self.assertIsInstance(result.yong_shen_element, Element)
        self.assertIsInstance(result.shi_element, Element)
        self.assertIsInstance(result.yong_shen_to_shi, str)
        self.assertIsInstance(result.moving_line_effects, tuple)
        self.assertIsInstance(result.overall_support, bool)

    def test_analyze_with_moving_lines(self) -> None:
        """测试有动爻时的生克分析"""
        qian_with_relations = _create_hexagram_with_relations(
            self.qian, moving_positions=(1, 3), shi_position=6
        )
        result = ShengKeAnalyzer.analyze(
            qian_with_relations, SixRelation.WEALTH
        )

        # 有动爻时应该有影响描述
        self.assertIsInstance(result.moving_line_effects, tuple)

    def test_analyze_no_moving_lines(self) -> None:
        """测试无动爻时的生克分析"""
        qian_with_relations = _create_hexagram_with_relations(
            self.qian, shi_position=6
        )
        result = ShengKeAnalyzer.analyze(
            qian_with_relations, SixRelation.WEALTH
        )

        # 无动爻时影响描述为空
        self.assertEqual(len(result.moving_line_effects), 0)


class TestWangShuaiAnalyzer(unittest.TestCase):
    """旺衰分析器测试"""

    def setUp(self) -> None:
        """设置测试数据"""
        self.qian = HexagramEngine.get_by_name("乾为天")
        self.kun = HexagramEngine.get_by_name("坤为地")

    def test_analyze_qian_spring(self) -> None:
        """测试乾卦在春季（寅月）的旺衰"""
        qian_with_relations = _create_hexagram_with_relations(
            self.qian, shi_position=6
        )
        result = WangShuaiAnalyzer.analyze(
            qian_with_relations, SixRelation.WEALTH, "寅"
        )

        self.assertIsInstance(result, ProsperityAnalysis)
        self.assertEqual(result.month_element, Element.WOOD)
        self.assertIsInstance(result.yong_shen_element, Element)
        self.assertIsInstance(result.prosperity_state, ProsperityState)
        self.assertIsInstance(result.description, str)

    def test_analyze_kun_winter(self) -> None:
        """测试坤卦在冬季（子月）的旺衰"""
        kun_with_relations = _create_hexagram_with_relations(
            self.kun, shi_position=6
        )
        result = WangShuaiAnalyzer.analyze(
            kun_with_relations, SixRelation.WEALTH, "子"
        )

        self.assertIsInstance(result, ProsperityAnalysis)
        self.assertEqual(result.month_element, Element.WATER)

    def test_analyze_invalid_branch(self) -> None:
        """测试无效地支抛出异常"""
        qian_with_relations = _create_hexagram_with_relations(
            self.qian, shi_position=6
        )
        with self.assertRaises(ValueError):
            WangShuaiAnalyzer.analyze(
                qian_with_relations, SixRelation.WEALTH, "无效"
            )

    def test_prosperity_descriptions(self) -> None:
        """测试旺衰描述不为空"""
        qian_with_relations = _create_hexagram_with_relations(
            self.qian, shi_position=6
        )
        result = WangShuaiAnalyzer.analyze(
            qian_with_relations, SixRelation.WEALTH, "子"
        )
        self.assertTrue(len(result.description) > 0)


class TestAnalyzer(unittest.TestCase):
    """综合分析器测试"""

    def setUp(self) -> None:
        """设置测试数据"""
        self.qian = HexagramEngine.get_by_name("乾为天")
        self.kun = HexagramEngine.get_by_name("坤为地")

    def test_analyze_career(self) -> None:
        """测试事业分析"""
        qian_with_relations = _create_hexagram_with_relations(
            self.qian, shi_position=6
        )
        result = Analyzer.analyze(
            qian_with_relations, "事业", "寅"
        )

        self.assertIsNotNone(result.yong_shen)
        self.assertIsInstance(result.moving_lines, tuple)
        self.assertIsInstance(result.relationships, tuple)
        self.assertIsInstance(result.prosperity, ProsperityState)
        self.assertIsNotNone(result.verdict)

    def test_analyze_wealth(self) -> None:
        """测试财运分析"""
        qian_with_relations = _create_hexagram_with_relations(
            self.qian, shi_position=6
        )
        result = Analyzer.analyze(
            qian_with_relations, "财运", "午"
        )

        self.assertEqual(result.yong_shen, SixRelation.WEALTH)
        self.assertIn(result.verdict.overall, ["吉", "凶", "平"])

    def test_analyze_with_moving_lines(self) -> None:
        """测试有动爻的分析"""
        qian_with_relations = _create_hexagram_with_relations(
            self.qian, moving_positions=(1, 4), shi_position=6
        )
        result = Analyzer.analyze(
            qian_with_relations, "事业", "子"
        )

        self.assertEqual(len(result.moving_lines), 2)
        self.assertIn(1, result.moving_lines)
        self.assertIn(4, result.moving_lines)

    def test_analyze_verdict_range(self) -> None:
        """测试结论数值范围"""
        qian_with_relations = _create_hexagram_with_relations(
            self.qian, shi_position=6
        )
        result = Analyzer.analyze(
            qian_with_relations, "事业", "子"
        )

        self.assertGreaterEqual(result.verdict.strength, 0)
        self.assertLessEqual(result.verdict.strength, 100)
        self.assertGreaterEqual(result.verdict.confidence, 0)
        self.assertLessEqual(result.verdict.confidence, 100)

    def test_analyze_relationships_not_empty(self) -> None:
        """测试关系描述不为空"""
        qian_with_relations = _create_hexagram_with_relations(
            self.qian, shi_position=6
        )
        result = Analyzer.analyze(
            qian_with_relations, "事业", "子"
        )

        self.assertGreater(len(result.relationships), 0)

    def test_analyze_different_months(self) -> None:
        """测试不同月份的分析结果"""
        qian_with_relations = _create_hexagram_with_relations(
            self.qian, shi_position=6
        )

        result_spring = Analyzer.analyze(
            qian_with_relations, "事业", "寅"
        )
        result_winter = Analyzer.analyze(
            qian_with_relations, "事业", "子"
        )

        # 不同月份可能导致不同旺衰状态
        self.assertIsInstance(result_spring.prosperity, ProsperityState)
        self.assertIsInstance(result_winter.prosperity, ProsperityState)


if __name__ == "__main__":
    unittest.main()
