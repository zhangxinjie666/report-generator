"""报告生成相关接口。

现在只有占位路由，第 7 步（端到端）时会在这里实现 POST /api/reports/generate。
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/reports", tags=["报告"])


@router.post("/generate")
def generate_report() -> dict:
    """生成报告（占位）。

    目前直接返回 501，表示功能尚未实现，避免调用方误以为成功。
    """
    raise HTTPException(status_code=501, detail="报告生成功能尚未实现")
