# P1：重排后 Child 选择回放与公共运行结果

日期：2026-09-10。结论：本轮 P1 工程改动完成并可复现。它修复了一个真实的 Top-8 截断路径：CS07 的两个目标 Child 进入了最终 packed context；同时 CS08 发生一组证据退化。最终完整题数持平，但 Macro EGC@20 从 94.26357% 提升至 95.42636%。本轮选择器曾在实验运行中默认启用，审核后已改为显式策略开关，默认恢复历史 Top-K；因此实验结果不能直接视为默认策略质量。

## 1. 范围和不变量

- 分支：`develop`；工作区开始时干净。
- 题库：`policy-parent-child-dev50-v1`，50 题，43 题进入 evidence-group 评分分母；没有修改题目或 gold mapping。
- 快照：5 份 PDF、Child/Parent、向量库和数据库快照未修改。
- Embedding：`BAAI/bge-small-en-v1.5`。
- Reranker：`BAAI/bge-reranker-base`。
- Generation：`deepseek/deepseek-v4-flash`。
- 原候选参数：dense/BM25 各 30、RRF 常数 60；`child_rerank_k=8`。
- 新增的 `child_selection_pool_k=20` 只是独立的重排后查看池，不是生成上下文大小；实际仍最多送入 8 个 Child，Parent 上限 8、每文档 5、context 6000 tokens 均未改。`child_selection_strategy` 默认是 `reranker_top_k`，实验值 `reranker_rrf_reciprocal_rank_v1` 必须显式指定。
- Controlled Retrieval、Planner/Inspector、Query、阈值、补查轮数、Web Search 和 packing quota 未改。

## 2. P0 诊断

旧链路是：`BM25+dense → RRF → reranker → ranked[:8] → Parent resolution → packing`。候选池中已有证据不等于生成时实际保留了证据；MC06 的 Dayos 证据甚至不在联合候选池内，P1 不可能从后续选择阶段恢复它。

| 题目 | 候选数 | 旧选择/packed | P1 选择/packed | 诊断 |
| --- | ---: | ---: | ---: | --- |
| CS07 | 54 | 8 / 7 | 8 / 7 | reranker 较低位的两个必需 Child 被选择器保留，最终两组证据均在 packed context；题目从不完整变为完整。 |
| CS08 | 47 | 8 / 8 | 8 / 8 | 选择器替换了一个原先有效的 Child，完整覆盖退化为半覆盖。 |
| MC04 | 53 | 8 / 5 | 8 / 5 | 仍有第 13 位证据未进入最终上下文；另一个位于第 8 位的证据受现有 per-document Parent 限额影响。 |
| MC06 | 50 | 8 / 5 | 8 / 5 | Dayos 相关证据未进入联合候选池；属于上游召回问题，不归因于 P1。 |

每题完整的 candidate → selected → packed ID 与 drop reason 保存在离线回放目录的 `loss_table` 和逐题 `selection_trace` 中。

## 3. 实际修改

- `backend/app/modules/documents/child_selection.py`：新增确定性的 reranker/RRF 倒数秩选择器，去重并记录候选决策；不读取 gold、题目 ID、关键词或文档正文。
- `backend/app/core/config.py`、`backend/.env.example`：增加显式 `CHILD_SELECTION_STRATEGY`（默认 `reranker_top_k`）和 `CHILD_SELECTION_POOL_K`（默认 20）；不改变原 `child_rerank_k=8`。
- `backend/app/modules/documents/service.py`：Classic selected-document 和 full-corpus 入口先查看 20 个重排候选，再选择最多 8 个进入公共 Parent pipeline；Controlled 分支保持原路径。
- `backend/evaluation/exploratory_parent_child.py`：正式评测保存 `selected_child_ids`、`selected_scores` 和逐候选 `selection_trace`。
- `backend/evaluation/replay_selection.py`：新增离线回放，不重新检索、不调用模型、不覆盖旧运行目录。
- `backend/tests/test_child_selection.py` 及 `test_document_service_reranking.py`：覆盖 RRF 互补保留、重复 Child、查看池与实际选择上限、旧 dense-only 兼容和公共入口。

