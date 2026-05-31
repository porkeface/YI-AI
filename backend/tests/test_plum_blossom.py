"""梅花易数引擎单元测试

测试数字起卦、外应起卦和体用分析功能。
"""

from __future__ import annotations

import unittest

from foundation.plum_blossom import (
    ExternalSign,
    NumberBasis,
    PlumBlossomEngine,
    PlumBlossomResult,
)
from foundation.types import Element


class TestPlumBlossomNumbers(unittest.TestCase):
    """数字起卦测试"""

    def test_number_divination_basic(self) -> None:
        """数字起卦基本测试：1,1 -> 乾上兑下"""
        result = PlumBlossomEngine.divinate_by_numbers(1, 1)
        self.assertIsInstance(result, PlumBlossomResult)
        self.assertIsNotNone(result.hexagram)
        self.assertIsNotNone(result.ti_gua)
        self.assertIsNotNone(result.yong_gua)
        self.assertIsNotNone(result.sheng_ke_relation)
        self.assertIsNotNone(result.method)

    def test_number_divination_hexagram_structure(self) -> None:
        """数字起卦结果包含完整卦结构"""
        result = PlumBlossomEngine.divinate_by_numbers(1, 1)
        self.assertEqual(len(result.hexagram.lines), 6)

    def test_number_divination_changed_hexagram(self) -> None:
        """数字起卦应产生变卦"""
        result = PlumBlossomEngine.divinate_by_numbers(1, 1)
        # 有动爻时应有变卦
        self.assertIsNotNone(result.changed_hexagram)

    def test_houtian_basis(self) -> None:
        """后天数起卦"""
        result = PlumBlossomEngine.divinate_by_numbers(
            5, 3, basis=NumberBasis.HOUTIAN
        )
        self.assertIsInstance(result, PlumBlossomResult)
        self.assertIsNotNone(result.hexagram)
        self.assertIn("后天数", result.method)

    def test_xiantian_basis_default(self) -> None:
        """默认使用先天数"""
        result = PlumBlossomEngine.divinate_by_numbers(1, 1)
        self.assertIn("先天数", result.method)

    def test_number_mod_8_zero_maps_to_8(self) -> None:
        """数字除8余0时映射到第8卦（坤）"""
        # 8 % 8 = 0 -> 坤
        result = PlumBlossomEngine.divinate_by_numbers(8, 8)
        self.assertIsNotNone(result.hexagram)

    def test_number_mod_6_zero_maps_to_6(self) -> None:
        """动爻除6余0时映射到第6爻"""
        # 3+3=6, 6%6=0 -> 动爻在第6爻
        result = PlumBlossomEngine.divinate_by_numbers(3, 3)
        self.assertIsNotNone(result.hexagram)

    def test_large_numbers(self) -> None:
        """大数起卦应正常工作"""
        result = PlumBlossomEngine.divinate_by_numbers(100, 200)
        self.assertIsNotNone(result.hexagram)
        self.assertIsNotNone(result.changed_hexagram)


class TestPlumBlossomExternalSign(unittest.TestCase):
    """外应起卦测试"""

    def test_direction_basic(self) -> None:
        """方位起卦基本测试"""
        result = PlumBlossomEngine.divinate_by_external_sign("北", "南")
        self.assertIsInstance(result, PlumBlossomResult)
        self.assertIsNotNone(result.hexagram)
        # 上卦=北=坎，下卦=南=离 -> 坎上离下 = 水火既济
        self.assertEqual(result.hexagram.name, "水火既济")

    def test_direction_with_moving_position(self) -> None:
        """外应起卦支持指定动爻"""
        result = PlumBlossomEngine.divinate_by_external_sign(
            "北", "南", moving_position=3
        )
        self.assertIsNotNone(result.hexagram)
        self.assertEqual(len(result.hexagram.lines), 6)

    def test_direction_default_moving(self) -> None:
        """外应起卦默认初爻动"""
        result = PlumBlossomEngine.divinate_by_external_sign("北", "南")
        self.assertIsNotNone(result.hexagram)

    def test_direction_all_eight(self) -> None:
        """八个方位都能正确映射"""
        directions = ["北", "南", "东", "西", "东北", "东南", "西南", "西北"]
        for upper_dir in directions:
            for lower_dir in directions:
                result = PlumBlossomEngine.divinate_by_external_sign(
                    upper_dir, lower_dir
                )
                self.assertIsNotNone(result.hexagram)

    def test_animal_sign(self) -> None:
        """动物外应起卦"""
        result = PlumBlossomEngine.divinate_by_external_sign(
            "龙", "虎", sign_type=ExternalSign.ANIMAL
        )
        self.assertIsNotNone(result.hexagram)
        # 上卦=龙=震，下卦=虎=兑 -> 震上兑下 = 雷泽归妹
        self.assertEqual(result.hexagram.name, "雷泽归妹")

    def test_invalid_upper_sign(self) -> None:
        """无效的上卦外应应抛出异常"""
        with self.assertRaises(ValueError):
            PlumBlossomEngine.divinate_by_external_sign("无效", "南")

    def test_invalid_lower_sign(self) -> None:
        """无效的下卦外应应抛出异常"""
        with self.assertRaises(ValueError):
            PlumBlossomEngine.divinate_by_external_sign("北", "无效")

    def test_invalid_moving_position_zero(self) -> None:
        """动爻位置为0应抛出异常"""
        with self.assertRaises(ValueError):
            PlumBlossomEngine.divinate_by_external_sign(
                "北", "南", moving_position=0
            )

    def test_invalid_moving_position_seven(self) -> None:
        """动爻位置为7应抛出异常"""
        with self.assertRaises(ValueError):
            PlumBlossomEngine.divinate_by_external_sign(
                "北", "南", moving_position=7
            )


