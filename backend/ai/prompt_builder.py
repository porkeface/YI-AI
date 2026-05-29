"""Prompt构建器模块

构建发送给LLM的系统提示词和用户提示词。
将结构化的卦象数据和规则分析结果转换为LLM可理解的自然语言描述。
"""

from __future__ import annotations

from foundation.types import (
    Element,
    Hexagram,
    Line,
    ProsperityState,
    RuleAnalysisResult,
    SixRelation,
    Verdict,
)


class PromptBuilder:
    """Prompt构建器

    负责将六爻排盘的结构化数据组装成LLM的输入Prompt。
    """

    def build_system_prompt(self) -> str:
        """构建系统提示词

        Returns:
            系统提示词文本
        """
        return (
            "你是一位精通易学的AI助手。你的任务是将六爻排盘的规则分析结果"
            "翻译成通俗易懂的现代汉语解释。\n\n"
            "核心原则：\n"
            "1. 你只负责\"解释\"规则结果，不负责\"计算\"\n"
            "2. 解释要通俗易懂，避免专业术语堆砌\n"
            "3. 要结合用户的具体问题来解释\n"
            "4. 要给出实用的建议\n"
            "5. 不要做绝对化的预测，用\"趋势\"、\"可能性\"等词语\n"
            "6. 要有温度，不要冷冰冰的\n\n"
            "输出格式：\n"
            "1. 首先用一句话概括卦象的核心含义\n"
            "2. 然后详细解释各爻的关系和含义\n"
            "3. 最后给出实用建议\n\n"
            "注意：不要使用\"算命\"、\"注定\"等词语，"
            "用\"趋势\"、\"分析\"、\"参考\"等中性词。"
        )

    def build_user_prompt(
        self,
        question: str,
        hexagram: Hexagram,
        analysis: RuleAnalysisResult,
    ) -> str:
        """构建用户提示词

        将卦象信息和规则分析结果转换为自然语言描述，
        作为用户输入发送给LLM。

        Args:
            question: 用户的问题
            hexagram: 卦象数据
            analysis: 规则分析结果

        Returns:
            用户提示词文本
        """
        parts: list[str] = []

        # 1. 用户问题
        parts.append(f"【用户问题】{question}")

        # 2. 卦象基本信息
        parts.append(self._format_hexagram_info(hexagram))

        # 3. 六爻详情
        parts.append(self._format_lines(hexagram.lines))

        # 4. 规则分析结果
        parts.append(self._format_analysis(analysis))

        # 5. 指令
        parts.append(
            "请根据以上信息，为用户生成一段通俗易懂的卦象解释。"
            "要结合用户的具体问题，给出实用的建议。"
        )

        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # 内部格式化方法
    # ------------------------------------------------------------------

    def _format_hexagram_info(self, hexagram: Hexagram) -> str:
        """格式化卦象基本信息

        Args:
            hexagram: 卦象数据

        Returns:
            格式化后的文本
        """
        return (
            f"【卦象信息】\n"
            f"- 卦名：{hexagram.name}\n"
            f"- 上卦：{hexagram.upper_trigram.name.value}"
            f"（{hexagram.upper_trigram.nature}，"
            f"{hexagram.upper_trigram.element.value}）\n"
            f"- 下卦：{hexagram.lower_trigram.name.value}"
            f"（{hexagram.lower_trigram.nature}，"
            f"{hexagram.lower_trigram.element.value}）\n"
            f"- 卦辞：{hexagram.judgment}\n"
            f"- 象辞：{hexagram.image}"
        )

    def _format_lines(
        self, lines: tuple[Line, Line, Line, Line, Line, Line]
    ) -> str:
        """格式化六爻详情

        Args:
            lines: 六爻数据

        Returns:
            格式化后的文本
        """
        header = "【六爻详情】"
        rows: list[str] = []

        for line in lines:
            # 位置名称
            pos_name = self._position_name(line.position)

            # 阴阳
            yin_yang_str = "阳" if line.yin_yang.value == "yang" else "阴"

            # 动爻标记
            moving_str = "（动爻）" if line.is_moving else ""

            # 世应标记
            role_str = ""
            if line.is_shi:
                role_str = " [世]"
            elif line.is_ying:
                role_str = " [应]"

            rows.append(
                f"- {pos_name}：{line.gan_zhi} "
                f"{yin_yang_str}爻 {line.element.value} "
                f"{line.six_relation.value}{moving_str}{role_str}"
            )

        return header + "\n" + "\n".join(rows)

    def _format_analysis(self, analysis: RuleAnalysisResult) -> str:
        """格式化规则分析结果

        Args:
            analysis: 规则分析结果

        Returns:
            格式化后的文本
        """
        parts: list[str] = ["【规则分析结果】"]

        # 用神
        parts.append(f"- 用神：{analysis.yong_shen.value}")

        # 动爻
        if analysis.moving_lines:
            moving_str = "、".join(
                f"第{pos}爻" for pos in analysis.moving_lines
            )
            parts.append(f"- 动爻：{moving_str}")

        # 旺衰
        parts.append(f"- 用神旺衰：{analysis.prosperity.value}")

        # 关系描述
        if analysis.relationships:
            parts.append("- 分析要点：")
            for rel in analysis.relationships:
                parts.append(f"  · {rel}")

        # 结论
        parts.append(self._format_verdict(analysis.verdict))

        return "\n".join(parts)

    def _format_verdict(self, verdict: Verdict) -> str:
        """格式化占卜结论

        Args:
            verdict: 占卜结论

        Returns:
            格式化后的文本
        """
        return (
            f"- 综合判断：{verdict.overall}\n"
            f"- 力量强度：{verdict.strength}/100\n"
            f"- 趋势：{verdict.trend}\n"
            f"- 置信度：{verdict.confidence}%"
        )

    @staticmethod
    def _position_name(position: int) -> str:
        """将爻位数字转换为中文名称

        Args:
            position: 爻位（1-6）

        Returns:
            中文名称
        """
        names = {1: "初爻", 2: "二爻", 3: "三爻",
                 4: "四爻", 5: "五爻", 6: "上爻"}
        return names.get(position, f"第{position}爻")
