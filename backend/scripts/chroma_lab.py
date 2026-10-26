"""U9 动手实验：向量库 Chroma（学习脚本，不属于主工程流程）

运行（backend 目录下，四条子命令）:
    .\\venv\\Scripts\\python.exe scripts\\chroma_lab.py rebuild                        # 切块→向量化→建实验库（TODO 1/2）
    .\\venv\\Scripts\\python.exe scripts\\chroma_lab.py peek                           # 看库里存了什么（已写好）
    .\\venv\\Scripts\\python.exe scripts\\chroma_lab.py query "实验原理"                # 基础相似检索（TODO 3）
    .\\venv\\Scripts\\python.exe scripts\\chroma_lab.py filter "三、实验原理" "实验原理"  # metadata 过滤检索（TODO 4）

与主库的关系：只建 u9_lab 一个实验集合，不碰 reference_reports 主库。
切块直接复用 chunking_lab 里你 U8 亲手写的 chunk_by_section——不重复造轮子。
rebuild 先删后建 = 全量重建，可反复跑（概念 6）。
"""

import os

# 国内网络直连 HuggingFace 通常超时，默认走镜像站（模型已缓存，此处只是保险）
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import argparse
import sys
from pathlib import Path

# 同目录复用 U8 的切块产物（extract + chunk_by_section）与常量
sys.path.insert(0, str(Path(__file__).resolve().parent))
from chunking_lab import PDF_PATH, CHROMA_DIR, MODEL_NAME, extract_pages, chunk_by_section

LAB_COLLECTION = "u9_lab"  # 本单元专属实验集合


# ================= 工程粘合（已写好）：模型加载 =================

def get_model():
    """加载与 U7/U8 同一个 Embedding 模型——两套向量必须同一坐标系（U7 结论）。"""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME, device="cpu")


# ================= 知识核心（你来写）：建库与入库 =================

def rebuild() -> None:
    """切块 → 向量化 → 入库实验库（TODO 1/2）。

    流程：复用你 U8 的 chunk_by_section 切出带 page/section 的块，
    同一模型向量化后写入 u9_lab 集合。
    """
    import chromadb

    model = get_model()
    chunks = chunk_by_section(extract_pages(PDF_PATH))
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    try:
        client.delete_collection(LAB_COLLECTION)  # 先删后建：保证反复重跑不残留旧块
    except Exception:
        pass  # 首次运行库不存在，忽略

    embeddings = model.encode(
        [c["text"] for c in chunks],
        normalize_embeddings=True,  # 归一化（U7 结论：点积 = 余弦相似度）
        show_progress_bar=False,
    )

    # TODO 1: 建集合
    #   要求：get_or_create_collection，name 用 LAB_COLLECTION，
    #         metadata={"hnsw:space": "cosine"}——建库时定死，写错只能删库重建（概念 2/误区 2）
    #   提示：chunking_lab.build_index 里有一模一样的行，抄过来改集合名即可
    #   验收：rebuild 全流程不报错
    col = None  # ← 替换

    # TODO 2: 入库
    #   要求：用 upsert 写入四件套，然后打印入库块数——
    #       ids:      f"u9-{i}"，按枚举序号生成
    #       embeddings: embeddings.tolist()
    #       documents:  每块的 text
    #       metadatas:  每块的 {"page": ..., "section": ...}（U8 红利 3：免费 metadata，实验 2 全靠它）
    #   提示：for i, c in enumerate(chunks) 配合 embeddings[i] 可同时拿到块、序号、向量；
    #         也可以一次性把整个列表传给 upsert（chunking_lab.build_index 就是这么写的）
    #   验收：末行打印"入库 25 块"（与 U8 的 u8_section 块数一致——同源切块）
    pass  # ← 替换为入库代码 + print


# ================= 已写好：看库（get 用法示范） =================

