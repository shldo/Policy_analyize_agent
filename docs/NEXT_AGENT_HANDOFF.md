# 下一阶段开发交接：混合检索后的证据保留

更新：2026-09-10。接手分支：`develop`。这是当前工作的入口；旧 V3–V6 文档保留实验历史，不代表现在的默认路径。

## 1. 接手目标与边界

目标是可复现的政策 RAG 工程，不是继续堆叠 Planner schema。保持“有依据的部分可以回答；缺口明确说明；部分回答不能标成完整支持”。下一轮优化 **候选选择和上下文打包**，然后处理上游漏召回。

- 不改 benchmark 问题、gold evidence groups、PDF/Child/Parent/向量快照、embedding 或 reranker。
- 不拿 MC04/MC06/CS07 的 ID、gold 位置或专用关键词写运行时代码；这些题只用于诊断。
- 不重建数据库，不批量 reprocess，不覆盖旧运行目录，不以增加补查轮数为主方案。
- 不删除严格模式兼容路径，不默认开启 Controlled Retrieval；不修改 Web Search。
- 推送源码不是部署。接手时检查实际环境覆盖值；进程需重启才读取新配置。

## 2. 已完成的真实架构

入库：PDF extraction/layout hints → deterministic structure detection → Parent → token-aware Child → structure prefix + Child embedding → PostgreSQL/pgvector。

查询：BM25 + dense Child → RRF → cross-encoder → Child selection → Parent resolution/deduplication → token packing → generation → Child citation。

Classic、selected-document、full-corpus、Agent internal search 复用公共候选入口。Controlled 首轮/补查也复用，但默认不开启。Parent 用于生成上下文，Child 保留证据和引用身份。

BM25 是 SQLite FTS5 原生 BM25，英文 `porter unicode61`，不是 PostgreSQL `ts_rank_cd`。PostgreSQL 是权威数据源；FTS5 是进程内按授权范围构建的缓存，没有第二个持久数据库迁移。RRF 同权，不能把 RRF/BM25 分数当相关性概率。

### 当前配置基线

| 项目 | 当前值 |
|---|---|
| Embedding | `BAAI/bge-small-en-v1.5`，384 维 |
| Reranker | `BAAI/bge-reranker-base` |
| 上轮生成模型 | `deepseek/deepseek-v4-flash`，由实际配置确认 |
| Child target/max/overlap | 320 / 380 / 50 tokens |
| Parent target | 600–1500 tokens，结构优先 |
| 向量 / BM25 candidates | 30 / 30 |
| RRF rank constant | 60 |
| Child rerank K | 8 |
| Context / Parent K / per-document | 6000 tokens / 8 / 5 |
| `RAG_ALLOW_PARTIAL_ANSWERS` | true |
| `CONTROLLED_RETRIEVAL_ENABLED` | false |
| `COMPOUND_RETRIEVAL_ENABLED` | false |
| LLM contextual header | 默认关闭 |

### 字段语义不能回退

- `generation_allowed`：能否进入生成，不是完整支持认证。
- 默认 Classic 没有完整性 Inspector：`coverage_status=not_assessed`，不能补成 complete。
- Controlled 的完整支持必须来自有效检查且必要证据仍在最终 packed context 中。
- 无可用 context/citation 仍不能伪造有依据回答。
- 引用编号合法不等于引用语义正确。

## 3. 上轮证据与成绩

先阅读 [完整结果及限制](PARTIAL_ANSWER_RESULTS_20260910.md)、[部分回答契约](PARTIAL_ANSWER_POLICY.md)、[混合检索实现](HYBRID_RETRIEVAL_IMPLEMENTATION.md)。

冻结 development 集 50 题，43 题有可评分 evidence groups；其余 7 题不进入检索分母。5 PDF、332 Child 是**本轮冻结评测快照**，不代表所有本地库文件总数。不是独立 held-out 成绩。

| 阶段 | Complete@20 | Macro EGC@20 |
|---|---:|---:|
| Dense | 37/43 | 91.05% |
| BM25 | 39/43 | 94.46% |
| RRF | 41/43 | 97.36% |
| Reranked candidates | 42/43 | 98.14% |
| 最终 packed context | 40/43 | 94.26% |

实际只选择前 8 Child，不能把候选 @20 成绩当作生成已获得的证据。旧严格模式与部分回答模式用同一候选对照，最终覆盖相同，均允许 50 题生成；旧模式没有重跑生成。新模式 50 次生成成功，未完成全量逐断言语义审核，不报告答案正确率。

