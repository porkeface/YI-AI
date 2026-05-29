"""Embedding向量生成模块

使用 fastembed 生成文本嵌入向量。
默认模型: BAAI/bge-small-en-v1.5 (384维)
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embedding服务"""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self._model_name = model_name
        self._model: Any = None
        self._dimension: int = 384

    @property
    def dimension(self) -> int:
        return self._dimension

    def _get_model(self) -> Any:
        if self._model is None:
            try:
                from fastembed import TextEmbedding

                self._model = TextEmbedding(model_name=self._model_name)
                logger.info("embedding_model_loaded", extra={"model": self._model_name})
            except ImportError:
                logger.error("fastembed not installed. Install with: pip install fastembed")
                raise
        return self._model

    def embed(self, text: str) -> list[float]:
        """生成单个文本的嵌入向量"""
        model = self._get_model()
        embeddings = list(model.embed([text]))
        return embeddings[0].tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量生成嵌入向量"""
        model = self._get_model()
        embeddings = list(model.embed(texts))
        return [e.tolist() for e in embeddings]


# 全局单例
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """获取全局 EmbeddingService 单例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
