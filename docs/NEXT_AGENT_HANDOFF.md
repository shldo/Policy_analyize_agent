# 下一阶段开发交接：混合检索后的证据保留

**当前接手入口：先读第 13 节。阶段 3 运行配置接入已完成；前文是历史步骤，不能据此重复开发 P1.1。**

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

先读本文件及上轮结果，核对 develop 和冻结快照。P0/P1 的选择器与 P2 的 packing 回填均已有独立结果；下一步如继续，只能在审核 A/C 后单独推进 P1.1。保留模型、候选池、6000-token 预算和题库不变，不同时启用 Controlled、改 prompt 或重建索引；任何新策略先做同候选离线对照，再决定是否调用生成 API。

## 10. P0/P1 执行记录（2026-09-10）

P0/P1 已完成一次受控实现和公共回归，详见 [P1 结果报告](P1_SELECTION_RESULTS_20260910.md)。新增选择器使用独立 20-Child inspection pool，再向原有 8-Child/6000-token Parent pipeline 发送选择结果；模型、候选生成参数、题库、数据库和快照均未改变。审核确认：CS07 恢复、CS08 退化，最终 Complete@20 仍为 40/43，但 Macro EGC@20 从 94.26357% 提升至 95.42636%。选择器现已改为显式实验策略，默认恢复历史 reranker Top-K，不能直接替换默认质量基线。

本轮源码和测试改动已完成，正式运行目录为 `backend/data/evaluation/selection_p1_public/draft_20260910T055116574066Z/`。审核后工程修正已补齐默认开关、缺失 Child ID 处理和入口一致性测试；没有重跑正式 50 题。下一步可独立设计 P1.1 与 P2，不再把两者混合。

## 11. P2 离线回放（2026-09-10）

P2 已实现为显式 `per_document_backfill_v1` packing policy，默认仍为 `original`。回放工具现在要求源报告明确 `corpus_unchanged=true`，支持显式 Child selection/packing policy，并记录预算、tokenizer、源码哈希和配置差异。使用同一保存候选完成 A（原 Top-K+原 packing）与 C（原 Top-K+P2 回填）离线对照；没有生成调用或正式 50 题。

结果见 [P2 离线报告](P2_PACKING_REPLAY_20260910.md)：A 为 Complete@20 `40/43`、Macro EGC@20 `94.26357%`；C 为 Complete@20 `40/43`、Macro EGC@20 `95.03876%`，Complete@5 均为 `36/43`。C 仅恢复 `DEV2-MC04` 的一组证据覆盖，没有退化题，未达到完整题数提升，因此默认策略不变。P1.1 尚未实现；B/D 不应伪造为已完成对照。

## 12. P1.1 固定方案与 C 真实链路选择（2026-09-10）

P1.1 `reranker_protected_rrf_backfill_v1` 已实现并完成 B/D 同候选回放，固定为 reranker 前 6 个保护、2 个 RRF 补入。B/D 均使 `DEV2-MC02` 退化，Complete@20 为 `39/43`，因此不进入真实链路，也不继续搜索名额。详见 [P1.1 结果报告](P1_1_SELECTION_RESULTS_20260910.md)。

本轮选择 C（原 Top-K + `per_document_backfill_v1`）进入后续真实链路验证；完整评测器已支持显式 `--packing-policy`，默认仍为 `original`，续跑会校验 packing policy。正式运行前必须确认 report 写入 `reranker_top_k` 和 `per_document_backfill_v1`。

真实链路 C 已完成：`backend/data/evaluation/selection_c_public/draft_20260910T092014171489Z/`。50/50 题处理完成，48 题生成、`DEV2-MC01` 与 `DEV2-CS06` 在生成阶段发生 `OpenAIConnectionError`；检索/packing 指标为 Complete@20 `40/43`、Macro EGC@20 `95.03876%`，selected→packed 损失 `0`。详见 [C full-50 报告](SELECTION_C_PUBLIC_RESULTS_20260910.md)。答案和引用仍待人工审核，不能将本轮称为答案质量提升。

