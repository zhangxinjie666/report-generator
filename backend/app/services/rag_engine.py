"""RAG 引擎：参考报告入库与检索。

RAG（Retrieval-Augmented Generation，检索增强生成）：
    把参考文档切块、向量化后存进向量库；生成时先用"查询语句"检索出
    最相关的几个块，塞进 LLM 的 prompt 里，让模型"开卷作答"。

本类的两条链路：
    入库:  PDF --pymupdf按页提取--> 文本 --清洗--> 文本 --滑动窗口切块--> 块列表
           --bge模型向量化--> 向量+原文+页码 --upsert--> Chroma（落盘）
    检索:  查询语句 --同一个bge模型向量化--> 查询向量 --Chroma找最近邻--> top_k 个块

为什么入库和检索必须用同一个模型：
    不同模型把文字映射到不同的"坐标空间"，A 模型的向量和 B 模型的向量
    之间的距离没有意义，就像"东经120度"和"5楼B座"没法比较远近。

关于 distance（Chroma 返回的相关度）：
    采用 cosine（余弦）距离时，取值 0~2，越小越相关：
    0 = 方向完全一致（内容几乎相同），越接近 2 越不相关。
    实际判断"相关不相关"看排序即可，不用死记阈值。

直接测试本文件（两条子命令）：
    .\\venv\\Scripts\\python.exe -m app.services.rag_engine index ..\\assets\\示例报告.pdf
    .\\venv\\Scripts\\python.exe -m app.services.rag_engine search "实验原理部分应该写什么"
"""

import os

# 国内网络直连 HuggingFace（模型下载源）通常超时，默认改走镜像站；
# 如果你开了代理也不冲突，镜像不可用时它会自动回退官方源
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import sys
from pathlib import Path

import chromadb
import pymupdf
from sentence_transformers import SentenceTransformer

from app.core.config import settings


class RagEngine:
    """参考报告知识库。"""

    def __init__(self) -> None:
        # 本地 embedding 模型（首次运行自动下载约 100MB 到用户缓存目录，之后离线可用）
        self.embedder = SentenceTransformer(
            settings.embedding_model,
            device="cpu",  # 没有独显也能跑，速度对几百个块完全够用
        )
        # Chroma 本地持久化客户端：数据落盘在 assets/chroma_db，重启不丢
        self.client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        self.collection = self.client.get_or_create_collection(
            name="reference_reports",
            # cosine：用余弦距离衡量向量相近程度，RAG 最常用的度量
            metadata={"hnsw:space": "cosine"},
        )

    # ---------------- 入库 ----------------

    def index_pdf(self, pdf_path: str | Path) -> int:
        """把一份参考报告 PDF 入库，返回本次写入的块数。"""
        pages = self._extract_pages(pdf_path)
        chunks = self._chunk(pages)
        if not chunks:
            return 0

        # 批量向量化：encode 一次算完所有块，比逐条快得多
        embeddings = self.embedder.encode(
            [c["text"] for c in chunks],
            normalize_embeddings=True,  # 归一化后，余弦计算更稳定
            show_progress_bar=False,
        )
        pdf_name = Path(pdf_path).stem
        # id 用"文件名-序号"：重复入库同一个 PDF 时 upsert 会覆盖旧块而不是重复添加
        ids = [f"{pdf_name}-{i}" for i in range(len(chunks))]
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=[c["text"] for c in chunks],
            metadatas=[{"page": c["page"], "source": pdf_name} for c in chunks],
        )
        return len(chunks)

    def _extract_pages(self, pdf_path: str | Path) -> list[dict]:
        """按页提取 PDF 文字。返回 [{"page": 页码(从1起), "text": 清洗后的文字}]。"""
        doc = pymupdf.open(str(pdf_path))
        pages: list[dict] = []
        for page in doc:
            text = self._clean_text(page.get_text())
            if text:  # 空白页跳过
                pages.append({"page": page.number + 1, "text": text})
        doc.close()
        return pages

    @staticmethod
    def _clean_text(raw: str) -> str:
        """清洗 PDF 提取出来的文字。

        PDF 里的一段话往往被拆成很多行，直接用会检索出"断句碎片"。
        处理规则：去掉每行首尾空白并拼接；仅当两行接缝处都是
        英文字母/数字时补一个空格，避免出现 "Multisim仿真" 变 "Multis im仿真"。
        """
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        out = ""
        for line in lines:
            if (
                out
                and out[-1].isascii() and out[-1].isalnum()
                and line[0].isascii() and line[0].isalnum()
            ):
                out += " " + line
            else:
                out += line
        return out

    def _chunk(self, pages: list[dict], chunk_size: int = 350, overlap: int = 60) -> list[dict]:
        """滑动窗口切块。

        chunk_size: 每块目标长度（字符）。bge-small-zh 上限 512 token，
                    中文约 1 字 = 1 token，350 字留了充足余量。
        overlap:    相邻块重叠的字符数，防止关键句恰好被切在边界上、
                    两块都只剩半句，导致两块都检索不准。
        """
        chunks: list[dict] = []
        for page in pages:
            text = page["text"]
            step = chunk_size - overlap  # 每次前进的步长
            for start in range(0, len(text), step):
                piece = text[start : start + chunk_size]
                if len(piece) < 30:  # 末尾太短的碎块直接丢弃
                    break
                chunks.append({"text": piece, "page": page["page"]})
                if start + chunk_size >= len(text):  # 已经覆盖到结尾
                    break
        return chunks

    # ---------------- 检索 ----------------

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """检索与 query 语义最相近的 top_k 个块。"""
        count = self.collection.count()
        if count == 0:
            return []
        query_embedding = self.embedder.encode(
            [query], normalize_embeddings=True
        )
        result = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )
        hits: list[dict] = []
        # Chroma 的返回结构是"每个查询一组列表"，这里只查了一条所以取 [0]
        for text, meta, dist in zip(
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0],
        ):
            hits.append({
                "text": text,
                "page": meta["page"],
                "source": meta["source"],
                "distance": round(dist, 4),
            })
        return hits


if __name__ == "__main__":
    # 用 argparse 提供两个子命令：index 入库 / search 检索
    import argparse
    import json

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    cli = argparse.ArgumentParser(description="RAG 知识库命令行工具")
    sub = cli.add_subparsers(dest="cmd", required=True)

    p_index = sub.add_parser("index", help="把 PDF 入库")
    p_index.add_argument("pdf", help="PDF 文件路径")

    p_search = sub.add_parser("search", help="语义检索")
    p_search.add_argument("query", help="查询语句")
    p_search.add_argument("--top-k", type=int, default=3, help="返回条数，默认3")

    args = cli.parse_args()
    engine = RagEngine()

    if args.cmd == "index":
        n = engine.index_pdf(args.pdf)
        print(f"入库完成：本次写入 {n} 块，库内共 {engine.collection.count()} 块")
    elif args.cmd == "search":
        hits = engine.search(args.query, args.top_k)
        if not hits:
            print("知识库为空，请先执行 index 子命令入库")
        for h in hits:
            print(f"\n[{h['source']} 第{h['page']}页 距离{h['distance']}]")
            print(h["text"][:120] + ("..." if len(h["text"]) > 120 else ""))
