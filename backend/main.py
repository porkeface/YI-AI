"""启动入口

使用uvicorn启动FastAPI应用。
"""

from __future__ import annotations

import os

import uvicorn

from api.app import app

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    reload = os.environ.get("RELOAD", "true").lower() == "true"
    uvicorn.run("main:app", host=host, port=port, reload=reload)
