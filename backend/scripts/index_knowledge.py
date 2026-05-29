"""将易经知识库索引到 Qdrant 向量数据库

用法:
    cd backend
    python scripts/index_knowledge.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog

from ai.adapters.qdrant_adapter import QdrantVectorBackend
from ai.embedding import EmbeddingService
from ai.knowledge_base import _HEXAGRAM_KNOWLEDGE

logger = structlog.get_logger()


def main() -> None:
    backend = QdrantVectorBackend()
    if not backend.is_available():
        logger.error("qdrant_not_available", hint="Start Qdrant first (docker run -p 6333:6333 qdrant/qdrant)")
        return

    backend.ensure_collection()
    embedding = EmbeddingService()

    count = 0
    for entry in _HEXAGRAM_KNOWLEDGE:
        doc_id = f"{entry.hexagram_name}_{entry.category}_{entry.content[:20]}"
        vector = embedding.embed(entry.content)
        payload = {
            "hexagram_name": entry.hexagram_name,
            "category": entry.category,
            "content": entry.content,
            "keywords": list(entry.keywords),
        }
        backend.upsert(doc_id, vector, payload)
        count += 1
        logger.info("indexed_entry", doc_id=doc_id)

    logger.info("indexing_complete", total=count)
    backend.close()


if __name__ == "__main__":
    main()