最近验证：358 passed、6 skipped、1 条依赖弃用 warning；相关 Ruff、format、diff check 通过。接手后仍需重跑，不将历史测试数字当新改动通过。

本机原始运行目录：
`backend/data/evaluation/hybrid_partial_answers/draft_20260910T021612893235Z/`

包含 `report.json`、`paired_summary.json` 和逐题候选/重排/打包/答案记录，禁止覆盖。

## 4. 必须解决的差距

| 诊断案例 | 定位 | 不能采用的解释 |
|---|---|---|
| CS07，最终 0/3 | BM25/RRF 前 10 完整；reranker 必需证据在 13、16 位，Top-8 全部丢失 | 不是缺 PDF，不是 Gate 拒答 |
| MC04，最终 1/3 | 必需证据在 rerank 8、13、2；13 被 Top-8 截掉，8 被每文档 5 Parents 排除；最终仅 3102 tokens | 不能仅称 6000 tokens 不够 |
| MC06，最终 1/5 | Dayos 四组证据不在联合候选，Bank 证据已命中 | 后续 packing 无法创造未召回证据 |

其他已知工程差距：BM25 每次读取授权范围正文并哈希，O(N)，每进程仅缓存两个快照；还不是大规模持久检索服务。当前分析器面向英文。部分回答由模型依据上下文表达，未获得逐断言正确性保证。未索引文档的兼容路径和 Agent 提示中的旧严格措辞也需独立回归，不能只看评测脚本。

## 5. 下一轮按此顺序开发

### P0：核对与复现，不先更改参数

1. 核对 develop、工作区改动、项目 AGENTS.md、运行配置与本地快照。
2. 阅读本文件列出的公共调用链，确认 Top-8 截断及 per-document 限制发生位置。
3. 运行相关单测和全套测试。读取已有逐题产物，形成候选 → selected Child → packed Child/Parent 的丢失表。
4. 如果快照或原始产物不存在，明确记录不可比；不要用另一个数据库冒充原基线。

### P1：修复重排后互补证据被截断

先保留当前模型和候选池，仅改 selection，优先利用现有 RRF 排名、reranker 排名、结构路径和去重信息。可实现一个小而明确的选择器，在有限池中保留来自不同检索通道/结构单元的互补候选，再按预算送入公共 Parent pipeline。

- 独立配置候选审视池与实际上下文预算，不能把诊断 Top-20 偷偷等同于已使用 Top-20。
- RRF 保留名额、结构去重或秩融合可作为单独变体，不要同时更换多个算法和阈值。
- 所有选择依据来自线上可见数据，不得读取 gold groups。结构多样性只是互补性的代理，不宣称自动完成语义 coverage。
- 日志保存每个保留/丢弃 Child 的原因与排名，不记录普通日志中的完整文档。
- 先使用已保存候选做离线 selection 对照；若尚无 replay harness，新增读取现有产物的小脚本，不重写评分器。随后必须跑公共运行路径验证。

### P2：将硬 diversity 限额改成受预算约束的偏好

单独对照：先做文档多样性选择，再在预算仍有空间时允许同一文档的其他有用 Parent 回填。保留全局 Parent 数量与 token 上限，避免重复 Parent、重复 Child 占位；超限块跳过或使用已有合理小范围扩展，禁止字符硬截正文。

验收重点是 MC04 所揭示的“预算有空余但证据被 quota 丢弃”，不是无条件扩大上下文。记录 token 成本、最终 supporting Child ID、丢弃原因、文档分布。

P1、P2 分开跑，再跑组合；不能只交付组合成绩而无法归因。

### P3：再处理上游缺失的独立实体证据

P1/P2 稳定后，分析 MC06 类型的多主体问题。优先原文 anchor 驱动、有限预算的实体/结构定向召回，保留原始 query 通道。禁止题目专用规则和自由制造问题外实体；不要重新引入大而脆弱的 Planner schema 作为首选。此项单独变体，不与 selection 结果混报。

### P4：答案质量与交付

固定最终 context 后单独调生成表达：只陈述问题要求的证据缺口，减少固定研究报告模板冗长；保留条件、主体、义务强度、例外和 Child 引用。全量逐断言审查答案支持性、引用正确性及完整性。语义审核未完成前不得宣称可上线或无幻觉。

## 6. 代码导航