def peek(limit: int = 8) -> None:
    """count + get 看库里到底存了什么。

    U6"眼见为实"教训的库版：调试检索问题前先看库——
    get() 按 id 直接取，不算相似度，与 query() 分工不同。
    """
    import chromadb

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    col = client.get_or_create_collection(name=LAB_COLLECTION, metadata={"hnsw:space": "cosine"})
    print(f"库 [{LAB_COLLECTION}] 共 {col.count()} 块")
    if col.count() == 0:
        print("空库，先跑 rebuild")
        return

    res = col.get(include=["documents", "metadatas"], limit=limit)
    for i, (doc, meta) in enumerate(zip(res["documents"], res["metadatas"])):
        section = meta.get("section", "")
        preview = doc[:50].replace("\n", " ")
        print(f"[{i}] 第{meta.get('page')}页 章节[{section}] | {preview}...")


# ================= 知识核心（你来写）：检索 =================

def search(query: str, where: dict | None = None, top_k: int = 3) -> None:
    """相似检索主流程（TODO 3 主体 + TODO 4 过滤）。

    where 不为 None 时启用 metadata 过滤——U8 埋的钩子今天兑现（概念 4）：
    过滤改变的是候选池，不是距离数字。
    """
    import chromadb

    model = get_model()
    qvec = model.encode([query], normalize_embeddings=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    col = client.get_or_create_collection(name=LAB_COLLECTION, metadata={"hnsw:space": "cosine"})
    if col.count() == 0:
        print("空库，先跑 rebuild")
        return

    # TODO 3: 相似检索主体（先不管过滤，把 query 跑通）
    #   要求：调用 col.query，传三个参数——
    #       query_embeddings = qvec.tolist()   查询向量（与入库同一模型同一归一化）
    #       n_results = top_k                  返回条数
    #       include = ["documents", "metadatas", "distances"]   调试三件套（漏了看不到文本）
    #   验收：query 子命令能打印 top_k 条"距离 | 页 | 章节 | 预览"

    # TODO 4: 接入 metadata 过滤
    #   要求：where 不为 None 时，query 调用额外传 where=where；为 None 时行为与 TODO 3 相同
    #   提示（推荐写法）：用 kwargs 字典组装参数，再 col.query(**kwargs)——
    #       kwargs = { 三个参数 }
    #       if where:
    #           kwargs["where"] = where
    #       res = col.query(**kwargs)
    #   验收：filter 子命令的 top_k 条结果章节列【全部】相同（实验 2 的翻案时刻）
    res = None  # ← 替换

    print(f"\n===== 查询: {query}" + (f" | 过滤: {where}" if where else "") + " =====")
    for text, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        print(f"  距离 {dist:.4f} | 第{meta.get('page')}页 | 章节[{meta.get('section', '')}]")
        print(f"    {text[:80]}...")


if __name__ == "__main__":
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    cli = argparse.ArgumentParser(description="U9 向量库 Chroma 实验")
    sub = cli.add_subparsers(dest="cmd", required=True)
    sub.add_parser("rebuild", help="切块→向量化→建实验库（TODO 1/2）")
    sub.add_parser("peek", help="看库里存了什么（count + get）")
    p_q = sub.add_parser("query", help="基础相似检索（TODO 3）")
    p_q.add_argument("query", help="查询语句")
    p_q.add_argument("--top-k", type=int, default=3, help="返回条数，默认3")
    p_f = sub.add_parser("filter", help="metadata 过滤检索（TODO 4）")
    p_f.add_argument("section", help="章节完整标题（先 peek 确认写法）")
    p_f.add_argument("query", help="查询语句")
    p_f.add_argument("--top-k", type=int, default=3, help="返回条数，默认3")

    args = cli.parse_args()
    if args.cmd == "rebuild":
        rebuild()
    elif args.cmd == "peek":
        peek()
    elif args.cmd == "query":
        search(args.query, top_k=args.top_k)
    elif args.cmd == "filter":
        search(args.query, where={"section": args.section}, top_k=args.top_k)
