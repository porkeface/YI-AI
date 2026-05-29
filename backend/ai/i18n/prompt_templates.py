"""多语言Prompt模板

提供不同语言的AI解释Prompt模板。
"""

from __future__ import annotations

import logging
from typing import Any

from ai.i18n.types import DEFAULT_LANGUAGE, Language
from ai.i18n.translator import Translator

logger = logging.getLogger(__name__)


# ---- 内置Prompt模板 ----

_BUILTIN_TEMPLATES: dict[str, dict[Language, str]] = {
    "interpret.system": {
        Language.ZH_CN: (
            "你是一位精通易经的AI助手。请根据以下卦象信息，"
            "用通俗易懂的语言为用户解读。"
            "注意：你只负责解释卦象含义，不做任何预测。"
        ),
        Language.EN: (
            "You are an AI assistant well-versed in the I Ching. "
            "Based on the following hexagram information, "
            "provide an interpretation in clear, accessible language. "
            "Note: You only explain hexagram meanings, not make predictions."
        ),
        Language.JA: (
            "あなたは易経に精通したAIアシスタントです。"
            "以下の卦の情報に基づき、分かりやすい言葉で解釈を提供してください。"
            "注意：卦の意味の解釈のみ行い、予測は行いません。"
        ),
        Language.KO: (
            "당신은 역경에 정통한 AI 어시스턴트입니다. "
            "다음 괘 정보를 바탕으로 이해하기 쉬운 언어로 해석을 제공하세요. "
            "주의: 괘 의미 해석만 하고 예측은 하지 않습니다."
        ),
    },
    "interpret.user": {
        Language.ZH_CN: (
            "卦象：{hexagram_name}\n"
            "问题：{question}\n"
            "规则分析：{rule_analysis}\n\n"
            "请为用户提供详细的卦象解读。"
        ),
        Language.EN: (
            "Hexagram: {hexagram_name}\n"
            "Question: {question}\n"
            "Rule Analysis: {rule_analysis}\n\n"
            "Please provide a detailed interpretation for the user."
        ),
        Language.JA: (
            "卦：{hexagram_name}\n"
            "質問：{question}\n"
            "規則分析：{rule_analysis}\n\n"
            "ユーザーに詳細な解釈を提供してください。"
        ),
        Language.KO: (
            "괘: {hexagram_name}\n"
            "질문: {question}\n"
            "규칙 분석: {rule_analysis}\n\n"
            "사용자에게 상세한 해석을 제공하세요."
        ),
    },
    "safety.disclaimer": {
        Language.ZH_CN: (
            "【声明】本系统基于易经变化学进行结构化分析，"
            "不提供任何形式的预测或决策建议。"
            "分析结果仅供参考，请结合实际情况自行判断。"
        ),
        Language.EN: (
            "[Disclaimer] This system provides structured analysis "
            "based on I Ching change theory. It does not provide "
            "predictions or decision advice. Results are for "
            "reference only; please use your own judgment."
        ),
        Language.JA: (
            "【声明】本システムは易経の変化学に基づく構造化分析を提供し、"
            "いかなる予測や意思決定の助言も行いません。"
            "分析結果は参考のみです。实际情况と照らし合わせてご判断ください。"
        ),
        Language.KO: (
            "[고지] 본 시스템은 역경 변화학에 기반한 구조화 분석을 제공하며, "
            "어떤 형태의 예측이나 의사결정 조언도 하지 않습니다. "
            "분석 결과는 참고용이며,实际情况과 대조하여自行判断하시기 바랍니다."
        ),
    },
}


def load_builtin_templates() -> int:
    """加载内置Prompt模板到翻译管理器

    Returns:
        加载的模板数量
    """
    count = 0
    for key, lang_map in _BUILTIN_TEMPLATES.items():
        for lang, value in lang_map.items():
            Translator.register(key, lang, value)
            count += 1
    return count


class PromptTemplateManager:
    """Prompt模板管理器

    classmethod-only API — 提供多语言Prompt构建功能。
    """

    @classmethod
    def get_system_prompt(
        cls,
        language: Language = DEFAULT_LANGUAGE,
    ) -> str:
        """获取系统Prompt

        Args:
            language: 目标语言

        Returns:
            系统Prompt文本
        """
        return Translator.translate("interpret.system", language)

    @classmethod
    def build_user_prompt(
        cls,
        hexagram_name: str,
        question: str,
        rule_analysis: str,
        language: Language = DEFAULT_LANGUAGE,
    ) -> str:
        """构建用户Prompt

        Args:
            hexagram_name: 卦名
            question: 用户问题
            rule_analysis: 规则分析结果
            language: 目标语言

        Returns:
            格式化的用户Prompt
        """
        return Translator.translate(
            "interpret.user",
            language,
            hexagram_name=hexagram_name,
            question=question,
            rule_analysis=rule_analysis,
        )

    @classmethod
    def get_disclaimer(
        cls,
        language: Language = DEFAULT_LANGUAGE,
    ) -> str:
        """获取免责声明

        Args:
            language: 目标语言

        Returns:
            免责声明文本
        """
        return Translator.translate("safety.disclaimer", language)