## 13. 阶段 3 已实现：统一应用配置与完整审核意见

### 13.1 本轮工程交付

新增 `RAG_PACKING_POLICY`，合法值 `original` / `per_document_backfill_v1`，默认 `original`。未修改本机环境文件、模型、题库、快照、默认选择策略，未部署、未调用生成 API。

- `backend/app/core/config.py`：配置校验；`backend/.env.example`：启用/回退说明。
- `backend/app/modules/chat/rag/parent_pipeline.py`：省略 policy 时读取运行配置，显式评测参数优先；Classic graph、Agent selected-document 和 full-corpus 工具均经此入口。
- `backend/app/modules/chat/rag/agent/context.py`：最终重打包读取同一配置，不会悄悄回到 original；记录输入/保留/丢失 Child 数量，不记录正文。证据丢失时追加最终上下文未完整认证提示，并预留提示 token 开销。
- `backend/tests/test_runtime_packing_policy.py`：真实 resolver/packer、Classic evidence node、两种 Agent 工具及最终消息打包测试。仅替换检索/文件加载 I/O，无模型调用；包括显式 original 回退、配置非法值、Child 引用编号、预算耗尽、历史/system prompt 预算与 Web payload 保持不变。

低层 `pack_generation_context()` 仍保持 original 默认；应用的公共 pipeline 和 Agent final 显式传递配置。评测显式指定策略可不受本机配置影响。未来新增调用点必须遵守同一规则。

启用步骤（应用运维验收时执行，本轮未执行）：在目标后端环境设置 `RAG_PACKING_POLICY=per_document_backfill_v1`，重启后端/worker，确认最终打包日志 policy。回退设为 `original` 并重启；不需要 DB migration、reembed 或重新入库。不同 worker 必须使用同一配置。不要仅改评测命令就宣称 UI 已启用。

### 13.2 对 C 的完整审核意见

1. **代码**：P2 first-pass → deferred backfill → expansion 的顺序正确，Child provenance 不变。阶段 3 补齐实际应用配置传递；测试通过不等于真实 HTTP/SSE/UI 已验收。
2. **结果**：C 为 40/43、95.03876%；相较原策略 MC04 从 1/3 到 2/3，已标注证据无退化；全题 selected→packed 损失为 0。它不是答案正确率，也不是 exhaustive Recall。
3. **范围**：原 C full-50 的 scope 是 full-corpus Classic RAG core，不含 Agent routing/UI。阶段 3 是无 API 的应用组件集成验证，不篡改旧报告 scope 或 source hash。
4. **可靠性**：原运行是 50 次应用层生成尝试、48 成功、2 连接错误；失败行 `generation.status=not_run` 是记账缺陷，不应解释为没有尝试。服务端是否接收/计费未知，不能只凭异常名归因代理。此问题留待阶段 1 修复，不冒称本轮已恢复两题。
5. **质量**：所有题 coverage 为 not_assessed；允许生成不等于完整支持。Parent 正文扩展可能因证据回填减少，需审核是否损失条件/例外背景。
6. **策略**：P1.1 B/D 使 MC02 退化，保留为禁用实验，不继续搜索 6+2 权重。MC06 上游缺失、CS07 Top-K 损失仍是已知限制，不因 P2 成功而注销。
7. **进度**：结束排序启发式迭代；接下来完成失败生成恢复、人工语义审核、实际应用验收，再决定是否启用 C。不是无限等待 Complete@20 超过 40/43。

### 13.3 答案审核标准：参考常用 RAG 维度，明确项目规则

