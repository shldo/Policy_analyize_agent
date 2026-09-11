# P2：Parent 配额剩余预算回填离线对照

日期：2026-09-10。结论：P2 的确定性回填实现和离线组 C 验证完成；没有调用生成 API，也没有运行新的正式 50 题。P2 保留原 `reranker_top_k` Child 选择，只改变 Parent packing 的第一轮配额处理。

## 范围与不变量

- 题库、gold evidence groups、Child/Parent 快照、数据库和 tokenizer 未修改。
- 使用旧 partial baseline 保存的同一批候选和 reranker 记录，不重新检索。
- Embedding、reranker、模型目标、候选参数、`child_rerank_k=8`、Parent 上限 8、每文档首轮限额 5 和 6000-token 上限不变。
- B/D 的 P1.1 在后续固定方案回放中已完成；本报告仍只记录 P2 的 A/C 对照。
- `generation_calls=0`；结果仅代表证据组覆盖和 packing，不代表答案语义质量。

## 实际修改

- `backend/app/modules/chat/rag/context_packing.py`：新增显式 `per_document_backfill_v1`。第一轮仍沿用原相关性顺序和每文档限额；仅因该限额延后的 Parent 进入回填队列。第一轮结束后，在全局 Parent 数量和 token 预算允许时按原顺序回填，不挤掉第一轮已选 Parent，也不做字符串硬截断。
- `backend/app/modules/chat/rag/parent_pipeline.py`：增加可选 `packing_policy`，默认仍为 `original`，线上默认行为不变。
- `backend/evaluation/replay_selection.py`：增加 `--selection-strategy`、`--packing-policy`，严格要求源报告 `corpus_unchanged=true`，并记录策略、预算、tokenizer、源码哈希及配置差异。回放不调用模型。
- 测试覆盖回填、全局上限、token budget、重复 Parent、Child 引用和默认策略不变。

## A/C 离线结果

| 组 | Child 选择 | Packing | Complete@5 | Complete@20 | Macro EGC@5 | Macro EGC@20 | 平均/最大 packed tokens |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| A | 原 `reranker_top_k` | 原策略 | 36/43 | 40/43 | 89.84496% | 94.26357% | 5052.80 / 5987 |
| C | 原 `reranker_top_k` | P2 回填 | 36/43 | 40/43 | 89.84496% | **95.03876%** | 5316.42 / 5997 |

相对 A，C 的 Macro EGC@20 提升 `0.77519` 个百分点，完整题数和 Complete@5 不变。C 相对源 baseline 的变化只有：

- `DEV2-MC04`：EGC@20 从 `0.3333` 提升到 `0.6667`，仍未完整；
- 没有检测到退化题；
- 选中 Child 在 packed 中的丢失数：A=`31`，C=`0`；
- packed 重复 Child：A/C 均为 `0`；
- 超预算：A/C 均为 `0`；
- C 的 Parent packing trace：`selected_initial=274`、`per_document_deferred=30`、`selected_backfill=30`。

这说明 Parent 硬限额确实造成了可恢复的上下文损失，但 P2 尚未将完整题数从 40/43 提高到 41/43。它也不解决未进入保存候选的上游 Child 召回问题。

## 产物与哈希

- A：`backend/data/evaluation/selection_replay_final/selection_20260910T084117714041Z/`
- C：`backend/data/evaluation/selection_replay_final/selection_20260910T084131847267Z/`
- dataset SHA-256：`950b8639b459092512f6d4a885440e8eaf22ed828309cc612fbdc8add5c290c1`
- corpus snapshot：`52aca085e534f74883e2f4ef3acd2cf2e5a65001205de05e07f093477aba1895`
- Parent snapshot：`bd17ce27f0e245ea0066a769670994d9acaae41d3840395125d259a030502786`
- tokenizer SHA-256：`89085f12ef79460ac5f66d1119325ddfc694b4ab209d80bbd81d35f081dc9614`
- 本轮回放源码 SHA-256：`f7a6cbdbd7879e0f41e97aaf911073c5db0f08de34d0f309f495b5405b10a95c`

## 工程验证

- P2/入口相关测试：`35 passed, 1 warning`。
- `ruff format --check`：通过。
- `ruff check`：通过。
- 全套测试：`373 passed, 6 skipped, 1 warning`（在专用 Docker 测试容器中执行）。
- `git diff --check`：通过。

## 停止结论

P2 可以作为独立离线实验保留；默认 packing 仍为 `original`，没有替换线上策略。下一步若继续，应先由指挥 agent 审核 A/C 结果，再单独实现并回放 P1.1；在没有离线收益证据前，不调用生成 API，也不开展正式 50 题。
