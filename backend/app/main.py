"""FastAPI 应用入口。

启动命令（在 backend 目录下）：
    .\\venv\\Scripts\\uvicorn.exe app.main:app --reload
访问：
    http://127.0.0.1:8000/health
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI

from app.api import report
from app.core.config import settings

app = FastAPI(title=settings.app_name)

# 所有业务接口统一挂在 /api 前缀下，方便以后加版本号（/api/v2）
app.include_router(report.router, prefix="/api")


@app.get("/health")
def health() -> dict:
    """健康检查：服务活着就返回 ok，用于确认启动成功。"""
    return {"status": "ok"}
