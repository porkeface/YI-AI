"""三路RAG融合检索模块

融合三种检索方式提升AI解释质量：
1. 向量检索：基于语义相似度（MVP用关键词匹配替代）
2. 图谱检索：基于知识图谱关系
3. 规则检索：基于规则引擎分析结果

融合算法：RRF (Reciprocal Rank Fusion)
- 对每个检索源的结果按排名打分
- 分数 = 1 / (k + rank)，k=60（常数）
- 合并所有源的分数，按总分排序

用法：
    rag = RAGFusion(knowledge_base, knowledge_graph)
    context = rag.retrieve("乾", "事业", analysis_result)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from typing import Any

from ai.knowledge_base import KnowledgeBase
from ai.knowledge_graph import KnowledgeGraph
from foundation.types import Hexagram, RuleAnalysisResult

logger = logging.getLogger(__name__)

# RRF常数
RRF_K = 60


@dataclass(frozen=True)
class RetrievalResult:
    """检索结果

    Attributes:
        content: 检索到的文本内容
        source: 来源（vector/graph/rule）
        score: RRF融合分数
        rank: 在本源中的排名
    """
    content: str
    source: str
    score: float
    rank: int


class RAGFusion:
    """三路RAG融合检索

    整合向量检索、图谱检索、规则检索，
    使用RRF算法融合排序，返回最相关的上下文。
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase | None = None,
        knowledge_graph: KnowledgeGraph | None = None,
        vector_backend: Any | None = None,
        embedding_service: Any | None = None,
    ) -> None:
        """初始化RAG融合检索

        Args:
            knowledge_base: 易经知识库（向量检索的MVP替代）
            knowledge_graph: 知识图谱
            vector_backend: 向量检索后端（可选，如 QdrantVectorBackend）
            embedding_service: Embedding 服务（可选，如 EmbeddingService）
        """
        self.knowledge_base = knowledge_base or KnowledgeBase(
            vector_backend=vector_backend,
            embedding_service=embedding_service,
        )
        self.knowledge_graph = knowledge_graph or KnowledgeGraph()
        self._vector_backend = vector_backend
        self._embedding_service = embedding_service

    def retrieve(
        self,
        hexagram: Hexagram,
        question_type: str,
        analysis: RuleAnalysisResult,
        max_results: int = 8,
    ) -> list[str]:
        """三路融合检索

        流程：
        1. 向量检索（关键词匹配）：获取相关易经原文
        2. 图谱检索：获取卦的关系网络和上下文
        3. 规则检索：获取分析结果中的关键信息
        4. RRF融合排序
        5. 返回top-N结果

        Args:
            hexagram: 卦象数据
            question_type: 问题类型
            analysis: 规则分析结果
            max_results: 最大返回结果数

        Returns:
            融合后的上下文文本列表
        """
        # 三路检索
        vector_results = self._vector_search(hexagram.name, question_type)
        graph_results = self._graph_search(hexagram.name)
        rule_results = self._rule_search(hexagram, analysis)

        # RRF融合
        fused = self._rrf_fuse(vector_results, graph_results, rule_results)

        # 去重并取top-N
        seen: set[str] = set()
        unique_results: list[RetrievalResult] = []
        for result in fused:
            # 简单去重：前30字符
            key = result.content[:30]
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
                if len(unique_results) >= max_results:
                    break

        logger.info(
            "rag_fusion_complete",
            vector=len(vector_results),
            graph=len(graph_results),
            rule=len(rule_results),
            fused=len(unique_results),
        )

        return [r.content for r in unique_results]

    def _vector_search(
        self, hexagram_name: str, question_type: str
    ) -> list[RetrievalResult]:
        """向量检索（有向量后端时用语义检索，否则降级到关键词匹配）

        Args:
            hexagram_name: 卦名
            question_type: 问题类型

        Returns:
            检索结果列表
        """
        if self._vector_backend and self._embedding_service:
            try:
                query = f"{hexagram_name} {question_type}"
                vector = self._embedding_service.embed(query)
                results = self._vector_backend.search(vector, top_k=5)
                return [
                    RetrievalResult(
                        content=r.get("content", ""),
                        source="vector",
                        score=r.get("score", 0.0),
                        rank=i,
                    )
                    for i, r in enumerate(results)
                    if r.get("content")
                ]
            except Exception as e:
                logger.warning(f"Vector search failed, falling back: {e}")

        # 降级到关键词匹配
        entries = self.knowledge_base.retrieve(
            hexagram_name, question_type, max_entries=5
        )
        return [
            RetrievalResult(
                content=entry,
                source="vector",
                score=0.0,  # RRF会重新计算
                rank=i,
            )
            for i, entry in enumerate(entries)
        ]

    def _graph_search(self, hexagram_name: str) -> list[RetrievalResult]:
        """图谱检索

        获取卦的关系网络上下文。

        Args:
            hexagram_name: 卦名

        Returns:
            检索结果列表
        """
        results: list[RetrievalResult] = []

        # 卦的完整上下文
        context = self.knowledge_graph.get_hexagram_context(hexagram_name)
        if context:
            results.append(RetrievalResult(
                content=context,
                source="graph",
                score=0.0,
                rank=0,
            ))

        # 相关卦
        related = self.knowledge_graph.get_related_hexagrams(
            hexagram_name, max_results=3
        )
        for i, name in enumerate(related):
            related_context = self.knowledge_graph.get_hexagram_context(name)
            if related_context:
                results.append(RetrievalResult(
                    content=f"【相关卦·{name}】\n{related_context}",
                    source="graph",
                    score=0.0,
                    rank=i + 1,
                ))

        return results

    def _rule_search(
        self, hexagram: Hexagram, analysis: RuleAnalysisResult
    ) -> list[RetrievalResult]:
        """规则检索

        从规则分析结果中提取关键信息作为上下文。

        Args:
            hexagram: 卦象数据
            analysis: 规则分析结果

        Returns:
            检索结果列表
        """
        results: list[RetrievalResult] = []

        # 用神信息
        results.append(RetrievalResult(
            content=f"用神：{analysis.yong_shen.value}，旺衰：{analysis.prosperity.value}",
            source="rule",
            score=0.0,
            rank=0,
        ))

        # 动爻信息
        if analysis.moving_lines:
            moving_desc = "、".join(
                f"{p}爻" for p in analysis.moving_lines
            )
            results.append(RetrievalResult(
                content=f"动爻：{moving_desc}（变化的关键点）",
                source="rule",
                score=0.0,
                rank=1,
            ))

        # 关系描述
        for i, rel in enumerate(analysis.relationships[:3]):
            results.append(RetrievalResult(
                content=rel,
                source="rule",
                score=0.0,
                rank=i + 2,
            ))

        # 结论
        verdict = analysis.verdict
        results.append(RetrievalResult(
            content=(
                f"综合判断：{verdict.overall}，"
                f"力量{verdict.strength}%，"
                f"趋势{verdict.trend}，"
                f"置信度{verdict.confidence}%"
            ),
            source="rule",
            score=0.0,
            rank=len(results),
        ))

        return results

    def _rrf_fuse(
        self,
        *result_groups: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """RRF (Reciprocal Rank Fusion) 融合算法

        对每个检索源的结果按排名计算RRF分数，
        合并所有源的结果并按总分排序。

        RRF分数 = sum(1 / (k + rank_i)) for each source i

        Args:
            *result_groups: 各检索源的结果列表

        Returns:
            融合后按分数降序排列的结果列表
        """
        # 计算每个内容的RRF分数
        content_scores: dict[str, float] = {}
        content_results: dict[str, RetrievalResult] = {}

        for results in result_groups:
            for result in results:
                key = result.content[:50]  # 用前50字符作为去重key
                rrf_score = 1.0 / (RRF_K + result.rank + 1)

                if key in content_scores:
                    content_scores[key] += rrf_score
                else:
                    content_scores[key] = rrf_score
                    content_results[key] = result

        # 按RRF分数排序
        sorted_keys = sorted(
            content_scores.keys(),
            key=lambda k: content_scores[k],
            reverse=True,
        )

        return [
            RetrievalResult(
                content=content_results[k].content,
                source=content_results[k].source,
                score=content_scores[k],
                rank=content_results[k].rank,
            )
            for k in sorted_keys
        ]
