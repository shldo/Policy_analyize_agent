# BM25 + Vector + RRF：工程实现

日期：2026-09-10。develop 分支的增量实现；源码交付不代表应用已经部署。接手见 [下一阶段指导](NEXT_AGENT_HANDOFF.md)。

## 现在的真实调用链

用户问题 → 向量 Child Top-K 与 BM25 Child Top-K → 按 Child ID 做 RRF → 现有 cross-encoder → 现有证据检查 → Parent expansion/token packing → generation/citation。

普通 selected-document、Full Corpus、Agent internal search 的公共入口为 `retrieve_child_candidates()`；Controlled Retrieval 的首轮与定向补查现也调用该入口，不再绕过混合检索。Controlled 内禁用额外的 legacy aspect expansion，避免双重规划。

## 实现选择

- PostgreSQL/pgvector 仍保存文档、Child、Parent 和向量，是唯一权威数据源。
- BM25 使用 Python 标准库 SQLite 的 FTS5 倒排索引，不是原来的 PostgreSQL `ts_rank_cd`。不需要另装 Elasticsearch、另购 API 或重嵌入。
- FTS5 使用 `porter unicode61`，针对当前英文问题/英文政策。查询作为转义后的 OR 词项，而不是执行用户输入的 FTS 表达式；保留 must/should/may/not 等义务与否定词。
- 使用 FTS5 原生 BM25 参数与计分约定。返回值取反为正向 `bm25_score`；RRF 只使用排名，绝不把 BM25/RRF 分数当成距离或证据置信度。不同引擎的分析器、IDF 细节不同，不承诺分数与 Elasticsearch 数值一致。[SQLite BM25 官方说明](https://www.sqlite.org/fts5.html#the_bm25_function)
- 两路同权 RRF：`score(child) = Σ 1 / (60 + rank)`，排名从 1 开始；每个来源同一 Child 只贡献一次；同分按 Child ID 稳定排序。[RRF 说明](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion)
- 保留原向量距离、Child/page/section provenance；额外返回 `bm25_score`、`rrf_score`、`retrieval_sources`、`retrieval_ranks`。`lexical_score` 保留兼容字段，现在与 BM25 分数相同。
- reranker 关闭或失败时保留 RRF 候选顺序，不回到先向量后词法的拼接顺序。

## 本地索引生命周期与限制

每次 BM25 检索从数据库获取当前授权范围内、已拥有当前模型向量的 Child。权限与 selected-document 范围在 BM25 Top-K 之前生效。

索引在进程内维护，最多缓存两个 corpus snapshot。Child ID + 正文 hash 标识 snapshot；导入、修改、重切、删除或权限范围变化后自动使用新 snapshot，不能沿用旧候选。metadata 从本次数据库行读取。重启后按需重建，不需要维护磁盘上的第二份文档副本。

这是面向当前本地知识库的低部署成本实现，不是百万级分布式检索架构。每次同步授权范围正文有 O(N) 数据读取/哈希成本，多个进程各有缓存，频繁切换范围会重建。未来实测这一成本成为瓶颈时，可在同一 repository 边界替换为持久化索引/搜索服务，RRF、reranker、Parent 与 Agent 不必重写。

FTS5 不可用时会报错，不静默冒充 BM25 或退回旧 FTS。当前 Docker Python SQLite 3.40.1 已验证支持 FTS5。

## 默认配置与启用

```dotenv
CHILD_CANDIDATE_K=30
CHILD_LEXICAL_CANDIDATE_K=30
HYBRID_RRF_RANK_CONSTANT=60
CHILD_RERANK_K=8
```

`CHILD_LEXICAL_CANDIDATE_K` 保留旧配置名以兼容部署，现在控制 BM25 候选数。默认已从 0 改为 30，`backend/.env.example` 已更新。旧环境显式设置为 0 会保持关闭，需改成 30；已有后端进程需要重启以清除已缓存 settings。

默认每路最多 30 个，去重后最多 60 个进入 reranker。调用方可请求不同 dense K。已有 compound expansion 开启时还可能追加候选；当前默认关闭。未修改 embedding、reranker 模型、证据阈值、context budget 或 Controlled 默认开关。

## 修改文件

| 文件 | 职责 |
|---|---|
| `backend/app/modules/documents/hybrid_search.py`（新增） | BM25 索引缓存、字面查询、RRF |
| `backend/app/modules/documents/repositories/embeddings.py` | 用授权 Child snapshot 替代旧 ts_rank_cd 词法召回；只为 BM25 命中项计算真实距离 |
| `backend/app/modules/documents/service.py` | 两路 RRF 公共入口与 reranker 降级顺序 |
| `backend/app/modules/documents/controlled_retrieval.py` | 首轮/定向补查复用公共混合入口 |
| `backend/app/core/config.py`、`backend/.env.example` | 默认启用与 RRF 参数 |
| `backend/tests/test_hybrid_search.py`（新增） | BM25、RRF、缓存、权限、公共路径回归 |
| `backend/tests/test_chain_regression.py` | 来源名称更新为 bm25 |
| `backend/evaluation/hybrid_retrieval_smoke.py`（新增） | 真数据库只读工程 smoke，无生成、无题库变更 |

注意：工作区存在本轮之前的 Controlled 等未提交改动；整个 git diff 不是本轮全部工作。

## 验证结果

- 修改前相关基线：4 passed。
- 新增及相关测试：61 passed。
- 连接实际测试数据库后的全套：351 passed、6 skipped、1 条既有依赖弃用 warning。第一次未提供容器数据库连接时 12 个数据库用例失败，修正连接后全部通过；不是跳过失败测试。
- 新增和修改 Python 文件 Ruff 检查、格式检查通过。

真实数据库工程 smoke：

| 问题 | Dense | BM25 | 两路交集 | RRF 后 | Reranker 返回/有分数 | 两路召回+RRF 耗时 |
|---|---:|---:|---:|---:|---:|---:|
| AI-generated media / watermarking | 30 | 30 | 6 | 54 | 8 / 8 | 1.451 秒 |
| Mandatory AI training | 30 | 30 | 12 | 48 | 8 / 8 | 0.250 秒 |

另验证 selected-document 结果不越出指定文档、RRF 公式与顺序正确。两题每题包含 rerank 和额外 selected-document 查询的完整 smoke 步骤分别约 32.163 秒、10.924 秒；这不是生成答案延迟，也不是 p95。不能据此声称端到端已经很快。

前后 fingerprint 相同：

- Children：332，hash `0d8f18be0e4e47bedba43f3777a08c5a`。
- 当前模型向量：332，hash `497b1bce6a3c5b4c7b507827d800a655`。

复现（设置正确数据库连接后）：

```sh
python -m pytest tests/test_hybrid_search.py tests/test_chain_regression.py tests/test_document_service_reranking.py tests/test_controlled_retrieval.py -q
python -m evaluation.hybrid_retrieval_smoke
```

本次验证目标是工程功能，不是新增 50 题 benchmark。没有宣称召回率或答案正确率提升。旧距离和语义证据 gate 保持不变，因此 BM25 补回的候选仍可能被后续 gate 拒绝；不会因 RRF 高分就绕过证据要求。
