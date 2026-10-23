"""内容生成：把实验内容 + RAG 检索结果交给 LLM，生成各章节文字。

第 4 步实现。要求返回结构化 JSON，例如：
    {"purpose": "...", "principle": "...", ...}
"""


class ContentGenerator:
    """章节文字生成器。"""

    def generate(self, experiment_content: str, references: list[str]) -> dict:
        """返回六个章节的文字。"""
        raise NotImplementedError("第 4 步实现")
