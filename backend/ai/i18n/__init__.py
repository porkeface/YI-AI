"""国际化模块

多语言支持框架，包括：
- Translator: 翻译管理器
- PromptTemplateManager: 多语言Prompt模板
- Language: 支持的语言枚举
"""

from ai.i18n.translator import Translator
from ai.i18n.prompt_templates import (
    PromptTemplateManager,
    load_builtin_templates,
)
from ai.i18n.types import (
    Language,
    LANGUAGE_NAMES,
    DEFAULT_LANGUAGE,
    TranslationEntry,
    LocaleConfig,
)

__all__ = [
    # 核心
    "Translator",
    "PromptTemplateManager",
    "load_builtin_templates",
    # 类型
    "Language",
    "LANGUAGE_NAMES",
    "DEFAULT_LANGUAGE",
    "TranslationEntry",
    "LocaleConfig",
]
