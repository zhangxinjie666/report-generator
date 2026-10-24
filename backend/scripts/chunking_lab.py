"""U8 动手实验：分块策略对比（学习脚本，不属于主工程流程）

运行（backend 目录下，三条子命令）:
    .\\venv\\Scripts\\python.exe scripts\\chunking_lab.py show              # 看两种切分长什么样（不加载模型，秒出）
    .\\venv\\Scripts\\python.exe scripts\\chunking_lab.py index             # 两种切分各建一个实验库
    .\\venv\\Scripts\\python.exe scripts\\chunking_lab.py compare "实验原理"  # 同一查询查两个库，并排对比

与主库的关系：本脚本只建 u8_window / u8_section 两个实验 collection，
不碰 reference_reports 主库。实验完想清场：跑一次 index 会整体重建，无需手动清理。
"""

import os

# 国内网络直连 HuggingFace 通常超时，默认走镜像站（模型已缓存，此处只是保险）
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import argparse
import re
import sys
from pathlib import Path

import pymupdf

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
PDF_PATH = BASE_DIR / "assets" / "示例报告.pdf"
CHROMA_DIR = BASE_DIR / "assets" / "chroma_db"
MODEL_NAME = "BAAI/bge-small-zh-v1.5"  # 与 rag_engine 同一个模型——两套向量必须同一坐标系（U7 结论）


# ================= 工程粘合（已写好）：PDF 提取 =================
# 注意与 rag_engine 的差异：这里【保留行结构】、不做整页拼接——
# 标题在 PDF 里独立成行，行结构是识别"章节标题"的天然锚点。
# 工程认知：清洗策略要服务于切分策略（U8 文档概念 5）。

def extract_pages(pdf_path: Path) -> list[dict]:
    """按页提取 PDF 文字并保留行。返回 [{"page": 页码(从1起), "lines": [该页非空行]}]。"""
    doc = pymupdf.open(str(pdf_path))
    pages = []
    for page in doc:
        lines = [ln.strip() for ln in page.get_text().splitlines() if ln.strip()]
        if lines:
            pages.append({"page": page.number + 1, "lines": lines})
    doc.close()
    return pages


# ================= 对照组（已写好，读一遍即可）：固定长度滑窗 =================
# 与 rag_engine._chunk 同思路：整页行拼成整串文本，再按字符数滑窗。
# 它就是 U6 破案里的"真凶"，留着做对照组。

def chunk_by_window(pages: list[dict], chunk_size: int = 350, overlap: int = 60) -> list[dict]:
    chunks = []
    for page in pages:
        text = "".join(page["lines"])
        step = chunk_size - overlap  # 每次前进的步长
        for start in range(0, len(text), step):
            piece = text[start : start + chunk_size]
            if len(piece) < 30:  # 末尾太短的碎块丢弃（与 rag_engine 一致）
                break
            chunks.append({"text": piece, "page": page["page"], "section": ""})
            if start + chunk_size >= len(text):  # 已覆盖到结尾
                break
    return chunks


# ================= 知识核心（你来写）：按章节标题切分 =================

def chunk_by_section(pages: list[dict], chunk_size: int = 350, overlap: int = 60) -> list[dict]:
    """按章节标题切分：标题行 = 语义边界。

    三步（对应 TODO 2.1 ~ 2.3）：
        第一步 找标题：正则匹配"中文数字 + 顿号"开头的行
        第二步 切章节：标题行开启新章节，后续行归入当前章节（章节可跨页）
        第三步 章节→块：整章一块；超过 chunk_size 的章节内部滑窗二次切分，子块保留标题做块首
    """
    # TODO 2.1: 把 None 换成你的标题正则（re.compile 的 pattern 参数）
    #   要求：匹配形如 "一、实验目的" "三、实验原理" 的【行首】
    #   提示：中文数字字符集 [一二三四五六七八九十]{1,3}，后面跟一个全角顿号 、
    title_pattern = None  # ← 填写 re.compile(...)

    sections = []    # 收集所有章节，每个元素 {"page": 起始页码, "title": 标题行, "lines": [行, ...]}
    current = None   # 当前正在收集的章节；None = 还没遇到第一个标题（如页眉、报告大标题，直接丢弃）

    for page in pages:
        for line in page["lines"]:
            # TODO 2.2: 行级切片（把下面两行注释之间的逻辑写出来，替换 pass）
            #   1. 若 line 匹配标题 → 开启新章节：
            #      current = {"page": page["page"], "title": line, "lines": [line]}
            #      并 append 进 sections
            #   2. 否则 → 若 current 不为 None，把 line 归入 current["lines"]
            #   3. 标题行自己就是章节的第一行（title 与 lines[0] 相同）——块首天然带标题
            #   提示：判断"是否标题"用 title_pattern.match(line)（match 只看行首，正好符合要求）
            pass  # ← 替换 pass

    # TODO 2.3: 章节 → 块（替换下面的 pass，对 sections 逐个处理）
    #   1. 章节全文 = "".join(sec["lines"])
    #   2. 长度 <= chunk_size → 整章一块：
    #      {"text": 全文, "page": sec["page"], "section": sec["title"]}
    #   3. 长度 > chunk_size → 章内滑窗二次切分（step = chunk_size - overlap，思路同对照组），
    #      每个子块的 text = 标题 + 切片（标题不算进切片长度，允许子块略超 chunk_size，
    #      但必须 < 512——想想这个数字是哪来的）
    #      子块的 section 字段同样填 sec["title"]
    chunks = []
    pass  # ← 替换 pass
    return chunks


