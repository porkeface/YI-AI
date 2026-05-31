"""Agent工具集

定义Agent可以调用的工具函数。
所有工具都是确定性的，不经过LLM。
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from foundation.types import Hexagram, RuleAnalysisResult
from foundation.hexagram_engine import HexagramEngine
from foundation.element_engine import ElementEngine
from rule_engine.inference_engine import InferenceEngine

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolResult:
    """工具调用结果"""
    tool_name: str
    success: bool
    data: dict
    error: str | None = None


class AgentTools:
    """Agent工具集

    提供Agent可以调用的确定性计算工具。
    """

    @staticmethod
    def query_hexagram(hexagram_name: str) -> ToolResult:
        """查询卦象完整信息"""
        try:
            hexagram = HexagramEngine.get_by_name(hexagram_name)
            return ToolResult(
                tool_name="query_hexagram",
                success=True,
                data={
                    "name": hexagram.name,
                    "id": hexagram.id,
                    "judgment": hexagram.judgment,
                    "image": hexagram.image,
                    "element": hexagram.element.value,
                    "upper_trigram": hexagram.upper_trigram.name.value,
                    "lower_trigram": hexagram.lower_trigram.name.value,
                },
            )
        except Exception as e:
            return ToolResult(
                tool_name="query_hexagram",
                success=False,
                data={},
                error=str(e),
            )

    @staticmethod
    def calculate_five_elements(element_a: str, element_b: str) -> ToolResult:
        """计算五行生克关系"""
        try:
            from foundation.types import Element
            ea = Element(element_a)
            eb = Element(element_b)
            relation = ElementEngine.get_relation(ea, eb)
            return ToolResult(
                tool_name="calculate_five_elements",
                success=True,
                data={"element_a": element_a, "element_b": element_b, "relation": relation},
            )
        except Exception as e:
            return ToolResult(
                tool_name="calculate_five_elements",
                success=False,
                data={},
                error=str(e),
            )

    @staticmethod
    def get_hexagram_transformations(hexagram_name: str) -> ToolResult:
        """获取卦变信息（错综互）"""
        try:
            hexagram = HexagramEngine.get_by_name(hexagram_name)
            result: dict = {"name": hexagram_name}

            try:
                opposite = HexagramEngine.get_opposite(hexagram)
                result["opposite"] = opposite.name
            except Exception:
                logger.warning("get_opposite_failed", hexagram=hexagram_name, exc_info=True)
                result["opposite"] = None

            try:
                reversed_h = HexagramEngine.get_reversed(hexagram)
                result["reversed"] = reversed_h.name
            except Exception:
                logger.warning("get_reversed_failed", hexagram=hexagram_name, exc_info=True)
                result["reversed"] = None

            try:
                interlock = HexagramEngine.get_interlock(hexagram)
                result["interlock"] = interlock.name
            except Exception:
                logger.warning("get_interlock_failed", hexagram=hexagram_name, exc_info=True)
                result["interlock"] = None

            return ToolResult(
                tool_name="get_hexagram_transformations",
                success=True,
                data=result,
            )
        except Exception as e:
            return ToolResult(
                tool_name="get_hexagram_transformations",
                success=False,
                data={},
                error=str(e),
            )

    @staticmethod
    def simulate_evolution_chain(
        hexagram_name: str,
        analysis: RuleAnalysisResult | None = None,
        month_branch: str = "子",
        steps: int = 3,
    ) -> ToolResult:
        """模拟卦象演化链

        Args:
            hexagram_name: 卦名
            analysis: 规则分析结果（可选，为None时自动执行真实分析）
            month_branch: 月建地支（analysis为None时用于分析）
            steps: 推演深度
        """
        try:
            hexagram = HexagramEngine.get_by_name(hexagram_name)

            if analysis is None:
                # Perform real analysis instead of using hardcoded dummy data
                from rule_engine.analyzer import Analyzer
                analysis = Analyzer.analyze(hexagram, "通用", month_branch)

            result = InferenceEngine.infer(hexagram, analysis, max_depth=steps)
            return ToolResult(
                tool_name="simulate_evolution_chain",
                success=True,
                data={
                    "source": result.source_hexagram,
                    "path_count": len(result.paths),
                    "paths": [
                        {
                            "final": p.final_hexagram,
                            "trend": p.overall_trend,
                            "probability": p.path_probability,
                            "summary": p.summary,
                        }
                        for p in result.paths
                    ],
                    "recommended": result.recommended_path.final_hexagram,
                    "summary": result.summary,
                },
            )
        except Exception as e:
            return ToolResult(
                tool_name="simulate_evolution_chain",
                success=False,
                data={},
                error=str(e),
            )

    @staticmethod
    def analyze_prosperity(element: str, month_branch: str) -> ToolResult:
        """分析五行旺衰"""
        try:
            from foundation.types import Element
            elem = Element(element)
            state = ElementEngine.judge_prosperity(elem, month_branch)
            return ToolResult(
                tool_name="analyze_prosperity",
                success=True,
                data={"element": element, "month_branch": month_branch, "state": state.value},
            )
        except Exception as e:
            return ToolResult(
                tool_name="analyze_prosperity",
                success=False,
                data={},
                error=str(e),
            )
