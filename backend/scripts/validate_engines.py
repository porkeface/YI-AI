"""引擎输出验证脚本

校验所有引擎的输出是否与知识库权威数据一致。
运行方式: PYTHONPATH=. uv run python scripts/validate_engines.py
"""

from __future__ import annotations

import sys
import os
from collections import Counter

# 添加项目根目录到 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from foundation.hexagram_engine import HexagramEngine
from foundation.gan_zhi_engine import GanZhiEngine
from foundation.six_relation_engine import SixRelationEngine
from foundation.six_spirit_engine import SixSpiritEngine
from foundation.shi_ying_engine import ShiYingEngine
from foundation.element_engine import ElementEngine
from foundation.reference_data import (
    get_najia_rules,
    get_six_spirit_rules,
    get_palace_order,
    get_element_prosperity,
    get_najia_for_trigram,
)

# 地支五行对应（共享常量）
BRANCH_ELEMENT = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

# 宫位五行对应
PALACE_ELEMENT = {
    "乾宫": "金", "坤宫": "土", "震宫": "木", "巽宫": "木",
    "坎宫": "水", "离宫": "火", "艮宫": "土", "兑宫": "金",
}


def validate_najia() -> list[str]:
    """验证纳甲规则"""
    errors = []
    trigrams = ["乾", "坤", "震", "巽", "坎", "离", "艮", "兑"]

    # 天干五行对应
    STEM_ELEMENT = {
        "甲": "木", "乙": "木", "丙": "火", "丁": "火",
        "戊": "土", "己": "土", "庚": "金", "辛": "金",
        "壬": "水", "癸": "水",
    }

    for trigram in trigrams:
        lower_rules = get_najia_for_trigram(trigram, is_upper=False)
        upper_rules = get_najia_for_trigram(trigram, is_upper=True)

        for rules, is_upper in [(lower_rules, False), (upper_rules, True)]:
            for rule in rules:
                stem = rule["heavenly_stem"]
                branch = rule["earthly_branch"]
                element = rule["element"]

                # 验证天干地支是否合法
                if stem not in STEM_ELEMENT:
                    errors.append(f"纳甲: {trigram}{'外' if is_upper else '内'}爻{rule['position']} 天干无效: {stem}")
                if branch not in BRANCH_ELEMENT:
                    errors.append(f"纳甲: {trigram}{'外' if is_upper else '内'}爻{rule['position']} 地支无效: {branch}")

                # 验证五行与地支对应
                expected_element = BRANCH_ELEMENT.get(branch)
                if expected_element and element != expected_element:
                    errors.append(
                        f"纳甲: {trigram}{'外' if is_upper else '内'}爻{rule['position']} "
                        f"地支{branch}应为{expected_element}，实际{element}"
                    )

    return errors


def validate_six_spirits() -> list[str]:
    """验证六神排布"""
    errors = []
    valid_spirits = {"青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"}

    for day_stem in "甲乙丙丁戊己庚辛壬癸":
        rules = [
            r for r in get_six_spirit_rules()
            if r["day_stem"] == day_stem
        ]
        if len(rules) != 6:
            errors.append(f"六神: 日干{day_stem} 应有6条规则，实际{len(rules)}条")

        spirits = [r["spirit"] for r in sorted(rules, key=lambda r: r["line_position"])]
        for s in spirits:
            if s not in valid_spirits:
                errors.append(f"六神: 日干{day_stem} 六神名无效: {s}")

        # 验证六神不重复
        if len(set(spirits)) != 6:
            errors.append(f"六神: 日干{day_stem} 六神有重复: {spirits}")

    return errors