# ================= 入库与对比（工程粘合，已写好） =================

def build_index() -> None:
    """两种切分各建一个实验库（先删后建：改完切分策略重跑 index 即全量重建——误区 5 的正确姿势）。"""
    import chromadb
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL_NAME, device="cpu")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    pages = extract_pages(PDF_PATH)

    strategies = {"u8_window": chunk_by_window, "u8_section": chunk_by_section}
    for name, fn in strategies.items():
        chunks = fn(pages)
        try:
            client.delete_collection(name)  # 旧库整体删掉，防止改切分后旧块残留
        except Exception:
            pass  # 首次运行库不存在，忽略
        col = client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
        embeddings = model.encode(
            [c["text"] for c in chunks],
            normalize_embeddings=True,  # 归一化（U7 结论：点积 = 余弦相似度）
            show_progress_bar=False,
        )
        col.upsert(
            ids=[f"示例报告-{i}" for i in range(len(chunks))],
            embeddings=embeddings.tolist(),
            documents=[c["text"] for c in chunks],
            metadatas=[{"page": c["page"], "section": c["section"]} for c in chunks],
        )
        print(f"[{name}] 入库 {len(chunks)} 块")


def compare(query: str, top_k: int = 3) -> None:
    """同一查询分别查两个实验库，并排打印 top_k。"""
    import chromadb
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL_NAME, device="cpu")
    qvec = model.encode([query], normalize_embeddings=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    for name in ["u8_window", "u8_section"]:
        col = client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
        if col.count() == 0:
            print(f"\n[{name}] 空库，请先跑 index")
            continue
        res = col.query(
            query_embeddings=qvec.tolist(),
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        print(f"\n===== [{name}] 查询: {query} =====")
        for text, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
            tag = meta["section"] if meta["section"] else "无"
            print(f"  距离 {dist:.4f} | 第{meta['page']}页 | 章节[{tag}]")
            print(f"    {text[:80]}...")


def show() -> None:
    """不加载模型，纯看切块效果：两种策略的块数 + 每块预览。"""
    pages = extract_pages(PDF_PATH)
    strategies = [("滑窗切块", chunk_by_window), ("章节切块", chunk_by_section)]
    for name, fn in strategies:
        try:
            chunks = fn(pages)
        except Exception as e:
            print(f"\n===== {name}：暂无法运行（{type(e).__name__}: {e}）——完成对应 TODO 后重试")
            continue
        print(f"\n===== {name}：共 {len(chunks)} 块 =====")
        for i, c in enumerate(chunks):
            preview = c["text"][:60].replace("\n", " ")
            tag = f" 章节[{c['section']}]" if c["section"] else ""
            print(f"[{i}] 第{c['page']}页 {len(c['text'])}字{tag} | {preview}...")


if __name__ == "__main__":
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    cli = argparse.ArgumentParser(description="U8 分块策略实验")
    sub = cli.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show", help="看两种切分的块数与预览（不加载模型）")
    sub.add_parser("index", help="两种切分各建一个实验库")
    p_cmp = sub.add_parser("compare", help="同一查询查两个库对比")
    p_cmp.add_argument("query", help="查询语句")
    p_cmp.add_argument("--top-k", type=int, default=3, help="每个库返回条数，默认3")

    args = cli.parse_args()
    if args.cmd == "show":
        show()
    elif args.cmd == "index":
        build_index()
    elif args.cmd == "compare":
        compare(args.query, args.top_k)