选择器固定使用 25% reranker reciprocal rank + 75% RRF reciprocal rank；最终输出仍按原 reranker 顺序排列，避免改变引用顺序。结构标识用于审计，不新增硬结构 quota；语义 coverage 仍不能由该选择器认证。

## 4. 验证

- 修改前相关回归：39 passed。
- 修改前全套测试：358 passed、6 skipped、1 个既有 warning。
- P1 初版相关回归：45 passed。
- 审核修正后相关回归：53 passed。
- 审核修正后全套测试：367 passed、6 skipped、1 个既有 warning。
- Ruff：通过。
- `git diff --check`：通过。
- 离线 selection replay：43 题可评分，0 模型调用，快照未变；Complete@20=40/43，Macro EGC@20=95.4264%。
- 公共 full-50：50/50 完成生成，0 错误；50 题均为 `generated_pending_review`，`coverage_status=not_assessed`。生成成功不等于答案或引用语义正确。

## 5. 指标对照

| 指标 | 原 partial baseline | P1 公共运行 |
| --- | ---: | ---: |
| Complete@5 | 36/43 | 37/43 |
| Complete@20 | 40/43 | 40/43 |
| Macro EGC@5 | 89.84496% | 90.77519% |
| Macro EGC@20 | 94.26357% | 95.42636% |
| 平均 packed tokens | 4989.14 | 4911.16 |
| 生成调用/错误 | 50 / 0 | 50 / 0 |

P1 的 @5 和 @20 EGC 均有改善，但 Complete@20 仍为 40/43，且 CS08 发生退化；不能把平均覆盖改善描述为完整题数改善。长期 V3 基线仍保留为 38/43、93.72093023255813%，不能只因高于 V3 就宣称本轮突破。

## 6. 运行路径和哈希

- 旧基线：`backend/data/evaluation/hybrid_partial_answers/draft_20260910T021612893235Z/`
- P1 离线回放：`backend/data/evaluation/selection_p1_replay/selection_20260910T055016111733Z/`
- P1 公共 full-50：`backend/data/evaluation/selection_p1_public/draft_20260910T055116574066Z/`
- dataset SHA-256：`950b8639b459092512f6d4a885440e8eaf22ed828309cc612fbdc8add5c290c1`
- corpus snapshot：`52aca085e534f74883e2f4ef3acd2cf2e5a65001205de05e07f093477aba1895`
- Parent snapshot：`bd17ce27f0e245ea0066a769670994d9acaae41d3840395125d259a030502786`
- 公共运行源码 SHA-256：`cea9c9e2ad9dac556b3eb422f5ca3f320071b587fe8421275e764fdffa32096e`

## 7. 审核后工程修正

- 普通查询和全库查询默认恢复 `reranker_top_k`，实验选择器必须通过 `CHILD_SELECTION_STRATEGY=reranker_rrf_reciprocal_rank_v1` 或评测参数显式启用。
- 缺失/空 `chunk_id` 的 Child 直接丢弃并记录 `invalid_child_id`，不可引用的对象不再占用选择名额。
- 测试补充了真正位于旧 Top-K 之外的 RRF 候选、缺失 ID 数量上限、同 section 不做硬去重、默认策略和 selected/full-corpus 两入口一致性。
- 本轮没有实现 P1.1 的有限补入，也没有实现 P2 quota 对照。

## 8. 停止结论

P1 可以作为一个已验证的实验变体保留，但当前不应替换默认选择策略：它恢复 CS07 的真实截断损失、提高平均 EGC，却引入 CS08 退化且没有提高最终 Complete@20。下一步可按审核意见独立开展 P1.1 与 P2；本轮修正不调用生成 API、不重跑正式 50 题、不扩库、不换模型。
