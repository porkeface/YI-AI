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
from ai.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


class AIInterpreter:
    """AI解释器 - 将规则结果翻译为自然语言

    核心职责：
    1. 接收规则分析结果
    2. 构建Prompt（含RAG知识参考）
    3. 调用LLM生成解释
    4. 返回自然语言解释
    """

    def __init__(
        self,
        llm_client: LLMClient,
        knowledge_base: KnowledgeBase | None = None,
    ) -> None:
        """初始化解释器

        Args:
            llm_client: LLM API客户端
            knowledge_base: 易经知识库（可选，启用RAG）
        """
        self.llm_client = llm_client
        self.prompt_builder = PromptBuilder()
        self.knowledge_base = knowledge_base

    def _retrieve_context(
        self, hexagram: Hexagram, question_type: str
    ) -> list[str] | None:
        """从知识库检索相关上下文

        Args:
            hexagram: 卦象数据
            question_type: 问题类型

        Returns:
            相关知识条目列表，无知识库时返回None
        """
        if self.knowledge_base is None:
            return None

        try:
            context = self.knowledge_base.retrieve(
                hexagram.name, question_type, max_entries=5
            )
            logger.info(
                "RAG检索完成，卦名=%s，返回%d条参考",
                hexagram.name,
                len(context),
            )
            return context if context else None
        except Exception:
            logger.warning("RAG检索失败，跳过知识参考", exc_info=True)
            return None

    async def interpret(
        self,
        question: str,
        hexagram: Hexagram,
        analysis: RuleAnalysisResult,
        question_type: str = "通用",
    ) -> str:
        """生成AI解释（非流式）

        流程：
        1. 构建上下文（卦象信息、规则分析结果）
        2. 调用RAG获取参考
        3. 调用LLM生成解释
        4. 返回自然语言解释

        Args:
            question: 用户的问题
            hexagram: 卦象数据
            analysis: 规则分析结果
            question_type: 问题类型（用于RAG检索）

        Returns:
            自然语言解释文本

        Raises:
            LLMError: LLM调用失败
        """
        rag_context = self._retrieve_context(hexagram, question_type)

        system_prompt = self.prompt_builder.build_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(
            question, hexagram, analysis, rag_context
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
        question_type: str = "通用",
    ) -> AsyncIterator[str]:
        """流式生成AI解释

        与interpret相同的流程，但使用流式API，
        逐步返回生成的文本片段。

        Args:
            question: 用户的问题
            hexagram: 卦象数据
            analysis: 规则分析结果
            question_type: 问题类型（用于RAG检索）

        Yields:
            逐步生成的文本片段

        Raises:
            LLMError: LLM调用失败
        """
        rag_context = self._retrieve_context(hexagram, question_type)

        system_prompt = self.prompt_builder.build_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(
            question, hexagram, analysis, rag_context
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
