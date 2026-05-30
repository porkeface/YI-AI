"""将易经知识图谱写入 Neo4j

用法:
    cd backend
    python scripts/seed_neo4j.py

需要 Neo4j 运行在 NEO4J_URI (默认 bolt://localhost:7687)
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog

from ai.knowledge_graph import KnowledgeGraphBuilder, NodeType
from ai.adapters.neo4j_adapter import Neo4jGraphBackend

logger = structlog.get_logger()


def main() -> None:
    # 1. Build in-memory graph
    logger.info("building_knowledge_graph")
    graph = KnowledgeGraphBuilder.build()
    logger.info("graph_built", nodes=graph.node_count, edges=graph.edge_count)

    # 2. Connect to Neo4j
    backend = Neo4jGraphBackend()
    if not backend.is_available():
        logger.error("neo4j_not_available", hint="Start Neo4j first")
        return

    # 3. Transfer nodes
    node_count = 0
    for node in graph._nodes.values():
        backend.add_node(node)
        node_count += 1
        if node_count % 50 == 0:
            logger.info("nodes_progress", count=node_count)
    logger.info("nodes_seeded", total=node_count)

    # 4. Transfer edges
    edge_count = 0
    for edge in graph._edges:
        backend.add_edge(edge)
        edge_count += 1
        if edge_count % 100 == 0:
            logger.info("edges_progress", count=edge_count)
    logger.info("edges_seeded", total=edge_count)

    # 5. Verify
    for nt in NodeType:
        nodes = backend.query_by_type(nt)
        logger.info("type_count", node_type=nt.value, count=len(nodes))

    backend.close()
    logger.info("seed_complete", nodes=node_count, edges=edge_count)


if __name__ == "__main__":
    main()
