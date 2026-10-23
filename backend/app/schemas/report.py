"""报告相关的请求/响应模型。

第 4 步（内容生成）会在这里补充 ReportSections 等模型。
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