def validate_palace_order() -> list[str]:
    """验证八宫卦序"""
    errors = []
    palaces = get_palace_order()

    # 验证每个宫有8个卦
    palace_counts = Counter(p["palace"] for p in palaces)
    for palace, count in palace_counts.items():
        if count != 8:
            errors.append(f"宫序: {palace} 应有8卦，实际{count}卦")

    # 验证64个卦ID不重复
    ids = [p["hexagram_id"] for p in palaces]
    if len(set(ids)) != 64:
        errors.append(f"宫序: 卦ID有重复，共{len(ids)}个，去重后{len(set(ids))}个")

    # 验证世应位置和宫位五行
    for p in palaces:
        shi = p["shi_position"]
        ying = p["ying_position"]
        if not (1 <= shi <= 6) or not (1 <= ying <= 6):
            errors.append(f"宫序: {p['hexagram_name']} 世应位置异常: 世{shi} 应{ying}")

        expected_element = PALACE_ELEMENT.get(p["palace"])
        if expected_element and p["palace_element"] != expected_element:
            errors.append(
                f"宫序: {p['hexagram_name']} 宫位五行应为{expected_element}，实际{p['palace_element']}"
            )

    return errors


def validate_element_prosperity() -> list[str]:
    """验证五行旺衰表"""
    errors = []
    prosperity = get_element_prosperity()

    if len(prosperity) != 25:
        errors.append(f"旺衰: 应有25条，实际{len(prosperity)}条")

    valid_states = {"旺", "相", "休", "囚", "死"}
    for entry in prosperity:
        if entry["state"] not in valid_states:
            errors.append(f"旺衰: {entry['month_element']}月{entry['target_element']}爻 状态无效: {entry['state']}")

    return errors


def validate_hexagram_enrichment() -> list[str]:
    """验证卦象充实（通过API模块）"""
    errors = []

    try:
        from api.hexagram_enrich import enrich_hexagram
    except ImportError:
        errors.append("无法导入 hexagram_enrich 模块")
        return errors

    for hid in range(1, 65):
        try:
            hexagram = HexagramEngine.get_by_id(hid)
            enriched = enrich_hexagram(hexagram)

            # 验证每爻干支不同
            gz_list = [l.gan_zhi for l in enriched.lines]
            if len(set(gz_list)) < 6:
                errors.append(f"卦{hid} {enriched.name}: 干支有重复 {gz_list}")

            # 验证干支五行与爻五行一致
            for line in enriched.lines:
                if len(line.gan_zhi) >= 2:
                    branch = line.gan_zhi[1]
                    expected = BRANCH_ELEMENT.get(branch)
                    if expected and line.element.value != expected:
                        errors.append(
                            f"卦{hid} {enriched.name} 爻{line.position}: "
                            f"干支{line.gan_zhi}地支{branch}应为{expected}，爻五行{line.element.value}"
                        )

            # 验证世应位置合理
            shi_count = sum(1 for l in enriched.lines if l.is_shi)
            ying_count = sum(1 for l in enriched.lines if l.is_ying)
            if shi_count != 1:
                errors.append(f"卦{hid} {enriched.name}: 世爻数量异常: {shi_count}")
            if ying_count != 1:
                errors.append(f"卦{hid} {enriched.name}: 应爻数量异常: {ying_count}")

        except Exception as e:
            errors.append(f"卦{hid}: 充实失败: {e}")

    return errors


def main():
    """运行所有验证"""
    print("=" * 60)
    print("YI-AI 引擎输出验证")
    print("=" * 60)

    all_errors = []

    validators = [
        ("纳甲规则", validate_najia),
        ("六神排布", validate_six_spirits),
        ("八宫卦序", validate_palace_order),
        ("五行旺衰", validate_element_prosperity),
        ("卦象充实", validate_hexagram_enrichment),
    ]

    for name, validator in validators:
        print(f"\n--- {name} ---")
        try:
            errors = validator()
            if errors:
                print(f"  ❌ 发现 {len(errors)} 个问题:")
                for err in errors[:10]:  # 最多显示10个
                    print(f"    - {err}")
                if len(errors) > 10:
                    print(f"    ... 还有 {len(errors) - 10} 个问题")
            else:
                print(f"  ✅ 验证通过")
            all_errors.extend(errors)
        except Exception as e:
            print(f"  💥 验证器异常: {e}")
            all_errors.append(f"{name}: 验证器异常: {e}")

    print(f"\n{'=' * 60}")
    if all_errors:
        print(f"❌ 总计发现 {len(all_errors)} 个问题")
        return 1
    else:
        print("✅ 所有验证通过！")
        return 0


if __name__ == "__main__":
    sys.exit(main())
