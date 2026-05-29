"""健康检查路由"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "version": "0.1.0"}
