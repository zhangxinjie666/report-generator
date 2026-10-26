# U9 · 向量库 Chroma

> **本单元服务于项目哪个模块**：v1 MVP 第 3 步"RAG 知识库（PDF→切块→Chroma→检索）"的存储与查询引擎。U6~U8 解决了"块从哪来、向量怎么算"，U9 解决"向量存哪、怎么查"——U10 把四者组装成真正的检索链（改造 `rag_engine.py`）。

## 前置知识

- U7：归一化后点积 = 余弦相似度；两套向量必须同一坐标系（同一 Embedding 模型）
- U8：`chunk_by_section`（你亲手写的）产出的块带 `page`、`section` 两个元数据字段——今天的核心实验就是让它们发挥作用
- 顺带的隐性基础：`chunking_lab.py` 的 `index`/`compare` 里你已经**用过** Chroma（我写的工程粘合部分）——本单元的任务是把"用过但没理解"变成"理解并能自己写"

## 概念讲解

### 概念 1：为什么需要一个"库"——从 U7 的 numpy 暴力检索说起

U7 的 `embedding_lab.py` 里，检索是这么做的：所有向量装进一个矩阵，`vectors @ vectors.T` 算全部两两点积，取 top-k。这在实验里完全够用，但它有四个致命伤，恰好对应向量库提供的四件事：

| numpy 暴力检索的问题 | 向量库给的能力 |
|---|---|
| 程序一关向量就没了，下次启动要全量重算 | **持久化**：向量 + 文本 + 元数据落盘，重启即用 |
| 每次查询扫全部向量，数据量大就慢 | **索引**（如 HNSW，见概念 5）：近似检索换速度 |
| 只能按"向量像不像"排序，想"只查某章节"做不到 | **metadata 过滤**：结构化条件先筛后搜 |
| 没有增删改，改一条要重建整个矩阵 | **CRUD**：add / upsert / get / delete |

一句话：**向量库 = 会存向量 + 会算相似度 + 会按标签筛选的数据库**。Chroma 是其中最像 SQLite 的一种——零部署、数据就是本地一个文件夹，最适合本项目这种单机应用。

### 概念 2：Chroma 心智模型——两层结构 + 五个操作

```
PersistentClient(path=...)      ← 第一层：客户端，指向一个磁盘目录（assets/chroma_db）
    └── Collection（集合）       ← 第二层：一张"向量表"，如主库 reference_reports、实验库 u8_section
            add()      新增（id 重复会报错）
            upsert()   新增或覆盖（id 相同就替换）——chunking_lab 用的就是它
            query()    相似检索（今天的主角）
            get()      按 id / metadata 直接取（不排序，用于看库）
            delete()   按 id / metadata 删
```

两个工程细节：

- `get_or_create_collection(name, metadata={"hnsw:space": "cosine"})`——`hnsw:space` 决定距离度量，**建库时定死，事后改不了**；不指定默认是 L2（欧氏距离），和 bge + 归一化这套打法不匹配，所以每次建集合都要显式写 cosine
- 本项目所有库共用一个 `CHROMA_DIR`（`assets/chroma_db`），靠集合名区分：`reference_reports` 是主库，`u8_window`/`u8_section`/`u9_lab` 是实验库

### 概念 3：query 返回的 distance 是什么

Chroma 的 `query()` 返回**距离**不是相似度：cosine 空间下取值 0~2，越小越相关（U6 一路看下来的 0.1993、0.3682 就是它）。想要"相似度百分比"要自己换算（`1 - distance`），但 U8 的核心领悟提醒你：**别盯着距离数字看，要看命中块的构成**。

另一个细节：`include` 参数控制返回内容（`documents`/`metadatas`/`distances`），不写就只回 id——调试时看不到文本，还以为检索坏了。

### 概念 4：metadata 过滤——U8 红利 3 的兑现

U8 说过结构切分的第三个红利是"免费 metadata"：块自带的章节名、页码随手存进库，检索时就能按条件筛。今天兑现：

```python
# 无过滤：全库找最像的——U8 实测裸查"实验原理"top3 混进了表格块、目的块
res = col.query(query_embeddings=qvec, n_results=3)

# 有过滤：先按 metadata 缩小候选池，再在里面找最像的
res = col.query(query_embeddings=qvec, n_results=3, where={"section": "三、实验原理"})
```

**关键认知：过滤改变的是候选池，不是距离数字。** 过滤不会让某个块变得更像查询——它只是把别的章节的块从比赛里赶出去。所以过滤的收益是"top-k 的构成有保证"，而不是"距离变小"。这正是 U8 核心领悟（纯净度 ≠ 距离数字）的延续：结构切分让纯块**存在**，metadata 过滤让纯块**必被命中**——两步合起来，"按章节找写法"才算真正可依赖。

where 条件完整写法是 `{"section": {"$eq": "三、实验原理"}}`（$eq = equal），等值匹配可简写为 `{"section": "三、实验原理"}`。还有 `$ne`（不等）、`$in`（属于集合）、`$and`/`$or` 组合——够用了，别记更多。

### 概念 5：HNSW——"近似"检索是什么意思（认知层）

全库暴力比对（U7 的矩阵乘法）是**精确**检索：一定找到真正的 top-k，但 O(N) 全扫。HNSW（分层可导航小世界图）是**近似**检索（ANN）：预先把向量组织成一张多层"跳表式"图，查询时从顶层粗跳到底层细找，只比较一小部分向量——**牺牲一点点召回率，换数量级的速度**。