| 文件 | 阅读/修改职责 |
|---|---|
| `backend/app/modules/documents/hybrid_search.py` | BM25 cache、query、RRF |
| `backend/app/modules/documents/repositories/embeddings.py` | 数据库权限范围、两路检索 |
| `backend/app/modules/documents/service.py` | 公共候选检索、重排入口 |
| `backend/app/modules/chat/rag/parent_pipeline.py` | 证据/生成许可、Parent/packing orchestration |
| `backend/app/modules/chat/rag/context_packing.py` | token 预算、块选择与限制 |
| `backend/app/modules/chat/rag/graph/nodes.py`、`state.py` | Classic 集成 |
| `backend/app/modules/chat/rag/agent/` | Agent 工具、终止条件与最终上下文 |
| `backend/app/modules/documents/controlled_retrieval.py` | 可选 Controlled 路径；默认不启用 |
| `backend/evaluation/exploratory_parent_child.py` | 分阶段候选与双路打包评测 |
| `backend/scripts/summarize_partial_answers.py` | 本轮产物汇总 |
| `backend/tests/test_hybrid_search.py`、`test_partial_answers.py`、`test_parent_pipeline.py` | 重点回归 |

## 7. 测试、评测与验收

新增测试至少覆盖：RRF 高位互补证据不会无说明全被截掉；重复候选不占多份名额；软 quota 可以利用剩余预算；跨文档首轮公平性；token 上限；Child 引用保留；权限与 selected/full-corpus 一致；部分支持不能标完整；旧严格模式不崩溃。

在 `backend` 目录，使用项目依赖环境与正确测试数据库：

```sh
python -m pytest tests/test_hybrid_search.py tests/test_partial_answers.py tests/test_parent_pipeline.py tests/test_agent_parent_context.py tests/test_chain_regression.py -q
python -m pytest -q
python -m evaluation.exploratory_parent_child --dataset evaluation/datasets/policy-parent-child-dev50-v1 --output data/evaluation/selection_packing_next --all-development --compare-strict --run --api-timeout 90
python scripts/summarize_partial_answers.py <new-run-directory>
```

Ruff/format 按仓库 CI 对改动文件及要求目录检查。模型调用会消耗 API 额度；先离线/单测，再执行完整开发集。任何新变体记录实际开关、代码版本、dataset/corpus/Parent fingerprint，输出到全新目录。

每个变体报告：分阶段 Hit@5、MRR@10、Complete@5/@20、Macro EGC；最终 packed coverage；退化/恢复题；上下文 tokens；生成许可及 coverage status；调用错误、延迟及成本。若没有 Inspector，不报告一个虚假的 false-sufficient 改善数字。

目标是超过最终 40/43、94.26%，且不以伪造完整认证或不受控 token 膨胀换取成绩；这是目标，不是保证。未改善就明确失败，保留基线默认，不改题库/阈值凑分。上游 reranker 42/43 不是必须由 packing 盲目承诺达到的线上质量。

## 8. Git 与本地运行资料交接

仓库：`https://github.com/shldo/Policy_analyize_agent`，分支 `develop`。
本机工作目录：`D:\AIWorkspace\Projects\policy-research-agent`。

Git 包含源码、测试、评测数据集与文档；**不包含** `.env`/密钥、`backend/data/` 下原始 PDF、模型/tokenizer 缓存、数据库卷及逐题运行产物。不要为了另一 agent 方便而取消忽略规则或把 API key 写入指导文件。

- 同一台机器：可以直接复用本目录、现有 Docker 和上述只读运行产物；先确认没有另一个 agent 同时写同一文件。
- 新 clone/另一机器：按 backend README 与 `.env.example` 建环境；需要用户安全提供快照备份/原始文件和模型资源，再核对 fingerprint。仓库 clone 本身不足以复现冻结库；重新 ingestion 的数据不能未经核验用于旧指标配对。
- 根 AGENTS.md 引用仓库外 AgentHub 规则；另一机器若缺文件应说明缺失，不编造内容。
- 下一 agent 每轮交付改动列表、测试实录、对照指标与剩余差距，并更新本文件和主指导文档。默认不发布；是否再次推送遵循用户当轮授权。

## 9. 下一 agent 的第一条执行指令

先读本文件及上轮结果，核对 develop 和冻结快照。仅推进 P0/P1：定位并实现一个通用的重排后互补 Child 选择策略，保留模型、候选池、6000-token 预算和题库不变，补针对性测试，输出离线同候选对照及完整开发集结果。不要同时启用 Controlled、改 prompt 或重建索引；P2 单独对照后再合并。
