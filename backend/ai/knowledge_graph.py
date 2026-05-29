"""易经知识图谱模块

构建易学知识图谱，包含：
- 64卦节点
- 384爻节点
- 8经卦节点
- 5五行节点
- 关系：卦-爻、卦-卦（错/综/互/变）、爻-五行、卦-五行、卦-宫

MVP阶段使用内存图结构，接口设计兼容Neo4j迁移。
后续可通过替换GraphBackend切换到Neo4j。
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

logger = logging.getLogger(__name__)


# ============================================================================
# 类型定义
# ============================================================================

class NodeType(str, Enum):
    """节点类型"""
    HEXAGRAM = "hexagram"      # 六爻卦
    LINE = "line"              # 爻
    TRIGRAM = "trigram"        # 经卦
    ELEMENT = "element"        # 五行
    PALACE = "palace"          # 宫
    CONCEPT = "concept"        # 概念（如"事业"、"财运"等）


class RelationType(str, Enum):
    """关系类型"""
    CONTAINS = "contains"              # 卦-爻（包含）
    OPPOSITE = "opposite"              # 错卦
    REVERSED = "reversed"              # 综卦
    INTERLOCK = "interlock"            # 互卦
    CHANGES_TO = "changes_to"          # 变卦（动爻变化）
    HAS_ELEMENT = "has_element"        # 五行属性
    BELONGS_TO = "belongs_to"          # 属于宫
    UPPER_TRIGRAM = "upper_trigram"    # 上卦
    LOWER_TRIGRAM = "lower_trigram"    # 下卦
    GENERATES = "generates"            # 五行相生
    OVERCOMES = "overcomes"            # 五行相克
    RELATES_TO = "relates_to"          # 概念关联


@dataclass(frozen=True)
class GraphNode:
    """图节点

    Attributes:
        id: 节点唯一标识
        node_type: 节点类型
        name: 节点名称
        properties: 附加属性
    """
    id: str
    node_type: NodeType
    name: str
    properties: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    """图边（关系）

    Attributes:
        source_id: 源节点ID
        target_id: 目标节点ID
        relation: 关系类型
        properties: 附加属性
    """
    source_id: str
    target_id: str
    relation: RelationType
    properties: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphQueryResult:
    """图查询结果

    Attributes:
        nodes: 匹配的节点列表
        edges: 相关的边列表
        paths: 路径（节点ID序列）
    """
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    paths: tuple[tuple[str, ...], ...] = ()


# ============================================================================
# 图后端协议（兼容Neo4j迁移）
# ============================================================================

class GraphBackend(Protocol):
    """图存储后端协议"""

    def add_node(self, node: GraphNode) -> None: ...
    def add_edge(self, edge: GraphEdge) -> None: ...
    def get_node(self, node_id: str) -> GraphNode | None: ...
    def get_neighbors(
        self, node_id: str, relation: RelationType | None = None
    ) -> tuple[GraphNode, ...]: ...
    def get_edges(
        self, source_id: str | None = None,
        target_id: str | None = None,
        relation: RelationType | None = None,
    ) -> tuple[GraphEdge, ...]: ...
    def query_by_type(self, node_type: NodeType) -> tuple[GraphNode, ...]: ...
    def find_path(
        self, start_id: str, end_id: str, max_depth: int = 3
    ) -> tuple[tuple[str, ...], ...]: ...
    def is_available(self) -> bool: ...
    def close(self) -> None: ...


# ============================================================================
# 内存图实现
# ============================================================================

class InMemoryGraph:
    """内存图存储

    MVP阶段的图实现，接口兼容GraphBackend协议。
    """

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[GraphEdge] = []
        self._adjacency: dict[str, list[int]] = {}  # node_id -> edge indices

    def add_node(self, node: GraphNode) -> None:
        self._nodes[node.id] = node
        if node.id not in self._adjacency:
            self._adjacency[node.id] = []

    def add_edge(self, edge: GraphEdge) -> None:
        idx = len(self._edges)
        self._edges.append(edge)
        self._adjacency.setdefault(edge.source_id, []).append(idx)
        self._adjacency.setdefault(edge.target_id, []).append(idx)

    def get_node(self, node_id: str) -> GraphNode | None:
        return self._nodes.get(node_id)

    def get_neighbors(
        self, node_id: str, relation: RelationType | None = None
    ) -> tuple[GraphNode, ...]:
        neighbors: list[GraphNode] = []
        for idx in self._adjacency.get(node_id, []):
            edge = self._edges[idx]
            if relation and edge.relation != relation:
                continue
            other_id = (
                edge.target_id if edge.source_id == node_id
                else edge.source_id
            )
            other = self._nodes.get(other_id)
            if other:
                neighbors.append(other)
        return tuple(neighbors)

    def get_edges(
        self, source_id: str | None = None,
        target_id: str | None = None,
        relation: RelationType | None = None,
    ) -> tuple[GraphEdge, ...]:
        result: list[GraphEdge] = []
        for edge in self._edges:
            if source_id and edge.source_id != source_id:
                continue
            if target_id and edge.target_id != target_id:
                continue
            if relation and edge.relation != relation:
                continue
            result.append(edge)
        return tuple(result)

    def query_by_type(self, node_type: NodeType) -> tuple[GraphNode, ...]:
        return tuple(
            n for n in self._nodes.values() if n.node_type == node_type
        )

    def find_path(
        self, start_id: str, end_id: str, max_depth: int = 3
    ) -> tuple[tuple[str, ...], ...]:
        """BFS寻路"""
        if start_id not in self._nodes or end_id not in self._nodes:
            return ()

        paths: list[tuple[str, ...]] = []
        queue: list[tuple[str, list[str]]] = [(start_id, [start_id])]
        visited: set[str] = {start_id}

        while queue:
            current, path = queue.pop(0)
            if len(path) > max_depth + 1:
                continue

            if current == end_id and len(path) > 1:
                paths.append(tuple(path))
                if len(paths) >= 5:  # 最多5条路径
                    break
                continue

            for idx in self._adjacency.get(current, []):
                edge = self._edges[idx]
                other = (
                    edge.target_id if edge.source_id == current
                    else edge.source_id
                )
                if other not in visited or other == end_id:
                    visited.add(other)
                    queue.append((other, path + [other]))

        return tuple(paths)

    def is_available(self) -> bool:
        """内存图始终可用"""
        return True

    def close(self) -> None:
        """内存图无需清理"""
        pass

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)


# ============================================================================
# 知识图谱构建器
# ============================================================================

class KnowledgeGraphBuilder:
    """易经知识图谱构建器

    从HexagramEngine数据自动构建完整的易学知识图谱。
    """

    @staticmethod
    def build() -> InMemoryGraph:
        """构建完整的易学知识图谱

        Returns:
            填充好的内存图实例
        """
        from foundation.hexagram_engine import HexagramEngine
        from foundation.types import Element

        graph = InMemoryGraph()

        # 1. 添加五行节点
        elements = KnowledgeGraphBuilder._add_elements(graph)

        # 2. 添加八卦节点
        trigrams = KnowledgeGraphBuilder._add_trigrams(graph, elements)

        # 3. 添加64卦节点和关系
        KnowledgeGraphBuilder._add_hexagrams(graph, elements, trigrams)

        logger.info(
            "knowledge_graph_built",
            nodes=graph.node_count,
            edges=graph.edge_count,
        )

        return graph

    @staticmethod
    def _add_elements(graph: InMemoryGraph) -> dict[str, str]:
        """添加五行节点和相生相克关系"""
        from foundation.types import Element

        element_names = {
            Element.METAL: "金",
            Element.WOOD: "木",
            Element.WATER: "水",
            Element.FIRE: "火",
            Element.EARTH: "土",
        }

        # 相生：木生火，火生土，土生金，金生水，水生木
        generates = {
            Element.WOOD: Element.FIRE,
            Element.FIRE: Element.EARTH,
            Element.EARTH: Element.METAL,
            Element.METAL: Element.WATER,
            Element.WATER: Element.WOOD,
        }

        # 相克：木克土，土克水，水克火，火克金，金克木
        overcomes = {
            Element.WOOD: Element.EARTH,
            Element.EARTH: Element.WATER,
            Element.WATER: Element.FIRE,
            Element.FIRE: Element.METAL,
            Element.METAL: Element.WOOD,
        }

        id_map: dict[str, str] = {}
        for elem, name in element_names.items():
            node_id = f"element:{elem.value}"
            graph.add_node(GraphNode(
                id=node_id,
                node_type=NodeType.ELEMENT,
                name=name,
                properties={"value": elem.value},
            ))
            id_map[elem.value] = node_id

        # 添加相生关系
        for source, target in generates.items():
            graph.add_edge(GraphEdge(
                source_id=f"element:{source.value}",
                target_id=f"element:{target.value}",
                relation=RelationType.GENERATES,
            ))

        # 添加相克关系
        for source, target in overcomes.items():
            graph.add_edge(GraphEdge(
                source_id=f"element:{source.value}",
                target_id=f"element:{target.value}",
                relation=RelationType.OVERCOMES,
            ))

        return id_map

    @staticmethod
    def _add_trigrams(
        graph: InMemoryGraph, elements: dict[str, str]
    ) -> dict[str, str]:
        """添加八卦节点"""
        from foundation.trigram_engine import TrigramEngine

        id_map: dict[str, str] = {}
        trigrams = TrigramEngine.get_all_trigrams()

        for tri in trigrams:
            node_id = f"trigram:{tri.name.value}"
            graph.add_node(GraphNode(
                id=node_id,
                node_type=NodeType.TRIGRAM,
                name=tri.name.value,
                properties={
                    "nature": tri.nature,
                    "direction": tri.direction,
                    "family": tri.family,
                    "animal": tri.animal,
                },
            ))
            id_map[tri.name.value] = node_id

            # 关联五行
            element_id = elements.get(tri.element.value)
            if element_id:
                graph.add_edge(GraphEdge(
                    source_id=node_id,
                    target_id=element_id,
                    relation=RelationType.HAS_ELEMENT,
                ))

        return id_map

    @staticmethod
    def _add_hexagrams(
        graph: InMemoryGraph,
        elements: dict[str, str],
        trigrams: dict[str, str],
    ) -> None:
        """添加64卦节点和所有关系"""
        from foundation.hexagram_engine import HexagramEngine

        hexagrams = HexagramEngine.get_all_hexagrams()

        for hexagram in hexagrams:
            hex_id = f"hexagram:{hexagram.id}"

            # 添加卦节点
            graph.add_node(GraphNode(
                id=hex_id,
                node_type=NodeType.HEXAGRAM,
                name=hexagram.name,
                properties={
                    "id": str(hexagram.id),
                    "judgment": hexagram.judgment[:50],
                    "element": hexagram.element.value,
                },
            ))

            # 关联五行
            element_id = elements.get(hexagram.element.value)
            if element_id:
                graph.add_edge(GraphEdge(
                    source_id=hex_id,
                    target_id=element_id,
                    relation=RelationType.HAS_ELEMENT,
                ))

            # 关联上下卦
            upper_id = trigrams.get(hexagram.upper_trigram.name.value)
            lower_id = trigrams.get(hexagram.lower_trigram.name.value)
            if upper_id:
                graph.add_edge(GraphEdge(
                    source_id=hex_id,
                    target_id=upper_id,
                    relation=RelationType.UPPER_TRIGRAM,
                ))
            if lower_id:
                graph.add_edge(GraphEdge(
                    source_id=hex_id,
                    target_id=lower_id,
                    relation=RelationType.LOWER_TRIGRAM,
                ))

            # 添加爻节点
            for line in hexagram.lines:
                line_id = f"line:{hexagram.id}:{line.position}"
                graph.add_node(GraphNode(
                    id=line_id,
                    node_type=NodeType.LINE,
                    name=f"{hexagram.name}·{line.position}爻",
                    properties={
                        "position": str(line.position),
                        "yin_yang": line.yin_yang.value,
                        "element": line.element.value,
                        "six_relation": line.six_relation.value,
                        "gan_zhi": line.gan_zhi,
                    },
                ))
                graph.add_edge(GraphEdge(
                    source_id=hex_id,
                    target_id=line_id,
                    relation=RelationType.CONTAINS,
                ))

            # 卦关系（错/综/互）
            KnowledgeGraphBuilder._add_hexagram_relations(
                graph, hexagram, hex_id
            )

    @staticmethod
    def _add_hexagram_relations(
        graph: InMemoryGraph,
        hexagram: object,
        hex_id: str,
    ) -> None:
        """添加卦之间的关系（错卦、综卦、互卦）"""
        from foundation.hexagram_engine import HexagramEngine

        try:
            opposite = HexagramEngine.get_opposite(hexagram)
            graph.add_edge(GraphEdge(
                source_id=hex_id,
                target_id=f"hexagram:{opposite.id}",
                relation=RelationType.OPPOSITE,
            ))
        except (ValueError, IndexError):
            pass

        try:
            reversed_hex = HexagramEngine.get_reversed(hexagram)
            graph.add_edge(GraphEdge(
                source_id=hex_id,
                target_id=f"hexagram:{reversed_hex.id}",
                relation=RelationType.REVERSED,
            ))
        except (ValueError, IndexError):
            pass

        try:
            interlock = HexagramEngine.get_interlock(hexagram)
            graph.add_edge(GraphEdge(
                source_id=hex_id,
                target_id=f"hexagram:{interlock.id}",
                relation=RelationType.INTERLOCK,
            ))
        except (ValueError, IndexError):
            pass


# ============================================================================
# 图谱查询API
# ============================================================================

class KnowledgeGraph:
    """知识图谱查询接口

    提供高级查询方法，供RAG和AI模块使用。
    支持后端切换：有 Neo4j 时用 Neo4j，否则用内存图。
    """

    def __init__(self, backend: GraphBackend | None = None) -> None:
        """初始化知识图谱

        Args:
            backend: 图存储后端（可选）。未提供时自动尝试 Neo4j，不可用则用内存图。
        """
        if backend is not None:
            self._backend = backend
        else:
            # 尝试使用 Neo4j
            neo4j_backend = None
            if os.environ.get("NEO4J_URI"):
                try:
                    from ai.adapters.neo4j_adapter import Neo4jGraphBackend

                    nb = Neo4jGraphBackend()
                    if nb.is_available():
                        neo4j_backend = nb
                        logger.info("neo4j_backend_enabled")
                except Exception as e:
                    logger.debug(f"Neo4j not available, using in-memory graph: {e}")

            self._backend = neo4j_backend or InMemoryGraph()

        # 如果使用内存后端且为空，自动构建
        if isinstance(self._backend, InMemoryGraph) and self._backend.node_count == 0:
            self._backend = KnowledgeGraphBuilder.build()

        # 兼容属性：内部用 _graph 访问
        self._graph = self._backend

    def get_hexagram_context(self, hexagram_name: str) -> str:
        """获取卦的完整图谱上下文

        包含：卦的基本信息、五行关系、关联卦、爻信息。

        Args:
            hexagram_name: 卦名

        Returns:
            格式化的图谱上下文文本
        """
        # 查找卦节点
        hex_nodes = [
            n for n in self._graph.query_by_type(NodeType.HEXAGRAM)
            if n.name == hexagram_name
        ]
        if not hex_nodes:
            return ""

        hex_node = hex_nodes[0]
        hex_id = hex_node.id
        parts: list[str] = []

        # 基本信息
        parts.append(f"【{hexagram_name}】")
        parts.append(f"五行：{hex_node.properties.get('element', '未知')}")
        parts.append(f"卦辞：{hex_node.properties.get('judgment', '')}")

        # 关联卦
        for rel_type, label in [
            (RelationType.OPPOSITE, "错卦"),
            (RelationType.REVERSED, "综卦"),
            (RelationType.INTERLOCK, "互卦"),
        ]:
            neighbors = self._graph.get_neighbors(hex_id, rel_type)
            for n in neighbors:
                parts.append(f"{label}：{n.name}")

        # 上下卦
        upper = self._graph.get_neighbors(hex_id, RelationType.UPPER_TRIGRAM)
        lower = self._graph.get_neighbors(hex_id, RelationType.LOWER_TRIGRAM)
        if upper:
            parts.append(f"上卦：{upper[0].name}（{upper[0].properties.get('nature', '')}）")
        if lower:
            parts.append(f"下卦：{lower[0].name}（{lower[0].properties.get('nature', '')}）")

        return "\n".join(parts)

    def get_related_hexagrams(
        self, hexagram_name: str, max_results: int = 5
    ) -> list[str]:
        """获取与指定卦相关的卦名列表

        Args:
            hexagram_name: 卦名
            max_results: 最大返回数

        Returns:
            相关卦名列表
        """
        hex_nodes = [
            n for n in self._graph.query_by_type(NodeType.HEXAGRAM)
            if n.name == hexagram_name
        ]
        if not hex_nodes:
            return []

        hex_id = hex_nodes[0].id
        related: list[str] = []

        for rel_type in [
            RelationType.OPPOSITE,
            RelationType.REVERSED,
            RelationType.INTERLOCK,
        ]:
            neighbors = self._graph.get_neighbors(hex_id, rel_type)
            for n in neighbors:
                if n.name not in related and n.name != hexagram_name:
                    related.append(n.name)
                    if len(related) >= max_results:
                        return related

        return related

    def get_element_context(self, element: str) -> str:
        """获取五行的图谱上下文

        Args:
            element: 五行名称（金/木/水/火/土）

        Returns:
            五行关系描述
        """
        elem_id = f"element:{element}"
        elem_node = self._graph.get_node(elem_id)
        if not elem_node:
            return ""

        parts: list[str] = [f"五行·{element}："]

        # 相生
        generates = self._graph.get_neighbors(elem_id, RelationType.GENERATES)
        if generates:
            parts.append(f"  生：{', '.join(n.name for n in generates)}")

        # 相克
        overcomes = self._graph.get_neighbors(elem_id, RelationType.OVERCOMES)
        if overcomes:
            parts.append(f"  克：{', '.join(n.name for n in overcomes)}")

        return "\n".join(parts)

    def search_by_keyword(self, keyword: str) -> tuple[GraphNode, ...]:
        """按关键词搜索节点名称

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的节点元组
        """
        results: list[GraphNode] = []
        for node_type in NodeType:
            for node in self._graph.query_by_type(node_type):
                if keyword in node.name or keyword in node.id:
                    results.append(node)
                    if len(results) >= 10:
                        return tuple(results)
        return tuple(results)

    @property
    def stats(self) -> dict[str, int]:
        """图谱统计信息"""
        node_counts: dict[str, int] = {}
        for node_type in NodeType:
            nodes = self._graph.query_by_type(node_type)
            node_counts[node_type.value] = len(nodes)
        return {
            "total_nodes": sum(node_counts.values()),
            "total_edges": len(self._graph.get_edges()),
            **node_counts,
        }
