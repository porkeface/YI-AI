"""Qdrant向量检索适配器

实现 VectorBackend 协议，连接 Qdrant 向量数据库。
部署 Qdrant 后可通过环境变量启用：
  QDRANT_URL=http://localhost:6333
  QDRANT_COLLECTION=yiai_knowledge
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import structlog

logger = structlog.get_logger()


class QdrantVectorBackend:
    """Qdrant向量检索后端

    实现 VectorBackend 协议。需要 qdrant-client 包：
      pip install qdrant-client

    使用方式：
      backend = QdrantVectorBackend()
      if backend.is_available():
          kb = KnowledgeBase(vector_backend=backend)
    """

    def __init__(self) -> None:
        self._client: Any = None
        self._url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        self._collection = os.environ.get("QDRANT_COLLECTION", "yiai_knowledge")
        self._dimension = 384  # 默认使用 BAAI/bge-small-en-v1.5
        self._timeout = 5.0  # 连接超时（秒）

    @staticmethod
    def _doc_id_to_uuid(doc_id: str) -> str:
        """将 doc_id 转换为确定性 UUID（基于内容哈希）"""
        return str(uuid.uuid5(uuid.NAMESPACE_URL, doc_id))

    def is_available(self) -> bool:
        """检查 Qdrant 是否可用（带超时）"""
        try:
            from qdrant_client import QdrantClient

            client = QdrantClient(url=self._url, timeout=self._timeout)
            client.get_collections()
            return True
        except Exception as e:
            logger.info("qdrant_not_available", error=str(e))
            return False

    def _get_client(self) -> Any:
        if self._client is None:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(url=self._url, timeout=self._timeout)
        return self._client

    def ensure_collection(self) -> None:
        """确保集合存在"""
        from qdrant_client.models import Distance, VectorParams

        client = self._get_client()
        collections = [c.name for c in client.get_collections().collections]
        if self._collection not in collections:
            client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(
                    size=self._dimension, distance=Distance.COSINE
                ),
            )
            logger.info("qdrant_collection_created", collection=self._collection)

    def upsert(
        self, doc_id: str, vector: list[float], payload: dict[str, Any]
    ) -> None:
        """插入或更新文档向量（使用确定性 UUID 避免冲突）"""
        from qdrant_client.models import PointStruct

        client = self._get_client()
        point_id = self._doc_id_to_uuid(doc_id)
        client.upsert(
            collection_name=self._collection,
            points=[
                PointStruct(id=point_id, vector=vector, payload={**payload, "doc_id": doc_id})
            ],
        )

    def search(
        self, query_vector: list[float], top_k: int = 5
    ) -> list[dict[str, Any]]:
        """向量相似度检索"""
        client = self._get_client()
        # 兼容 qdrant-client >= 1.7（query_points 替代 search）
        if hasattr(client, "query_points"):
            response = client.query_points(
                collection_name=self._collection,
                query=query_vector,
                limit=top_k,
                with_payload=True,
            )
            hits = response.points
        else:
            hits = client.search(
                collection_name=self._collection,
                query_vector=query_vector,
                limit=top_k,
            )
        return [
            {
                "id": str(hit.id),
                "score": hit.score,
                **(hit.payload or {}),
            }
            for hit in hits
        ]

    def delete(self, doc_id: str) -> None:
        """删除文档向量"""
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        client = self._get_client()
        client.delete(
            collection_name=self._collection,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="doc_id", match=MatchValue(value=doc_id)
                    )
                ]
            ),
        )

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
