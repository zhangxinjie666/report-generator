"""RAG 引擎：参考报告入库与检索。

第 3 步实现。流程：
    PDF 解析 -> 按章节切块 -> 本地 bge 模型生成向量 -> 存入 Chroma
    -> 按查询语句检索最相关的片段
"""


class RagEngine:
    """参考报告知识库。"""

    def index(self, pdf_path: str) -> int:
        """把一份参考报告入库，返回切块数量。"""
        raise NotImplementedError("第 3 步实现")

    def search(self, query: str, top_k: int = 3) -> list[str]:
        """检索与 query 最相关的片段。"""
        raise NotImplementedError("第 3 步实现")
