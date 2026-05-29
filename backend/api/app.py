"""FastAPI应用入口

配置CORS中间件，注册所有路由。
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.agent import router as agent_router
from api.auth import router as auth_router
from api.divination import router as divination_router
from api.graph import router as graph_router
from api.health import router as health_router
from api.hexagram import router as hexagram_router
from api.history import router as history_router
from api.inference import router as inference_router
from api.ws_divination import router as ws_router
from db.database import init_db

app = FastAPI(
    title="YI-AI 易学AI系统",
    description="东方变化学AI操作系统 API",
    version="0.1.0",
)

# CORS配置 - 允许Nuxt前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.on_event("startup")
async def startup():
    await init_db()
