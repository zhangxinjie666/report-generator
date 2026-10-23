"""模板解析：读取 docx 模板，得到封面字段位置、章节结构、表格行列。

第 2 步实现。用到 python-docx。
"""


class TemplateParser:
    """解析报告模板 docx。"""

    def parse(self, template_path: str) -> dict:
        """返回模板结构信息（封面字段、章节标题列表、表格结构）。"""
        raise NotImplementedError("第 2 步实现")
