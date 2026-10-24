"""U7 动手实验：Embedding 与相似度（学习脚本，不属于主工程流程）

运行（backend 目录下）:
    .\\venv\\Scripts\\python.exe scripts\\embedding_lab.py

首次运行会自动下载 bge-small-zh-v1.5 模型（约 95MB，缓存在用户目录 ~/.cache，
之后离线可用）。所有 TODO 处由你填写，填写要求见各行注释。
"""
# TODO 1.1: 取消下面一行的注释（numpy 是 sentence-transformers 的依赖，已安装）
import numpy as np

from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-zh-v1.5"  # 512 维中文模型（BAAI 发布）

# ================= 实验 1：从句子到向量 =================
sentences = ["苹果发布了新手机", "我吃了一个苹果", "华为推出了新机型"]

model = SentenceTransformer(MODEL_NAME)

# TODO 1.2: 调用 model.encode 把 sentences 编码为向量，赋给 vectors
#   要求：开启归一化（在 encode 的参数里找 normalize_ 开头的参数，设为 True）
vectors = model.encode(sentences, normalize_embeddings=True)  # ← 在这里填写（替换 None）

print("形状:", vectors.shape)  # 预期 (3, 512)：3 句话，每句 512 维
print("第 1 句前 5 维:", vectors[0][:5])
print("每句范数(应都≈1):", np.linalg.norm(vectors, axis=1))

# ================= 实验 2：相似度矩阵（核心） =================
# TODO 2.1: 计算余弦相似度矩阵
#   提示：向量已归一化 → 点积 = 余弦相似度；矩阵乘法用 @，转置用 .T
sim = vectors @ vectors.T  # ← 在这里填写（替换 None）

print("\n相似度矩阵(保留3位):")
print(np.round(sim, 3))
# 🎯 预测题（跑之前先答，写在 U7 文档小结区第 4 格）:
#   sim("实验步骤","操作流程") 和 sim("实验步骤","猫坐在垫子上") 哪个大？差多少量级?
# 换算练习: 相似度换算成 U6 的 distance = 1 - sim，落在 0.37~0.46 区间吗?

# ================= 实验 3：同字不同义陷阱 =================
# TODO 3.1: 把上面 sentences 换成下面 3 句，整脚本重跑一遍:
#   ["苹果发布了新手机", "我吃了一个苹果", "华为推出了新机型"]
# 🎯 预测: 谁和句 1 最像——共享"苹果"的句 2，还是同为手机话题的句 3?
#   先写预测再跑。预测错了，用一句话在文档小结区写出领悟。

# ================= 实验 4（可选进阶）：不归一化会怎样 =================
# TODO 4.1: 把 encode 的 normalize 参数改为 False，重跑实验 1、2
#   观察: 数值还在 [-1, 1] 吗? 还能和归一化版矩阵直接比较吗?
#   思考: 这解释了 rag_engine.py 入库前为什么要归一化?
