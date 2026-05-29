"""基础易学引擎单元测试

测试所有引擎的核心功能。
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
    Trigram,
    TrigramName,
    YinYang,
)
from foundation.element_engine import ElementEngine
from foundation.trigram_engine import TrigramEngine
from foundation.hexagram_engine import HexagramEngine
from foundation.gan_zhi_engine import GanZhiEngine
from foundation.six_relation_engine import SixRelationEngine
from foundation.six_spirit_engine import SixSpiritEngine
from foundation.shi_ying_engine import ShiYingEngine


class TestElementEngine(unittest.TestCase):
    """五行引擎测试"""

    def test_generates(self) -> None:
        """测试五行相生关系"""
        # 木生火
        self.assertTrue(ElementEngine.generates(Element.WOOD, Element.FIRE))
        # 火生土
        self.assertTrue(ElementEngine.generates(Element.FIRE, Element.EARTH))
        # 土生金
        self.assertTrue(ElementEngine.generates(Element.EARTH, Element.METAL))
        # 金生水
        self.assertTrue(ElementEngine.generates(Element.METAL, Element.WATER))
        # 水生木
        self.assertTrue(ElementEngine.generates(Element.WATER, Element.WOOD))
        # 反向不成立
        self.assertFalse(ElementEngine.generates(Element.FIRE, Element.WOOD))

    def test_overcomes(self) -> None:
        """测试五行相克关系"""
        # 木克土
        self.assertTrue(ElementEngine.overcomes(Element.WOOD, Element.EARTH))
        # 土克水
        self.assertTrue(ElementEngine.overcomes(Element.EARTH, Element.WATER))
        # 水克火
        self.assertTrue(ElementEngine.overcomes(Element.WATER, Element.FIRE))
        # 火克金
        self.assertTrue(ElementEngine.overcomes(Element.FIRE, Element.METAL))
        # 金克木
        self.assertTrue(ElementEngine.overcomes(Element.METAL, Element.WOOD))
        # 反向不成立
        self.assertFalse(ElementEngine.overcomes(Element.EARTH, Element.WOOD))

    def test_get_relation(self) -> None:
        """测试获取五行关系"""
        self.assertEqual(
            ElementEngine.get_relation(Element.WOOD, Element.FIRE), "生"
        )
        self.assertEqual(
            ElementEngine.get_relation(Element.WOOD, Element.EARTH), "克"
        )
        self.assertEqual(
            ElementEngine.get_relation(Element.FIRE, Element.WOOD), "被生"
        )
        self.assertEqual(
            ElementEngine.get_relation(Element.EARTH, Element.WOOD), "被克"
        )
        self.assertEqual(
            ElementEngine.get_relation(Element.WOOD, Element.WOOD), "同"
        )

    def test_judge_prosperity(self) -> None:
        """测试旺衰判断"""
        # 春月（寅月）木旺
        self.assertEqual(
            ElementEngine.judge_prosperity(Element.WOOD, "寅"),
            ProsperityState.WANG,
        )
        # 春月火相
        self.assertEqual(
            ElementEngine.judge_prosperity(Element.FIRE, "寅"),
            ProsperityState.XIANG,
        )

    def test_get_element_by_branch(self) -> None:
        """测试地支五行"""
        self.assertEqual(
            ElementEngine.get_element_by_branch("子"), Element.WATER
        )
        self.assertEqual(
            ElementEngine.get_element_by_branch("寅"), Element.WOOD
        )
        self.assertEqual(
            ElementEngine.get_element_by_branch("午"), Element.FIRE
        )


class TestTrigramEngine(unittest.TestCase):
    """八卦引擎测试"""

    def test_get_by_name(self) -> None:
        """测试按名称查询"""
        qian = TrigramEngine.get_by_name("乾")
        self.assertEqual(qian.name, TrigramName.QIAN)
        self.assertEqual(qian.binary_rep, "111")
        self.assertEqual(qian.element, Element.METAL)
        self.assertEqual(qian.nature, "天")

    def test_get_by_binary(self) -> None:
        """测试按二进制查询"""
        trigram = TrigramEngine.get_by_binary("111")
        self.assertEqual(trigram.name, TrigramName.QIAN)

        trigram = TrigramEngine.get_by_binary("000")
        self.assertEqual(trigram.name, TrigramName.KUN)

    def test_get_element(self) -> None:
        """测试获取五行属性"""
        self.assertEqual(TrigramEngine.get_element("乾"), Element.METAL)
        self.assertEqual(TrigramEngine.get_element("坤"), Element.EARTH)
        self.assertEqual(TrigramEngine.get_element("震"), Element.WOOD)

    def test_get_all_trigrams(self) -> None:
        """测试获取所有八卦"""
        trigrams = TrigramEngine.get_all_trigrams()
        self.assertEqual(len(trigrams), 8)


class TestHexagramEngine(unittest.TestCase):
    """卦引擎测试"""

    def test_create_qian(self) -> None:
        """测试创建乾卦"""
        # 乾卦：六爻皆阳
        lines = [YinYang.YANG] * 6
        hexagram = HexagramEngine.create(lines)
        self.assertEqual(hexagram.name, "乾为天")
        self.assertEqual(hexagram.id, 1)
        self.assertEqual(hexagram.element, Element.METAL)

    def test_create_kun(self) -> None:
        """测试创建坤卦"""
        # 坤卦：六爻皆阴
        lines = [YinYang.YIN] * 6
        hexagram = HexagramEngine.create(lines)
        self.assertEqual(hexagram.name, "坤为地")
        self.assertEqual(hexagram.id, 2)
        self.assertEqual(hexagram.element, Element.EARTH)

    def test_create_mixed(self) -> None:
        """测试创建混合卦"""
        # 水雷屯：010100
        lines = [
            YinYang.YANG,  # 初爻
            YinYang.YIN,   # 二爻
            YinYang.YIN,   # 三爻
            YinYang.YIN,   # 四爻
            YinYang.YANG,  # 五爻
            YinYang.YIN,   # 六爻
        ]
        hexagram = HexagramEngine.create(lines)
        self.assertEqual(hexagram.name, "水雷屯")

    def test_get_changed(self) -> None:
        """测试变卦"""
        # 乾卦，初爻动
        lines = [YinYang.YANG] * 6
        hexagram = HexagramEngine.create(lines)
        changed = HexagramEngine.get_changed(hexagram, (1,))
        # 初爻由阳变阴，变成天风姤
        self.assertEqual(changed.name, "天风姤")

    def test_get_opposite(self) -> None:
        """测试错卦"""
        # 乾卦的错卦是坤卦
        lines = [YinYang.YANG] * 6
        hexagram = HexagramEngine.create(lines)
        opposite = HexagramEngine.get_opposite(hexagram)
        self.assertEqual(opposite.name, "坤为地")

    def test_get_reversed(self) -> None:
        """测试综卦"""
        # 水雷屯的综卦是山水蒙
        lines = [
            YinYang.YANG,
            YinYang.YIN,
            YinYang.YIN,
            YinYang.YIN,
            YinYang.YANG,
            YinYang.YIN,
        ]
        hexagram = HexagramEngine.create(lines)
        reversed_hex = HexagramEngine.get_reversed(hexagram)
        self.assertEqual(reversed_hex.name, "山水蒙")

    def test_get_interlock(self) -> None:
        """测试互卦"""
        # 乾卦的互卦还是乾卦
        lines = [YinYang.YANG] * 6
        hexagram = HexagramEngine.create(lines)
        interlock = HexagramEngine.get_interlock(hexagram)
        self.assertEqual(interlock.name, "乾为天")

    def test_get_by_id(self) -> None:
        """测试按ID查卦"""
        hexagram = HexagramEngine.get_by_id(1)
        self.assertEqual(hexagram.name, "乾为天")

    def test_get_by_name(self) -> None:
        """测试按名查卦"""
        hexagram = HexagramEngine.get_by_name("乾为天")
        self.assertEqual(hexagram.id, 1)

    def test_get_all_hexagrams(self) -> None:
        """测试获取所有64卦"""
        hexagrams = HexagramEngine.get_all_hexagrams()
        self.assertEqual(len(hexagrams), 64)


class TestGanZhiEngine(unittest.TestCase):
    """干支纳甲引擎测试"""

    def test_get_gan_zhi(self) -> None:
        """测试干支组合"""
        self.assertEqual(GanZhiEngine.get_gan_zhi("甲", "子"), "甲子")
        self.assertEqual(GanZhiEngine.get_gan_zhi("乙", "丑"), "乙丑")

    def test_get_najia(self) -> None:
        """测试纳甲"""
        # 乾卦纳甲
        najia = GanZhiEngine.get_najia("乾为天")
        self.assertEqual(len(najia), 6)
        self.assertEqual(najia[0], "甲子")  # 初爻
        self.assertEqual(najia[3], "壬午")  # 四爻

    def test_time_to_gan_zhi(self) -> None:
        """测试时间转干支"""
        result = GanZhiEngine.time_to_gan_zhi(2024, 1, 1, 12)
        self.assertIn("year", result)
        self.assertIn("month", result)
        self.assertIn("day", result)
        self.assertIn("hour", result)

    def test_get_jiazi_table(self) -> None:
        """测试60甲子表"""
        table = GanZhiEngine.get_jiazi_table()
        self.assertEqual(len(table), 60)
        self.assertEqual(table[0], "甲子")
        self.assertEqual(table[59], "癸亥")


class TestSixRelationEngine(unittest.TestCase):
    """六亲引擎测试"""

    def test_assign(self) -> None:
        """测试六亲分配"""
        # 乾卦属金
        line_elements = [
            Element.WATER,  # 金生水 -> 子孙
            Element.WOOD,   # 金克木 -> 妻财
            Element.EARTH,  # 土生金 -> 父母
            Element.FIRE,   # 火克金 -> 官鬼
            Element.METAL,  # 金同金 -> 兄弟
            Element.EARTH,  # 土生金 -> 父母
        ]
        relations = SixRelationEngine.assign(Element.METAL, line_elements)
        self.assertEqual(relations[0], SixRelation.CHILDREN)
        self.assertEqual(relations[1], SixRelation.WEALTH)
        self.assertEqual(relations[2], SixRelation.PARENT)
        self.assertEqual(relations[3], SixRelation.OFFICIAL)
        self.assertEqual(relations[4], SixRelation.BROTHER)
        self.assertEqual(relations[5], SixRelation.PARENT)

    def test_get_relation(self) -> None:
        """测试获取六亲关系"""
        self.assertEqual(
            SixRelationEngine.get_relation(Element.METAL, Element.WATER),
            SixRelation.CHILDREN,
        )
        self.assertEqual(
            SixRelationEngine.get_relation(Element.METAL, Element.WOOD),
            SixRelation.WEALTH,
        )


class TestSixSpiritEngine(unittest.TestCase):
    """六神引擎测试"""

    def test_assign_jia(self) -> None:
        """测试甲日起青龙"""
        spirits = SixSpiritEngine.assign("甲")
        self.assertEqual(spirits[0], SixSpirit.QINGLONG)
        self.assertEqual(spirits[1], SixSpirit.ZHUQUE)
        self.assertEqual(spirits[2], SixSpirit.GOUCHEN)
        self.assertEqual(spirits[3], SixSpirit.TENGHE)
        self.assertEqual(spirits[4], SixSpirit.BAIHU)
        self.assertEqual(spirits[5], SixSpirit.XUANWU)

    def test_assign_bing(self) -> None:
        """测试丙日起朱雀"""
        spirits = SixSpiritEngine.assign("丙")
        self.assertEqual(spirits[0], SixSpirit.ZHUQUE)
        self.assertEqual(spirits[1], SixSpirit.GOUCHEN)

    def test_assign_wu(self) -> None:
        """测试戊日起勾陈"""
        spirits = SixSpiritEngine.assign("戊")
        self.assertEqual(spirits[0], SixSpirit.GOUCHEN)

    def test_get_spirit_for_position(self) -> None:
        """测试获取指定位置的六神"""
        spirit = SixSpiritEngine.get_spirit_for_position("甲", 1)
        self.assertEqual(spirit, SixSpirit.QINGLONG)

        spirit = SixSpiritEngine.get_spirit_for_position("甲", 6)
        self.assertEqual(spirit, SixSpirit.XUANWU)


class TestShiYingEngine(unittest.TestCase):
    """世应引擎测试"""

    def test_get_shi_ying(self) -> None:
        """测试获取世应"""
        # 乾为天：本宫卦，世在六爻
        shi, ying = ShiYingEngine.get_shi_ying(1)
        self.assertEqual(shi, 6)
        self.assertEqual(ying, 3)

    def test_get_shi_ying_by_name(self) -> None:
        """测试按卦名获取世应"""
        # 天风姤：一世卦，世在初爻
        shi, ying = ShiYingEngine.get_shi_ying_by_name("天风姤")
        self.assertEqual(shi, 1)
        self.assertEqual(ying, 4)

    def test_get_palace(self) -> None:
        """测试获取卦宫"""
        palace = ShiYingEngine.get_palace("乾为天")
        self.assertEqual(palace, "乾宫")

        palace = ShiYingEngine.get_palace("天风姤")
        self.assertEqual(palace, "乾宫")

    def test_get_palace_element(self) -> None:
        """测试获取宫五行"""
        elem = ShiYingEngine.get_palace_element("乾为天")
        self.assertEqual(elem, "金")


if __name__ == "__main__":
    unittest.main()
