"""国际化模块测试

覆盖：翻译管理器、Prompt模板、语言检测。
"""

from __future__ import annotations

import pytest
from ai.i18n.types import (
    Language,
    LANGUAGE_NAMES,
    DEFAULT_LANGUAGE,
    TranslationEntry,
    LocaleConfig,
)
from ai.i18n.translator import Translator
from ai.i18n.prompt_templates import (
    PromptTemplateManager,
    load_builtin_templates,
)


class TestTranslator:
    """翻译管理器测试"""

    def setup_method(self):
        Translator.clear()

    def test_register_and_translate(self):
        """注册并翻译"""
        Translator.register("hello", Language.EN, "Hello")
        Translator.register("hello", Language.ZH_CN, "你好")
        assert Translator.translate("hello", Language.EN) == "Hello"
        assert Translator.translate("hello", Language.ZH_CN) == "你好"

    def test_translate_fallback(self):
        """缺失翻译回退到默认语言"""
        Translator.register("test", Language.ZH_CN, "测试")
        result = Translator.translate("test", Language.EN)
        assert result == "测试"

    def test_translate_missing(self):
        """无翻译返回键名"""
        result = Translator.translate("nonexistent", Language.EN)
        assert result == "nonexistent"

    def test_translate_with_kwargs(self):
        """占位符替换"""
        Translator.register(
            "greeting", Language.EN, "Hello, {name}!"
        )
        result = Translator.translate(
            "greeting", Language.EN, name="World"
        )
        assert result == "Hello, World!"

    def test_register_batch(self):
        """批量注册"""
        entries = (
            TranslationEntry("a", Language.EN, "A"),
            TranslationEntry("a", Language.ZH_CN, "甲"),
            TranslationEntry("b", Language.EN, "B"),
        )
        count = Translator.register_batch(entries)
        assert count == 3
        assert Translator.count() == 2

    def test_has_translation(self):
        """检查翻译是否存在"""
        Translator.register("test", Language.ZH_CN, "测试")
        assert Translator.has_translation("test", Language.ZH_CN) is True
        assert Translator.has_translation("test", Language.EN) is True  # fallback
        assert Translator.has_translation("missing") is False

    def test_get_supported_languages(self):
        """获取支持的语言"""
        Translator.register("multi", Language.EN, "EN")
        Translator.register("multi", Language.JA, "JA")
        langs = Translator.get_supported_languages("multi")
        assert Language.EN in langs
        assert Language.JA in langs

    def test_detect_language_chinese(self):
        """检测中文"""
        assert Translator.detect_language("你好世界") == Language.ZH_CN

    def test_detect_language_english(self):
        """检测英文"""
        assert Translator.detect_language("Hello world") == Language.EN

    def test_detect_language_japanese(self):
        """检测日文"""
        assert Translator.detect_language("こんにちは") == Language.JA

    def test_detect_language_korean(self):
        """检测韩文"""
        assert Translator.detect_language("안녕하세요") == Language.KO

    def test_count(self):
        """计数"""
        assert Translator.count() == 0
        Translator.register("a", Language.EN, "A")
        assert Translator.count() == 1


class TestPromptTemplateManager:
    """Prompt模板管理器测试"""

    def setup_method(self):
        Translator.clear()
        load_builtin_templates()

    def test_load_builtin_templates(self):
        """加载内置模板"""
        assert Translator.count() >= 3

    def test_get_system_prompt_zh(self):
        """获取中文系统Prompt"""
        prompt = PromptTemplateManager.get_system_prompt(Language.ZH_CN)
        assert "易经" in prompt

    def test_get_system_prompt_en(self):
        """获取英文系统Prompt"""
        prompt = PromptTemplateManager.get_system_prompt(Language.EN)
        assert "I Ching" in prompt

    def test_build_user_prompt(self):
        """构建用户Prompt"""
        prompt = PromptTemplateManager.build_user_prompt(
            "乾为天", "事业如何", "分析结果", Language.ZH_CN
        )
        assert "乾为天" in prompt
        assert "事业如何" in prompt

    def test_get_disclaimer(self):
        """获取免责声明"""
        disclaimer = PromptTemplateManager.get_disclaimer(Language.ZH_CN)
        assert "声明" in disclaimer

    def test_multilingual_consistency(self):
        """多语言一致性"""
        for lang in Language:
            system = PromptTemplateManager.get_system_prompt(lang)
            assert system != "interpret.system"  # 不应返回键名
            disclaimer = PromptTemplateManager.get_disclaimer(lang)
            assert disclaimer != "safety.disclaimer"


class TestI18nTypes:
    """国际化类型测试"""

    def test_language_enum(self):
        """语言枚举"""
        assert Language.ZH_CN.value == "zh-CN"
        assert Language.EN.value == "en"
        assert Language.JA.value == "ja"
        assert Language.KO.value == "ko"

    def test_language_names(self):
        """语言名称"""
        assert LANGUAGE_NAMES[Language.ZH_CN] == "简体中文"
        assert LANGUAGE_NAMES[Language.EN] == "English"

    def test_translation_entry_frozen(self):
        """TranslationEntry 不可变"""
        entry = TranslationEntry("key", Language.EN, "value")
        with pytest.raises(AttributeError):
            entry.value = "new"  # type: ignore

    def test_locale_config_defaults(self):
        """LocaleConfig 默认值"""
        config = LocaleConfig(language=Language.ZH_CN)
        assert config.date_format == "%Y-%m-%d"
        assert config.direction == "ltr"
