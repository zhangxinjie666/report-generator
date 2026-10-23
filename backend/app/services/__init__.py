"""业务逻辑层。

每个文件负责一个独立环节，由 api 层按顺序调用，不互相耦合：
    template_parser    -> 解析 docx 模板，得到封面字段、章节、表格结构
    rag_engine         -> 参考报告入库（切块/向量化/存 Chroma）与检索
    content_generator  -> 调 LLM 生成各章节文字
    data_validator     -> 校验实验数据是否满足 KCL/KVL 等约束
    report_builder     -> 把文字和数据填进模板，导出 docx，再转 PDF
"""
