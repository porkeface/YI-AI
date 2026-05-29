"""AI解释器模块

将规则分析结果翻译成自然语言解释。
是AI模块的核心入口。
"""

from __future__ import annotations

import logging
from typing import AsyncIterator

from foundation.types import Hexagram, RuleAnalysisResult
from ai.llm_client import LLMClient, LLMError
from ai.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class AIInterpreter:
    """AI解释器 - 将规则结果翻译为自然语言

    核心职责：
    1. 接收规则分析结果
    2. 构建Prompt
    3. 调用LLM生成解释
    4. 返回自然语言解释
    """

    def __init__(self, llm_client: LLMClient) -> None:
        """初始化解释器

        Args:
            llm_client: LLM API客户端
        """
        self.llm_client = llm_client
        self.prompt_builder = PromptBuilder()

    async def interpret(
        self,
        question: str,
        hexagram: Hexagram,
        analysis: RuleAnalysisResult,
    ) -> str:
        """生成AI解释（非流式）

        流程：
        1. 构建上下文（卦象信息、规则分析结果）
        2. 调用RAG获取参考（MVP阶段跳过）
        3. 调用LLM生成解释
        4. 返回自然语言解释

        Args:
            question: 用户的问题
            hexagram: 卦象数据
            analysis: 规则分析结果

        Returns:
            自然语言解释文本

        Raises:
            LLMError: LLM调用失败
        """
        system_prompt = self.prompt_builder.build_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(
            question, hexagram, analysis
        )

        logger.info(
            "开始生成AI解释，卦名=%s，问题=%s",
            hexagram.name,
            question[:30],
        )

        try:
            result = await self.llm_client.chat(system_prompt, user_prompt)
            logger.info("AI解释生成完成，长度=%d", len(result))
            return result
        except LLMError:
            logger.error("AI解释生成失败", exc_info=True)
            raise

    async def interpret_stream(
        self,
        question: str,
        hexagram: Hexagram,
        analysis: RuleAnalysisResult,
    ) -> AsyncIterator[str]:
        """流式生成AI解释

        与interpret相同的流程，但使用流式API，
        逐步返回生成的文本片段。

        Args:
            question: 用户的问题
            hexagram: 卦象数据
            analysis: 规则分析结果

        Yields:
            逐步生成的文本片段

        Raises:
            LLMError: LLM调用失败
        """
        system_prompt = self.prompt_builder.build_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(
            question, hexagram, analysis
        )

        logger.info(
            "开始流式生成AI解释，卦名=%s，问题=%s",
            hexagram.name,
            question[:30],
        )

        try:
            async for chunk in self.llm_client.chat_stream(
                system_prompt, user_prompt
            ):
                yield chunk
        except LLMError:
            logger.error("AI流式解释生成失败", exc_info=True)
            raise