建集合时那两个参数的直觉：`hnsw:M` 是每个节点的连线数（越大图越密越准、建库越慢），`hnsw:construction_ef` 是建图时的候选宽度（同理）。**本项目数据量（几十块）下这些参数完全无感**——知道它们是"精度-速度旋钮"即可，数据量上百万时才有调的必要。

### 概念 6：add、upsert 与"重建"的分工

- **add**：新增，id 重复直接报错——适合"永远只加一次"的库
- **upsert**：存在则覆盖、不存在则新增——适合实验脚本反复重跑
- **delete_collection 后重建**：切分策略、Embedding 模型任一变化 → 所有块内容/坐标系全变 → 只能全量重建（U8 误区 5 的机制层原因：块边界变了，旧 id 和新块对不上号，upsert 无从覆盖）

本项目主库将来换 Embedding 模型时同理：**换模型 = 换坐标系 = 全量重建**，U7 结论在库层的落地。

## 常见误区

1. **把 distance 当相似度百分比**——0.2 不是"20% 相关"。它是 cosine 距离（0~2），越小越好；要百分比自己 `1 - dist` 换算（且换算后的数也没有概率含义）。
2. **建库忘写 `hnsw:space: cosine`**——默认 L2，和 U7 的归一化余弦打法不匹配，距离数字会变得没意义；而且建完改不了，只能删库重建。
3. **以为过滤能提高相关性**——where 只缩候选池，不改变距离计算。过滤后 top1 距离没变低是正常的，看构成别看数字（概念 4）。
4. **改了切分/模型还用 upsert 缝**——块边界或坐标系变了，upsert 救不了 id 对不上的残块，必须全量重建（概念 6）。
5. **query 报错或空结果先怀疑代码**——先查 `count()`：空库、或 `n_results` 大于库存量都会出幺蛾子；调试顺序是"count → get 看库 → query"（U6"眼见为实"教训的库版）。

## 动手实验（chroma_lab.py）

脚本已搭好，4 个 TODO 待你填写；切块直接复用你 U8 写的 `chunk_by_section`（不重复造轮子）。**只建 `u9_lab` 实验集合，不碰主库。**

```bash
# backend 目录下运行
.\venv\Scripts\python.exe scripts\chroma_lab.py rebuild                      # 建库（TODO 1/2）
.\venv\Scripts\python.exe scripts\chroma_lab.py peek                         # 看库存了什么（已写好）
.\venv\Scripts\python.exe scripts\chroma_lab.py query "实验原理"              # 基础检索（TODO 3）
.\venv\Scripts\python.exe scripts\chroma_lab.py filter "三、实验原理" "实验原理" # where 过滤（TODO 4）
```

### 实验步骤

**实验 1 · 建库与看库**

1. 填 TODO 1/2（建集合 + upsert 入库），跑 `rebuild`。验收：打印"入库 N 块"，N 应为 25（与 U8 的 u8_section 一致——同一份 PDF 同一切分函数）。
2. 跑 `peek`（已写好，get 用法示范）：确认每块的 metadata 里 `page`、`section` 都在，记下"实验原理"章节的**完整标题写法**（filter 命令要用它）。

**实验 2 · 翻案实验：metadata 过滤 vs U8 的裸查**

一句话预测（写在这里，赌一个字就行）：过滤后 top1 的距离会比 U8 裸查的 0.3682 更低吗？——赌"会"还是"不会"？

> 你的预测：

3. 填 TODO 3，跑 `query "实验原理"`。对照 U8 记录（top3 = 0.3682 表格子块 / 0.3684 一、目的块 / 0.3712 表格块，纯原理块缺席）——u9_lab 与 u8_section 同源，结果应基本一致。
4. 填 TODO 4，跑 `filter "三、实验原理" "实验原理"`。验收：top3 的章节列**全部**是"三、实验原理"。
5. 对比你的预测与实测，回答两个问题：
   - 过滤后 top1 的距离，相比不过滤时变了吗？（想想概念 4：过滤到底改了什么）
   - "纯块必被命中"靠的是 U8 的哪一步 + U9 的哪一步？两步各贡献了什么？

**实验 3 · 顺手验证 add vs upsert**

6. 把 `rebuild` 里的 upsert 心算换成 add 会有什么后果？（本脚本 rebuild 前先 delete_collection，所以两者此刻行为一样——想清楚"什么情况下 add 才会炸"，写一句话：）

> 你的答案：

### 自测清单（对话式抽查用——我逐题问，你一句话答，不往文档里写）

- 向量库四件事分别对应 numpy 暴力检索的哪个问题？
- `hnsw:space` 为什么必须建库时指定？写错了怎么办？
- query 返回的 distance 语义？为什么过滤后距离不降是正常的？
- add / upsert / 全量重建各用在什么场景？
- 调试一个"检索结果不对"，你的前三步动作？

## 单元小结（留白——只写这 2 格）

> 用你自己的话，每格一两句即可。写完我逐句 review。

1. 向完全没听过向量库的人解释"它是干嘛的"（一句话 + 一个类比）：

2. 本单元最大收获 / 还没想通的地方：

---

## 取材说明（KB 知识库 05_rag 域首次试用）

本单元取材自 `d:\html\agent_learn\KB\05_rag\overview.md` 索引的三源资料：Chroma 工程细节（HNSW 参数直觉、min_relevance、where 条件检索）取自 agent_learning `03_embeddings_vectordb.md`；"向量库解决什么"的概念框架参考 from-zero `18-向量数据库与Embedding实战.md` 第 2 节的库分类视角；HyDE、混合检索等进阶检索策略**不属于本单元**，留待 U46/U10 按需引入。出处完整路径见该 overview 的"出处索引"。
