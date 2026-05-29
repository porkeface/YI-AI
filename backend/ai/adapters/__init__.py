"""存储适配器

提供可替换的存储后端实现。
"""

from ai.adapters.neo4j_adapter import Neo4jGraphBackend
from ai.adapters.qdrant_adapter import QdrantVectorBackend

__all__ = ["Neo4jGraphBackend", "QdrantVectorBackend"]
