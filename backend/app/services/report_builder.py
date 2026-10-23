"""报告组装与导出：把文字和数据填进模板，导出 docx，再转 PDF。

第 6 步实现。docx 填充用 python-docx；
docx 转 PDF 调用本机 Word（win32com），效果与手动另存一致。
"""


class ReportBuilder:
    """报告组装器。"""

    def build(self, template_path: str, sections: dict, tables: dict, output_path: str) -> str:
        """生成 docx，返回文件路径。"""
        raise NotImplementedError("第 6 步实现")

    def to_pdf(self, docx_path: str) -> str:
        """把 docx 转成 PDF，返回 PDF 路径。"""
        raise NotImplementedError("第 6 步实现")
