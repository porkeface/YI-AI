"""Neo4j图谱适配器

实现 GraphBackend 协议，连接 Neo4j 数据库。
部署 Neo4j 后可通过环境变量启用：
  NEO4J_URI=bolt://localhost:7687
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=xxx
"""

from __future__ import annotations

import os
from typing import Any

import structlog

from ai.knowledge_graph import (
    GraphBackend,
    GraphNode,
    GraphEdge,
    NodeType,
    RelationType,
)

logger = structlog.get_logger()


def _to_graph_node(record_node: Any, labels: list[str]) -> GraphNode:
    """将 Neo4j 节点记录转换为 GraphNode"""
    node_type_str = labels[0] if labels else "concept"
    try:
        node_type = NodeType(node_type_str)
    except ValueError:
        node_type = NodeType.CONCEPT
    return GraphNode(
        id=record_node["id"],
        node_type=node_type,
        name=record_node.get("name", ""),
        properties={
            k: str(v)
            for k, v in record_node.items()
            if k not in ("id", "name")
        },
    )


class Neo4jGraphBackend:
    """Neo4j图谱后端 - 实现 GraphBackend 协议

    使用方式：
      backend = Neo4jGraphBackend()
      if backend.is_available():
          graph = KnowledgeGraph(backend=backend)
    """

    def __init__(self) -> None:
        self._driver: Any = None
        self._uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self._user = os.environ.get("NEO4J_USER", "neo4j")
        self._password = os.environ.get("NEO4J_PASSWORD", "")

    def is_available(self) -> bool:
        """检查 Neo4j 是否可用"""
        try:
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver(
                self._uri, auth=(self._user, self._password)
            )
            driver.verify_connectivity()
            driver.close()
            return True
        except Exception as e:
            logger.info("neo4j_not_available", error=str(e))
            return False

    def _get_driver(self) -> Any:
        if self._driver is None:
            from neo4j import GraphDatabase

            self._driver = GraphDatabase.driver(
                self._uri, auth=(self._user, self._password)
            )
        return self._driver

    def add_node(self, node: GraphNode) -> None:
        """添加或更新节点"""
        driver = self._get_driver()
        props = {"id": node.id, "name": node.name, **node.properties}
        # 验证 node_type 来自枚举，防止注入
        node_type = node.node_type.value
        assert node_type in [t.value for t in NodeType], f"Invalid node type: {node_type}"
        query = f"MERGE (n:{node_type} {{id: $id}}) SET n += $props"
        with driver.session() as session:
            session.run(query, id=node.id, props=props)

    def add_edge(self, edge: GraphEdge) -> None:
        """添加或更新边"""
        driver = self._get_driver()
        props = dict(edge.properties)
        # 验证 relation 来自枚举，防止注入
        rel_type = edge.relation.value
        assert rel_type in [r.value for r in RelationType], f"Invalid relation type: {rel_type}"
        query = (
            "MATCH (a {id: $source}), (b {id: $target}) "
            f"MERGE (a)-[r:{rel_type}]->(b) "
            "SET r += $props"
        )
        with driver.session() as session:
            session.run(
                query,
                source=edge.source_id,
                target=edge.target_id,
                props=props,
            )

    def get_node(self, node_id: str) -> GraphNode | None:
        """根据ID获取节点"""
        driver = self._get_driver()
        query = "MATCH (n {id: $id}) RETURN n, labels(n) as labels"
        with driver.session() as session:
            result = session.run(query, id=node_id)
            record = result.single()
            if record:
                return _to_graph_node(record["n"], record["labels"])
        return None

    def get_neighbors(
        self, node_id: str, relation: RelationType | None = None
    ) -> tuple[GraphNode, ...]:
        """获取邻居节点"""
        driver = self._get_driver()
        if relation:
            rel_val = relation.value
            assert rel_val in [r.value for r in RelationType], f"Invalid relation type: {rel_val}"
            query = (
                f"MATCH (a {{id: $id}})-[r:{rel_val}]-(b) "
                "RETURN b, labels(b) as labels"
            )
        else:
            query = (
                "MATCH (a {id: $id})-[r]-(b) "
                "RETURN b, labels(b) as labels"
            )

        neighbors: list[GraphNode] = []
        with driver.session() as session:
            result = session.run(query, id=node_id)
            for record in result:
                neighbors.append(
                    _to_graph_node(record["b"], record["labels"])
                )
        return tuple(neighbors)

    def get_edges(
        self,
        source_id: str | None = None,
        target_id: str | None = None,
        relation: RelationType | None = None,
    ) -> tuple[GraphEdge, ...]:
        """按条件查询边"""
        driver = self._get_driver()
        conditions: list[str] = []
        params: dict[str, Any] = {}

        if source_id:
            conditions.append("a.id = $source_id")
            params["source_id"] = source_id
        if target_id:
            conditions.append("b.id = $target_id")
            params["target_id"] = target_id

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        if relation:
            rel_val = relation.value
            assert rel_val in [r.value for r in RelationType], f"Invalid relation type: {rel_val}"
            rel_filter = f":{rel_val}"
        else:
            rel_filter = ""

        query = (
            f"MATCH (a)-[r{rel_filter}]->(b) {where} "
            "RETURN a.id as source, b.id as target, "
            "type(r) as rel_type, properties(r) as props"
        )

        edges: list[GraphEdge] = []
        with driver.session() as session:
            result = session.run(query, **params)
            for record in result:
                try:
                    rel_type = RelationType(record["rel_type"])
                except ValueError:
                    rel_type = RelationType.RELATES_TO
                edges.append(
                    GraphEdge(
                        source_id=record["source"],
                        target_id=record["target"],
                        relation=rel_type,
                        properties={
                            k: str(v)
                            for k, v in (record["props"] or {}).items()
                        },
                    )
                )
        return tuple(edges)

    def query_by_type(self, node_type: NodeType) -> tuple[GraphNode, ...]:
        """按类型查询节点"""
        driver = self._get_driver()
        nt_val = node_type.value
        assert nt_val in [t.value for t in NodeType], f"Invalid node type: {nt_val}"
        query = f"MATCH (n:{nt_val}) RETURN n, labels(n) as labels"
        nodes: list[GraphNode] = []
        with driver.session() as session:
            result = session.run(query)
            for record in result:
                nodes.append(
                    _to_graph_node(record["n"], record["labels"])
                )
        return tuple(nodes)

    def find_path(
        self, start_id: str, end_id: str, max_depth: int = 3
    ) -> tuple[tuple[str, ...], ...]:
        """查找最短路径"""
        driver = self._get_driver()
        query = (
            "MATCH path = shortestPath("
            f"(a {{id: $start}})-[*..{max_depth}]-(b {{id: $end}})) "
            "RETURN [n IN nodes(path) | n.id] as node_ids"
        )

        paths: list[tuple[str, ...]] = []
        with driver.session() as session:
            result = session.run(query, start=start_id, end=end_id)
            for record in result:
                paths.append(tuple(record["node_ids"]))
        return tuple(paths)

    def close(self) -> None:
        """关闭连接"""
        if self._driver:
            self._driver.close()
            self._driver = None
