"""FastAPI应用入口

配置CORS中间件，注册所有路由。
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.agent import router as agent_router
from api.auth import router as auth_router
from api.cache_middleware import CacheMiddleware, RateLimitMiddleware
from api.divination import router as divination_router
from api.graph import router as graph_router
from api.health import router as health_router
from api.hexagram import router as hexagram_router
from api.history import router as history_router
from api.inference import router as inference_router
from api.ws_divination import router as ws_router
from api.qimen import router as qimen_router
from api.ziwei import router as ziwei_router
from api.reasoning import router as reasoning_router
from api.observation import router as observation_router
from api.plugins import router as plugins_router
from api.api_platform import router as api_platform_router
from api.enterprise import router as enterprise_router
from api.analytics import router as analytics_router
from db.database import init_db

app = FastAPI(
    title="YI-AI 易学AI系统",
    description="东方变化学AI操作系统 API",
    version="0.3.0",
)

# 中间件（按注册的逆序执行）
app.add_middleware(CacheMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=120, window_seconds=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# 注册路由
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(hexagram_router)
app.include_router(divination_router)
app.include_router(history_router)
app.include_router(inference_router)
app.include_router(graph_router)
app.include_router(agent_router)
app.include_router(ws_router)
app.include_router(qimen_router)
app.include_router(ziwei_router)
app.include_router(reasoning_router)
app.include_router(observation_router)
app.include_router(plugins_router)
app.include_router(api_platform_router)
app.include_router(enterprise_router)
app.include_router(analytics_router)


@app.on_event("startup")
async def startup():
    await init_db()
    # 自动迁移：为旧表添加user_id列（如果不存在）
    import sqlalchemy
    from db.database import engine as _db_engine
    try:
        async with _db_engine.begin() as conn:
            result = await conn.execute(
                sqlalchemy.text("PRAGMA table_info(divination_records)")
            )
            columns = [row[1] for row in result.fetchall()]
            if "user_id" not in columns:
                await conn.execute(
                    sqlalchemy.text("ALTER TABLE divination_records ADD COLUMN user_id VARCHAR(36) REFERENCES users(id)")
                )
                await conn.execute(
                    sqlalchemy.text("CREATE INDEX IF NOT EXISTS ix_divination_records_user_id ON divination_records(user_id)")
                )
    except Exception:
        pass  # 新库直接创建，无需迁移
