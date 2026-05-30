"""参考数据加载器

从JSON数据文件加载易学规则数据，供引擎使用。
数据文件位于 foundation/data/ 目录下。
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def _load_json(filename: str) -> Any:
    """加载JSON数据文件"""
    path = os.path.join(_DATA_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"数据文件不存在: {path}") from None
    except json.JSONDecodeError as e:
        raise ValueError(f"数据文件格式错误 {filename}: {e}") from e


@lru_cache(maxsize=1)
def get_line_texts() -> list[dict]:
    """获取384爻辞数据

    Returns:
        list of dict, each with keys:
        - hexagram_id: int
        - position: int (1-6)
        - yao_name: str (初九/六二 etc.)
        - yin_yang: str ("yang"/"yin")
        - text: str (爻辞)
        - image_text: str (小象辞)
    """
    return _load_json("line_texts.json")


@lru_cache(maxsize=1)
def _line_text_index() -> dict[tuple[int, int], dict]:
    """构建 (hexagram_id, position) -> dict 的索引"""
    return {(e["hexagram_id"], e["position"]): e for e in get_line_texts()}


@lru_cache(maxsize=1)
def get_tuan_texts() -> dict[str, str]:
    """获取64卦彖辞数据

    Returns:
        dict mapping hexagram_id (str) -> tuan_text (str)
    """
    return _load_json("tuan_texts.json")


@lru_cache(maxsize=1)
def get_najia_rules() -> list[dict]:
    """获取纳甲规则（48条）

    Returns:
        list of dict, each with keys:
        - trigram: str
        - position: int (1-6)
        - heavenly_stem: str
        - earthly_branch: str
        - element: str
        - is_upper: bool
    """
    return _load_json("najia_rules.json")


@lru_cache(maxsize=1)
def get_six_spirit_rules() -> list[dict]:
    """获取六神排布规则（60条）

    Returns:
        list of dict, each with keys:
        - day_stem: str
        - line_position: int (1-6)
        - spirit: str
    """
    return _load_json("six_spirit_rules.json")


@lru_cache(maxsize=1)
def get_palace_order() -> list[dict]:
    """获取八宫卦序（64条）

    Returns:
        list of dict, each with keys:
        - palace: str
        - palace_element: str
        - position_in_palace: int (0-7)
        - hexagram_name: str
        - hexagram_id: int
        - shi_position: int (1-6)
        - ying_position: int (1-6)
    """
    return _load_json("palace_order.json")


@lru_cache(maxsize=1)
def get_element_prosperity() -> list[dict]:
    """获取五行旺衰表（25条）

    Returns:
        list of dict, each with keys:
        - month_element: str
        - target_element: str
        - state: str (旺/相/休/囚/死)
    """
    return _load_json("element_prosperity.json")


def get_line_text(hexagram_id: int, position: int) -> dict | None:
    """获取指定爻的辞数据

    Args:
        hexagram_id: 卦序号 (1-64)
        position: 爻位置 (1-6)

    Returns:
        dict with text and image_text, or None if not found
    """
    return _line_text_index().get((hexagram_id, position))


def get_tuan_text(hexagram_id: int) -> str | None:
    """获取指定卦的彖辞

    Args:
        hexagram_id: 卦序号 (1-64)

    Returns:
        彖辞文本，或 None
    """
    return get_tuan_texts().get(str(hexagram_id))


def get_najia_for_trigram(trigram_name: str, is_upper: bool) -> list[dict]:
    """获取指定卦的纳甲规则

    Args:
        trigram_name: 卦名 (乾/坤/震/巽/坎/离/艮/兑)
        is_upper: 是否为外卦

    Returns:
        list of dict, sorted by position
    """
    rules = [
        r for r in get_najia_rules()
        if r["trigram"] == trigram_name and r["is_upper"] == is_upper
    ]
    return sorted(rules, key=lambda r: r["position"])


def get_palace_for_hexagram(hexagram_name: str) -> dict | None:
    """获取指定卦的宫位信息

    Args:
        hexagram_name: 卦名

    Returns:
        dict with palace info, or None
    """
    for entry in get_palace_order():
        if entry["hexagram_name"] == hexagram_name:
            return entry
    return None


def get_six_spirits_for_day(day_stem: str) -> list[dict]:
    """获取指定日干的六神排布

    Args:
        day_stem: 日干 (甲/乙/丙/丁/戊/己/庚/辛/壬/癸)

    Returns:
        list of dict, sorted by line_position
    """
    rules = [
        r for r in get_six_spirit_rules()
        if r["day_stem"] == day_stem
    ]
    return sorted(rules, key=lambda r: r["line_position"])


def get_prosperity_state(month_element: str, target_element: str) -> str | None:
    """获取五行旺衰状态

    Args:
        month_element: 月令五行
        target_element: 被判断的五行

    Returns:
        旺/相/休/囚/死, or None
    """
    for entry in get_element_prosperity():
        if entry["month_element"] == month_element and entry["target_element"] == target_element:
            return entry["state"]
    return None
