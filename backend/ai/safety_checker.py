"""AI输出安全检查模块

对LLM生成的文本进行安全过滤，防止敏感或不当内容输出到前端。
MVP阶段使用关键词匹配+文本归一化，后续可升级为更智能的分类模型。
"""

from __future__ import annotations

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
    """归一化文本：去除空白/零宽字符、Unicode归一化、全角转半角"""
    # 去除零宽字符和各种不可见分隔符
    text = re.sub(r"[​-‏ - ⁠-⁩﻿]", "", text)
    # Unicode NFKC归一化（全角→半角，兼容字符→标准形态）
    text = unicodedata.normalize("NFKC", text)
    # 去除所有空白字符（防止"自 杀"绕过）
    text = re.sub(r"\s+", "", text)
    return text


# 敏感关键词分类
_SENSITIVE_CATEGORIES: dict[str, list[str]] = {
    "政治敏感": [
        "颠覆", "政变", "推翻政府", "分裂国家",
    ],
    "违法犯罪": [
        "自杀", "自残", "杀人", "投毒", "绑架",
        "诈骗方法", "洗钱", "贩毒",
    ],
    "迷信绝对化": [
        "命中注定", "必死无疑", "必有血光之灾",
        "天谴", "报应不爽",
    ],
}

# 需要替换的绝对化预测词汇
_ABSOLUTE_PREDICTIONS: list[tuple[str, str]] = [
    ("一定会", "较有可能"),
    ("必然会", "趋势上"),
    ("肯定能", "有机会"),
    ("绝对", "较大可能"),
    ("百分之百", "很大程度上"),
]

# 免责声明
DISCLAIMER = (
    "\n\n---\n"
    "*以上解读基于传统易学分析，仅供参考。"
    "重大决策请结合实际情况，必要时咨询专业人士。*"
)

# 最大输出长度（字符数）
MAX_OUTPUT_LENGTH = 3000


class SafetyCheckResult:
    """安全检查结果"""

    def __init__(
        self,
        text: str,
        is_safe: bool,
        warnings: list[str],
        modified: bool,
    ) -> None:
        self.text = text
        self.is_safe = is_safe
        self.warnings = warnings
        self.modified = modified


def check_safety(text: str) -> SafetyCheckResult:
    """检查AI输出的安全性

    流程：
    1. 检查是否包含敏感关键词（命中则标记不安全）
    2. 替换绝对化预测词汇
    3. 截断过长文本
    4. 追加免责声明

    Args:
        text: AI生成的原始文本

    Returns:
        SafetyCheckResult，包含处理后的文本和检查信息
    """
    warnings: list[str] = []
    modified = False
    is_safe = True

    # 0. 文本归一化（防止空白/Unicode绕过）
    normalized = _normalize_text(text)

    # 1. 敏感关键词检查（对归一化后的文本检测）
    for category, keywords in _SENSITIVE_CATEGORIES.items():
        for keyword in keywords:
            if keyword in normalized:
                is_safe = False
                warnings.append(f"包含{category}内容：'{keyword}'")
                logger.warning(
                    "sensitive_content_detected: category=%s keyword=%s",
                    category,
                    keyword,
                )

    # 如果检测到严重敏感内容，返回通用安全回复
    if not is_safe:
        safe_text = (
            "根据卦象分析，此卦提示您当前需要关注自身状态，"
            "建议保持平和心态，审慎行事。"
            "如需更详细的解读，请咨询专业人士。"
        )
        return SafetyCheckResult(
            text=safe_text + DISCLAIMER,
            is_safe=False,
            warnings=warnings,
            modified=True,
        )

    # 2. 替换绝对化预测
    for original, replacement in _ABSOLUTE_PREDICTIONS:
        if original in text:
            text = text.replace(original, replacement)
            modified = True
            warnings.append(f"已将绝对化表述'{original}'替换为'{replacement}'")

    # 3. 截断过长文本
    if len(text) > MAX_OUTPUT_LENGTH:
        # 在句号处截断
        truncated = text[:MAX_OUTPUT_LENGTH]
        last_period = truncated.rfind("。")
        if last_period > MAX_OUTPUT_LENGTH // 2:
            text = truncated[: last_period + 1]
        else:
            text = truncated + "..."
        modified = True
        warnings.append(f"文本过长已截断至{len(text)}字符")

    # 4. 追加免责声明
    text = text + DISCLAIMER

    return SafetyCheckResult(
        text=text,
        is_safe=True,
        warnings=warnings,
        modified=modified,
    )
