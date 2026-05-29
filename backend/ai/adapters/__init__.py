"""存储适配器

提供可替换的存储后端实现。
"""

from __future__ import annotations

from typing import Any, Protocol


class VectorBackend(Protocol):
    """向量存储后端协议"""

    def is_available(self) -> bool: ...
    def ensure_collection(self) -> None: ...
    def upsert(self, doc_id: str, vector: list[float], payload: dict[str, Any]) -> None: ...
    def search(self, query_vector: list[float], top_k: int = 5) -> list[dict[str, Any]]: ...
    def delete(self, doc_id: str) -> None: ...
    def close(self) -> None: ...


__all__ = ["VectorBackend"]
