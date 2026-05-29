"""国际化类型定义"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Language(str, Enum):
    """支持的语言"""
    ZH_CN = "zh-CN"    # 简体中文
    EN = "en"           # 英文
    JA = "ja"           # 日文
    KO = "ko"           # 韩文


# 语言显示名称
LANGUAGE_NAMES: dict[Language, str] = {
    Language.ZH_CN: "简体中文",
    Language.EN: "English",
    Language.JA: "日本語",
    Language.KO: "한국어",
}

# 默认语言
DEFAULT_LANGUAGE = Language.ZH_CN


@dataclass(frozen=True)
class TranslationEntry:
    """翻译条目

    Attributes:
        key: 翻译键（如 "hexagram.qian.name"）
        language: 目标语言
        value: 翻译值
    """
    key: str
    language: Language
    value: str


@dataclass(frozen=True)
class LocaleConfig:
    """语言区域配置

    Attributes:
        language: 语言
        date_format: 日期格式
        time_format: 时间格式
        direction: 文本方向（ltr/rtl）
    """
    language: Language
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M:%S"
    direction: str = "ltr"
