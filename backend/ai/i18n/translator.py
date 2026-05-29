"""翻译管理器

管理多语言翻译文本，支持：
- 翻译注册和查询
- 语言检测
- 回退机制（缺失翻译回退到默认语言）
- 批量翻译加载
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from ai.i18n.types import (
    DEFAULT_LANGUAGE,
    LANGUAGE_NAMES,
    Language,
    TranslationEntry,
)

logger = logging.getLogger(__name__)


class Translator:
    """翻译管理器

    classmethod-only API — 所有翻译存储在模块级变量中。
    线程安全 — 使用锁保护共享状态。
    """

    # 模块级状态
    _translations: dict[str, dict[Language, str]] = {}
    _lock = threading.Lock()

    @classmethod
    def register(cls, key: str, language: Language, value: str) -> None:
        """注册翻译

        Args:
            key: 翻译键
            language: 目标语言
            value: 翻译值
        """
        with cls._lock:
            if key not in cls._translations:
                cls._translations[key] = {}
            cls._translations[key][language] = value

    @classmethod
    def register_batch(cls, entries: tuple[TranslationEntry, ...]) -> int:
        """批量注册翻译

        Args:
            entries: 翻译条目列表

        Returns:
            成功注册的数量
        """
        count = 0
        for entry in entries:
            cls.register(entry.key, entry.language, entry.value)
            count += 1
        return count

    @classmethod
    def translate(
        cls,
        key: str,
        language: Language = DEFAULT_LANGUAGE,
        **kwargs: Any,
    ) -> str:
        """翻译

        支持占位符替换：translate("greeting", Language.EN, name="World")
        翻译文本中使用 {name} 作为占位符。

        Args:
            key: 翻译键
            language: 目标语言
            **kwargs: 占位符参数

        Returns:
            翻译文本，未找到返回键名
        """
        with cls._lock:
            entry = cls._translations.get(key)

        if entry is None:
            logger.debug("translation_missing: key=%s", key)
            return key

        # 优先返回目标语言
        value = entry.get(language)

        # 回退到默认语言
        if value is None and language != DEFAULT_LANGUAGE:
            value = entry.get(DEFAULT_LANGUAGE)
            if value:
                logger.debug(
                    "translation_fallback: %s -> %s",
                    language.value, DEFAULT_LANGUAGE.value,
                )

        if value is None:
            return key

        # 占位符替换
        if kwargs:
            try:
                value = value.format(**kwargs)
            except (KeyError, ValueError):
                pass

        return value

    @classmethod
    def has_translation(
        cls,
        key: str,
        language: Language = DEFAULT_LANGUAGE,
    ) -> bool:
        """检查是否有翻译

        Args:
            key: 翻译键
            language: 目标语言

        Returns:
            是否存在翻译
        """
        with cls._lock:
            entry = cls._translations.get(key)
            if entry is None:
                return False
            return language in entry or DEFAULT_LANGUAGE in entry

    @classmethod
    def get_supported_languages(cls, key: str) -> tuple[Language, ...]:
        """获取翻译键支持的语言列表

        Args:
            key: 翻译键

        Returns:
            支持的语言列表
        """
        with cls._lock:
            entry = cls._translations.get(key)
            if entry is None:
                return ()
            return tuple(entry.keys())

    @classmethod
    def detect_language(cls, text: str) -> Language:
        """检测文本语言

        基于字符范围的简单检测：
        - 包含CJK字符 → 中文
        - 包含平假名/片假名 → 日文
        - 包含韩文字符 → 韩文
        - 其他 → 英文

        Args:
            text: 输入文本

        Returns:
            检测到的语言
        """
        has_cjk = False
        has_hiragana = False
        has_katakana = False
        has_hangul = False

        for char in text:
            cp = ord(char)
            # CJK统一汉字
            if 0x4E00 <= cp <= 0x9FFF:
                has_cjk = True
            # 平假名
            elif 0x3040 <= cp <= 0x309F:
                has_hiragana = True
            # 片假名
            elif 0x30A0 <= cp <= 0x30FF:
                has_katakana = True
            # 韩文
            elif 0xAC00 <= cp <= 0xD7AF:
                has_hangul = True

        if has_hiragana or has_katakana:
            return Language.JA
        if has_hangul:
            return Language.KO
        if has_cjk:
            return Language.ZH_CN
        return Language.EN

    @classmethod
    def count(cls) -> int:
        """获取翻译键总数"""
        with cls._lock:
            return len(cls._translations)

    @classmethod
    def clear(cls) -> None:
        """清空所有翻译（用于测试）"""
        with cls._lock:
            cls._translations.clear()