检索与生成分开评估。维度参考 [Microsoft RAG evaluators](https://learn.microsoft.com/en-in/azure/ai-foundry/concepts/evaluation-evaluators/rag-evaluators?view=foundry) 的 groundedness/relevance，以及 [Ragas metrics](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/) 的 faithfulness、response relevancy、context recall。下列政策审核流程和放行规则是本项目制定，**不是统一行业认证或通用分数阈值**；不必安装这些平台才能人工执行。

先将回答拆成可核验的原子断言，每条保存 answer span、对应 Child ID/引用编号/页码、证据原文、标签、理由、reviewer、reviewed_at、run ID。标签使用 supported / partial / unsupported / contradicted / not_verifiable；非事实性建议应标记 suggestion，不能包装为原文义务。

| 维度 | 执行规则 |
|---|---|
| Faithfulness/groundedness | 每条政策事实由最终可见证据支持；不能用模型常识填数字/条款。Parent 提供上下文不自动获得 Child citation 身份 |
| Relevance | 直接回答用户问题，不用冗长报告模板掩盖未回答部分；不主动列大量用户未问的缺口 |
| Completeness | 分别记录“相对问题/gold 的完整度”和“已提供证据是否被充分利用”；诚实的部分回答可通过安全性，但不能获得完整回答标签 |
| Citation correctness | 引用 Child 真正支持相邻断言；编号合法只是语法检查；陈述应与证据的主体/条件/强度一致 |
| Citation completeness | 所有需要来源的实质性政策断言都有有效引用；不以一条泛相关引用支撑整段复合结论 |
| 政策特定准确性 | 检查 actor、action、condition/trigger、timeframe/exception，以及 jurisdiction/version；must/required 与 should/recommended 不混用 |
| 证据不足行为 | 写 provided corpus/available material 不足；不把未检索到写成全文不存在。仅在问题歧义影响检索目标时澄清，不因明确问题缺证据就反问 |
| 表达 | 回答为英文，面向用户的测试总结为中文；先给直接结论，再给适用条件、引用和真实缺口 |

人工结论分为：pass_complete、pass_partial、needs_revision、fail_critical、pending。pass_partial 不计为完整答案。无 gold 的题不编造 correctness 分数；UN 尚未 whole-corpus 人工确认，不能作为正式 refusal gold。

项目放行规则：虚构条款/数字、义务强度反转、错误适用范围、引用与结论矛盾、明知缺证据仍称完整，均为 critical，必须处理后再放行。轻微冗长等单列，不混入检索指标。自动 LLM judge 可以辅助定位，但必须标注 machine_assisted，不能冒充人工签字。

汇总时分母明确：50 总题、43 evidence-group 可评分题、48 当前有答案题，以及实际已审题数。可以报告 claim support rate、引用正确率、应引用断言覆盖率和问题完整度，但都需列计数/判定规则；不得从生成成功率推断答案正确率。示例输出：某明确子问题无证据时回答其他有依据部分，标 pass_partial 而非 fail 或 complete。

### 13.4 剩余实施细则与完成条件

**阶段 1（未执行）**：修复生成尝试/成功/错误的状态统计；对 MC01、CS06 只复用已保存 question/context/citations 恢复生成。记录 context/citation hash、原 run、模型/prompt 配置，写新目录，不覆盖首轮错误。现有 remaining-from 会重新检索，不是 generation-only；新增小入口并限制尝试次数，不叠加 SDK/外层重试。

**阶段 2（未执行）**：先将已有 48 答案按上述表格送审，优先 MC04/MC06/CS07 及扩展变化题，再审其余；失败题恢复后追加。保留错误样例及处理理由。若只修 prompt，应固定 context 单独验证，不能改 gold 或直接覆盖运行答案。

**阶段 4（未执行）**：在测试实例显式启用 P2，通过实际 HTTP/SSE/UI 验证单文档、多文档、全库、多轮、部分回答、Agent 多工具合并、网络错误提示与回退。检查当前引用、history/system 预算、最终日志 policy；确认没有额外 API/敏感日志泄漏。完成后报告可启用或具体阻塞，不仅写“实验保留”。

阶段 3 验证结果见本节后续记录；不以它替代生成恢复和人工答案审核。未获新的发布/推送授权，不部署或推送。

### 13.5 阶段 3 验证实录

- 新增配置/真实组件集成测试：5 个执行案例（包含两类 Agent 工具参数化）。
- 相关测试：26 passed。
- 专用 Docker 容器全套：384 passed、6 skipped、1 条既有 Starlette/AnyIO 弃用 warning。
- Ruff check / format check：通过，244 文件格式检查通过；git diff check 通过。
- 测试无生成 API；没有重跑 full-50，未恢复两道失败生成，未进行人工答案签核或浏览器验收。
- 默认仍为 `reranker_top_k + original`；P2 只在测试中通过临时配置启用，测试结束恢复。本轮没有提交或推送。

## 14. 2026-09-10 恢复、实际UI与答案审核追加结果（优先于前述待办状态）

完整审核与当时实施细则见 [C_ACCEPTANCE_AUDIT_20260910.md](C_ACCEPTANCE_AUDIT_20260910.md)。§13保留为历史记录；用户随后调整为工程收尾，当前执行范围以§15为准。

### 14.1 已执行与未放行状态

- 阶段1已完成：MC01/CS06 使用原已保存 question/context/citations 各恢复一次，2/2成功、0 retrieval calls，原错误保留，合计50个可审答案。新脚本 `evaluation/recover_generation.py`；评测器修复 attempted/error/attempt_count。
- 阶段2已执行50题模型辅助初审和高风险Child复核：23份机器结构校验通过、27份待裁决。**没有全量独立人工签核，不得声称50题答案审核通过。** 逐题可读包位于 `backend/data/evaluation/selection_c_review/reviewer_pack_20260910/INDEX.md`，全部人工栏pending。
- 阶段3配置接入保持；默认策略未改变。
- 阶段4已在隔离数据库和真实Edge页面执行：登录、5文档库、Direct生成、历史重开、引用抽屉、多轮、Agent selected-only、Open Discussion全库多来源、注入网络失败。文档分析模式不提供全库工具是当前设计约束；Open Discussion实际全库成功。
- 修复真实UI缺陷：已有答案不再因legacy sufficiency=false显示“已拒答”；改为完整覆盖未确认。此文案修复不代表router语义已完成修正。
- 全套390 passed/6 skipped/1既有warning；Ruff/format/diff检查通过；前端build通过。冻结Child/Parent哈希仍一致，未提交或推送。

### 14.2 必须纠正的结论

当前 C 最终 Complete@20=40/43、EGC=95.03876%属实，但不能写“CS07已恢复”。逐题CS07在reranked@20为100%，selected/packed为0%；MC04为100%→66.67%；MC06为20%→20%。最终selection造成两题从完整变不完整；P2没有selected→packed丢失，不能掩盖上游截断。

确认 UN02/UN05/UN06 存在“Parent事实引用到并不支持该事实的Child”问题。不能用合法引用编号、相同document_id、judge给pass作为通过依据。MC06诚实partial不能等同虚构；MO05不应因未展开题干没问的另外两个criteria被扣完整性。

Agent工具响应的`evidence_sufficient=false`可在最终router中变为true，原因是`evidence_sufficient = bool(evidence_sources)`，仍混淆“有来源”与“完整支持”。本轮仅改UI错误提示，没有偷偷扩大修复范围。

### 14.3 下一轮按此顺序实施

1. **R1状态合同**：generation_allowed、coverage_status、生成执行状态贯穿router/SSE/history/UI。旧记录为unknown，来源集合不决定complete，部分回答继续允许。补selected/full-corpus/partial/no-context/旧历史/网络失败合同测试。不要重新引入整题强制拒答。
2. **R2固定输入答案/引用**：固定C上下文、模型和题目，缩减无关六段模板，事实严格绑定已选Child；没有支持不扩写。先回归UN02/05/06、MC06、MO05，再全50份新目录generation-only对照。机器judge只能辅助，逐断言裁决留证据。
3. **R3离线selection**：MC04/CS07已在ranked池中，不增Parent预算、不改模型、不用gold在线选择；从现有pool重放一种受控选择改进，与原Top-K逐题比较。固定6+2已有MC02退化，不直接重启。MC06另查retrieval缺口。验收需完整题增加且旧完整题不退化，再调用生成。
4. **R4复现收尾**：UI模式边界可见、PDF页码与移动端、友好失败提示；公开注册admin secret校验被注释是部署前独立安全阻塞，单独修复权限测试，不与RAG效果实验混合。

各步的具体文件定位、失败案例与验收条件在完整报告§5。不要修改benchmark/gold/embedding/reranker/数据库快照来达标。保持原始运行不可变，所有新评测写新目录；未经授权不发布/推送。

### 14.4 交接产物与隐私

新增 `evaluation/review_saved_answers.py`、`evaluation/export_answer_review.py` 与 `evaluation/ui_acceptance.cjs`，后者需要本机Playwright包、Edge和隔离API实例，不是CI默认测试。恢复合同测试为 `tests/test_generation_recovery.py`。

结果文件位于ignored data/evaluation，另一工作区不会因拉取代码自动获得它们。按报告路径复制必要审查数据；**不要复制或提交UI目录中的private-test-user.json、private-browser-state.json**。隔离数据库包含普通合成账号与测试聊天，冻结库未写入这些数据。

## 15. 当前指令：停止指标追逐，完成工程收尾

用户已确认优先交付可复现、可演示、有人工复核边界的项目。下一Agent请执行 [ENGINEERING_CLOSEOUT_AGENT_PLAN.md](ENGINEERING_CLOSEOUT_AGENT_PLAN.md)，该方案覆盖§14.3旧顺序。

- A：状态合同贯穿API/SSE/history/UI；允许部分回答，不能假称完整。
- B：固定C上下文修生成/引用错配，诊断8题后至多一轮全50题generation-only验证；不要增加在线Judge/Planner复杂度。
- C：修复公开注册admin校验，独立权限测试，禁止在主库验证提权。
- D：真实UI、PDF页码、错误提示和Demo启动/回退说明。

**旧R3 selection优化、MC04/MC06/CS07召回补齐、更多PDF和架构升级都转为backlog，不属于本轮验收。** Complete@5=36/43无需提升。默认original不改、冻结材料不改；聊天状态增量迁移仅在隔离副本验证。

尚有未提交工作区改动，GitHub develop不是本机完整代码。接手先核对diff与ignored产物。详细方案本轮只写文档，A–D仍待实现；不得把计划表述为已完成。

## 16. Engineering closeout A–D（2026-09-10）

已按 [ENGINEERING_CLOSEOUT_AGENT_PLAN.md](ENGINEERING_CLOSEOUT_AGENT_PLAN.md) 完成一轮增量收尾，结果见 [ENGINEERING_CLOSEOUT_RESULTS.md](ENGINEERING_CLOSEOUT_RESULTS.md)，Demo 启动见 [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md)。上一句“ A–D仍待实现”仅为历史状态，本节为当前状态。

- A 状态合同已贯穿 API、SSE、history、Agent/Direct 和 UI；来源非空不会再自动证明 complete，旧消息保守为 unknown/not_assessed。
- B 已移除强制六段式、加入轻量引用身份检查，并完成固定 8 题诊断和一次 50 题 generation-only。两次均无检索/外层重试；引用编号身份通过，但语义支持仍未自动验证，50 题全部 pending review。
- C 已恢复 admin secret 服务端校验；普通注册仍为 user。migration 020 只在隔离数据库验证，禁止对冻结库应用。
- D 已更新状态/错误文案、引用抽屉映射和启动文档；前端 build 通过，但当前代码版本仍需在隔离 API 上做一次浏览器复验。
- 默认仍为 `reranker_top_k + original`；P2 不默认启用，旧 selection/召回优化、题库/模型/快照变更均不属于本轮。
- 自动化验证（临时独立数据库）：406 passed、6 skipped、1 个既有 Starlette/AnyIO warning；Ruff、format、diff、compile 和前端 build 通过。

当前交接判定：可运行的本地研究辅助 Demo，但整体 `needs-fix / environment-blocked`，不可宣称公网/客户正式政策决策上线。下一步先完成隔离数据库迁移后的浏览器验收和 50 题逐断言人工审核，不因生成成功或引用编号合法而宣布答案质量通过。不要复制或提交评测目录中的私有账号、浏览器状态或密钥。

## 17. 最后一轮确定性修复与 E1 审计（2026-09-11）

本轮没有改题库、模型、冻结数据、检索参数或默认策略，也没有调用生成 API。已完成：

- Direct finalize 调用与 history repository 签名对齐；新增 autospec 回归。
- `complete + false` 状态在结果/history 双向归一为 `not_assessed`；部分回答和 suggestions 权限保持独立。
- `Citation.number` 贯穿 schema/UI；显式非连续编号不重绑定，旧无编号数组按位置兼容。
- 离线 E1 审计读取既有 C/B 产物，50/50 有逐题记录，0 个未解析编号；语义字段全部 pending。
- UN02 的 [6] 已核对为 Child `3c867de1-2f08-4c34-9f39-de6d1591fa0f`，仍列为语义风险，不能写成已修复。

验证：临时隔离 pgvector 库（仅预置一个合成普通用户）上的全套测试为 `411 passed, 6 skipped, 2 warnings`；Ruff、format、diff、compile 和前端 build 通过。当前版本没有运行中的隔离 API/前端，浏览器全路径验收仍为 environment-blocked。详情见 [FINAL_ENGINEERING_CLOSEOUT_20260911.md](FINAL_ENGINEERING_CLOSEOUT_20260911.md)。

下一步只做环境准备后的浏览器验收和人工逐断言审核；不以 citation identity、生成成功或历史检索指标替代语义质量签核，不再进行召回率调参。

## 18. 审计与 UI 收尾增补（2026-09-11）

- `build_answer_audit.py` 已改为区分输入 hash 一致性与数据库快照状态；本轮 50/50 输入 hash 匹配，数据库快照为 `not_checked`，输出目录非空时拒绝覆盖。
- `closeout_e1_agent_review_20260911_r2` 包含 8 题/39 条主张的 agent review，以及其余 42 题/513 条主张的 evidence-traceable provisional recheck；没有人类签核，严格质量分母只覆盖 8 题。
- UN02、UN06 的引用语义问题已确认并记录；当前环境没有可用运行时模型凭据，未执行同输入局部生成修复，也没有修改已保存答案。
- UI 浏览器验收因新隔离 Compose 拉取 `node:22-alpine` 时 Docker Hub 网络超时而阻塞；详见 [UI_ACCEPTANCE_20260911.md](UI_ACCEPTANCE_20260911.md)。
- 最新工程收尾结论仍为 `needs-fix / environment-blocked`；不可宣称全 50 题答案质量通过或浏览器验收通过。
# 2026-09-11 最新接管结果

优先阅读 [主张绑定与全量结果](CLAIM_BINDING_RESULTS_20260911.md)。已实现显式 `RAG_CLAIM_BINDING_ENABLED=false` 开关，Direct/Agent 文档分析共用 Child-only 单轮检查；默认关闭。50 题有初稿，离线渲染后 48 题有最终答案、2 题待复核。第二审核器也存在误判，不能宣称全量质量通过。公开实际产物位于 `docs/results/claim_binding_20260911/`。不要重新使用早期 environment-blocked 结论：本地模型配置、PDF、Playwright 均可用，隔离 UI 已验证。
