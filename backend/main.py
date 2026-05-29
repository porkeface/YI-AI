"""启动入口

使用uvicorn启动FastAPI应用。
"""

from __future__ import annotations

import uvicorn

from api.app import app

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