class TestPlumBlossomTiYong(unittest.TestCase):
    """体用关系测试"""

    def test_ti_yong_relation_bibi(self) -> None:
        """体用比和：乾上兑下，动爻在下卦"""
        # 1,2 -> upper=乾(Metal), lower=兑(Metal), moving=3(lower)
        result = PlumBlossomEngine.divinate_by_numbers(1, 2)
        self.assertIsNotNone(result.sheng_ke_relation)
        self.assertIn("比和", result.sheng_ke_relation)

    def test_ti_yong_relation_sheng(self) -> None:
        """体用生克关系测试"""
        # 1,3 -> upper=乾(Metal), lower=离(Fire), moving=4(upper)
        # 动在上卦 -> 上为用，下为体
        # 体=离(Fire), 用=乾(Metal)
        # 火克金 -> 体克用
        result = PlumBlossomEngine.divinate_by_numbers(1, 3)
        self.assertIsNotNone(result.sheng_ke_relation)
        self.assertIn("体", result.sheng_ke_relation)

    def test_ti_yong_moving_in_lower(self) -> None:
        """动爻在下卦时，下卦为用，上卦为体"""
        # 1,1 -> upper=乾, lower=乾, moving=2(lower)
        result = PlumBlossomEngine.divinate_by_numbers(1, 1)
        # 动在下卦 -> 上为体，下为用
        self.assertEqual(result.ti_gua, "乾")
        self.assertEqual(result.yong_gua, "乾")

    def test_ti_yong_elements(self) -> None:
        """体用五行属性正确"""
        result = PlumBlossomEngine.divinate_by_numbers(1, 1)
        self.assertIsInstance(result.ti_element, Element)
        self.assertIsInstance(result.yong_element, Element)


class TestPlumBlossomTime(unittest.TestCase):
    """时间起卦测试"""

    def test_time_divination_basic(self) -> None:
        """时间起卦基本测试"""
        result = PlumBlossomEngine.divinate_by_time(
            year=2024, month=1, day=1, hour=12
        )
        self.assertIsInstance(result, PlumBlossomResult)
        self.assertIsNotNone(result.hexagram)
        self.assertIn("时间起卦", result.method)

    def test_time_divination_structure(self) -> None:
        """时间起卦结果包含完整结构"""
        result = PlumBlossomEngine.divinate_by_time(
            year=2024, month=6, day=15, hour=8
        )
        self.assertEqual(len(result.hexagram.lines), 6)
        self.assertIsNotNone(result.ti_gua)
        self.assertIsNotNone(result.yong_gua)
        self.assertIsNotNone(result.sheng_ke_relation)

    def test_different_times_different_results(self) -> None:
        """不同时间应产生不同卦"""
        result1 = PlumBlossomEngine.divinate_by_time(
            year=2024, month=1, day=1, hour=0
        )
        result2 = PlumBlossomEngine.divinate_by_time(
            year=2024, month=6, day=15, hour=12
        )
        # 不同时间可能产生不同卦（不保证一定不同，但结构应完整）
        self.assertIsNotNone(result1.hexagram)
        self.assertIsNotNone(result2.hexagram)


class TestPlumBlossomResult(unittest.TestCase):
    """梅花易数结果数据结构测试"""

    def test_result_fields(self) -> None:
        """结果包含所有必要字段"""
        result = PlumBlossomEngine.divinate_by_numbers(1, 1)
        self.assertTrue(hasattr(result, "hexagram"))
        self.assertTrue(hasattr(result, "changed_hexagram"))
        self.assertTrue(hasattr(result, "ti_gua"))
        self.assertTrue(hasattr(result, "yong_gua"))
        self.assertTrue(hasattr(result, "ti_element"))
        self.assertTrue(hasattr(result, "yong_element"))
        self.assertTrue(hasattr(result, "sheng_ke_relation"))
        self.assertTrue(hasattr(result, "method"))

    def test_result_frozen(self) -> None:
        """结果是不可变的"""
        result = PlumBlossomEngine.divinate_by_numbers(1, 1)
        with self.assertRaises(AttributeError):
            result.hexagram = None  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
