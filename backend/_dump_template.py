"""通用 docx 诊断脚本：打印任意 docx 的全部段落（索引/样式/原文），看完即用、随时可跑。

用法:
    .\\venv\\Scripts\\python.exe _dump_template.py [docx路径]
不传路径时默认检查 assets/报告模板.docx
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from docx import Document

ROOT = Path(__file__).parent
default_path = ROOT.parent / "assets" / "报告模板.docx"
path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path

doc = Document(path)
print(f"文件: {path}")
print(f"段落总数: {len(doc.paragraphs)}  表格总数: {len(doc.tables)}")
for i, p in enumerate(doc.paragraphs):
    style = p.style.name if p.style else "?"
    # repr() 能把全角空格、不可见字符显示出来
    print(f"{i:>3} [{style}] {repr(p.text[:60])}")
