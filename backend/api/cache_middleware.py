"""
API 缓存中间件 - Phase 2.5
提供 HTTP 响应缓存、ETag 支持
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


class CacheMiddleware(BaseHTTPMiddleware):
    """
    HTTP 缓存中间件
    - 对 GET 请求添加 Cache-Control 头
    - 支持 ETag 条件请求
    - 可配置不同路径的缓存策略
    """

    # 路径缓存策略配置
    CACHE_POLICIES: dict[str, dict[str, Any]] = {
        "/api/hexagram": {"max_age": 3600, "s_maxage": 7200},      # 1小时
        "/api/hexagrams": {"max_age": 3600, "s_maxage": 7200},     # 1小时
        "/api/graph": {"max_age": 1800, "s_maxage": 3600},         # 30分钟
        "/api/agent/health": {"max_age": 60, "s_maxage": 120},     # 1分钟
    }

    # 不缓存的路径
    NO_CACHE_PATHS: set[str] = {
        "/api/auth",
        "/api/agent/chat",
        "/api/agent/chat/stream",
        "/api/agent/evolve",
        "/api/divination",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 只缓存 GET 请求
        if request.method != "GET":
            return await call_next(request)

        path = request.url.path

        # 检查是否在不缓存列表中
        if any(path.startswith(p) for p in self.NO_CACHE_PATHS):
            response = await call_next(request)
            response.headers["Cache-Control"] = "no-store"
            return response

        # 查找匹配的缓存策略
        policy = None
        for prefix, p in self.CACHE_POLICIES.items():
            if path.startswith(prefix):
                policy = p
                break

        if not policy:
            return await call_next(request)

        # 检查 If-None-Match (ETag)
        if_none_match = request.headers.get("if-none-match")

        # 执行请求
        response = await call_next(request)

        # 只对成功响应添加缓存头
        if response.status_code == 200:
            # 生成 ETag
            etag = self._generate_etag(response)
            response.headers["ETag"] = etag

            # 检查条件请求
            if if_none_match and if_none_match == etag:
                return Response(
                    status_code=304,
                    headers={"ETag": etag, "Cache-Control": response.headers.get("Cache-Control", "")},
                )

            # 设置 Cache-Control
            max_age = policy.get("max_age", 300)
            s_maxage = policy.get("s_maxage", max_age * 2)
            response.headers["Cache-Control"] = (
                f"public, max-age={max_age}, s-maxage={s_maxage}, stale-while-revalidate=60"
            )

        return response

    def _generate_etag(self, response: Response) -> str:
        """生成 ETag（纯内容哈希，无时间戳）"""
        content = ""
        if hasattr(response, "body"):
            content = str(response.body)
        elif hasattr(response, "content"):
            content = str(response.content)

        return f'"{hashlib.sha256(content[:4096].encode()).hexdigest()[:16]}"'


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    频率限制中间件
    基于 IP 的滑动窗口限流
    """

    def __init__(
        self,
        app: Any,
        max_requests: int = 60,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._windows: dict[str, list[float]] = {}
        self._last_cleanup: float = time.time()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window_seconds

        # 定期清理过期 IP 条目（每 60 秒）
        if now - self._last_cleanup > 60:
            self._cleanup_stale_entries(now)
            self._last_cleanup = now

        # 清理窗口外记录
        if client_ip in self._windows:
            self._windows[client_ip] = [
                t for t in self._windows[client_ip] if t > window_start
            ]
        else:
            self._windows[client_ip] = []

        # 检查限流
        current = len(self._windows[client_ip])
        if current >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"error": "Too many requests", "retry_after": self.window_seconds},
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # 记录请求
        self._windows[client_ip].append(now)

        # 执行请求
        response = await call_next(request)

        # 添加限流头
        remaining = max(0, self.max_requests - current - 1)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(now + self.window_seconds))

        return response

    def _cleanup_stale_entries(self, now: float) -> None:
        """清理过期 IP 条目，防止内存泄漏"""
        window_start = now - self.window_seconds
        stale_ips = [
            ip for ip, timestamps in self._windows.items()
            if not timestamps or all(t <= window_start for t in timestamps)
        ]
        for ip in stale_ips:
            del self._windows[ip]
