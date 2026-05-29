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

logger = structlog.get_logger()


class Neo4jGraphBackend:
    """Neo4j图谱后端

    实现 GraphBackend 协议。需要 neo4j 包：
      pip install neo4j

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
            driver = GraphDatabase.driver(self._uri, auth=(self._user, self._password))
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

    def add_node(self, node_id: str, node_type: str, properties: dict[str, Any]) -> None:
        driver = self._get_driver()
        query = (
            f"MERGE (n:{node_type} {{id: $id}}) "
            f"SET n += $props"
        )
        with driver.session() as session:
            session.run(query, id=node_id, props=properties)

    def add_edge(
        self, source_id: str, target_id: str, relation: str, properties: dict[str, Any]
    ) -> None:
        driver = self._get_driver()
        query = (
            "MATCH (a {id: $source}), (b {id: $target}) "
            f"MERGE (a)-[r:{relation}]->(b) "
            "SET r += $props"
        )
        with driver.session() as session:
            session.run(query, source=source_id, target=target_id, props=properties)

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        driver = self._get_driver()
        query = "MATCH (n {id: $id}) RETURN n"
        with driver.session() as session:
            result = session.run(query, id=node_id)
            record = result.single()
            if record:
                node = record["n"]
                return {"id": node["id"], **dict(node)}
        return None

    def get_neighbors(
        self, node_id: str, relation: str | None = None, direction: str = "both"
    ) -> list[dict[str, Any]]:
        driver = self._get_driver()
        if direction == "outgoing":
            arrow = "-[r]->"
        elif direction == "incoming":
            arrow = "<-[r]-"
        else:
            arrow = "-[r]-"

        if relation:
            query = f"MATCH (a {{id: $id}}){arrow}(b) WHERE type(r) = $rel RETURN b, type(r) as rel_type"
            params = {"id": node_id, "rel": relation}
        else:
            query = f"MATCH (a {{id: $id}}){arrow}(b) RETURN b, type(r) as rel_type"
            params = {"id": node_id}

        neighbors = []
        with driver.session() as session:
            result = session.run(query, **params)
            for record in result:
                node = record["b"]
                neighbors.append({
                    "id": node["id"],
                    "type": list(node.labels)[0] if node.labels else "UNKNOWN",
                    **dict(node),
                })
        return neighbors

    def find_path(
        self, source_id: str, target_id: str, max_depth: int = 3
    ) -> list[list[str]]:
        driver = self._get_driver()
        query = (
            "MATCH path = shortestPath("
            "(a {{id: $source}})-[*..{max_depth}]-(b {{id: $target}}))"
            "RETURN [n IN nodes(path) | n.id] as node_ids"
        ).format(max_depth=max_depth)
        paths = []
        with driver.session() as session:
            result = session.run(query, source=source_id, target=target_id)
            for record in result:
                paths.append(record["node_ids"])
        return paths

    def search_by_type(self, node_type: str) -> list[dict[str, Any]]:
        driver = self._get_driver()
        query = f"MATCH (n:{node_type}) RETURN n"
        nodes = []
        with driver.session() as session:
            result = session.run(query)
            for record in result:
                node = record["n"]
                nodes.append({"id": node["id"], **dict(node)})
        return nodes

    def close(self) -> None:
        if self._driver:
            self._driver.close()
            self._driver = None
