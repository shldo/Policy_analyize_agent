# C：原 Top-K + P2 真实链路 full-50

日期：2026-09-10。C 是在 P1.1 B/D 离线回放出现 MC02 退化后选出的真实链路方案。运行已完成 50/50 题处理，显式使用 `reranker_top_k` 与 `per_document_backfill_v1`；未修改题库、模型、Child/Parent 快照或数据库内容。

## 运行配置

- Child selection：`reranker_top_k`
- Packing：`per_document_backfill_v1`
- candidate K：30；rerank K：8；selection pool：20
- Parent 上限：8；单文档首轮限额：5；context budget：6000 tokens
- Embedding：`BAAI/bge-small-en-v1.5`
- Reranker：`BAAI/bge-reranker-base`
- Generation target：`deepseek/deepseek-v4-flash`
- `generation_calls`：48；未自动重跑错误题

## 结果

| 指标 | C full-50 |
| --- | ---: |
| 总题数 | 50/50 处理完成 |
| 评分题数 | 43 |
| Complete@5 | 36/43 |
| Complete@20 | 40/43 |
| Macro EGC@5 | 89.84496% |
| Macro EGC@20 | 95.03876% |
| 平均 packed tokens（50题） | 5316.42 |
| 平均 packed tokens（43题） | 5246.19 |
| 最大 packed tokens | 5997 |
| selected → packed Child 损失 | 0 |
| packed 重复 Child | 0 |
| 超预算 | 0 |
| 完整扩展 Parent / 仅 Child（50题） | 266 / 38 |

证据覆盖指标与 C 离线回放一致：Complete@20=`40/43`，Macro EGC@20=`95.03876%`。这证明显式 `packing_policy` 已在完整评测器实际生效。它不代表生成答案已通过语义审核。

## 基础设施错误

两题在生成阶段发生 `OpenAIConnectionError`，没有生成答案：

- `DEV2-MC01`
- `DEV2-CS06`

两题的检索、packed context 和证据组分数已经写入；错误计入本轮，不重跑。其余 48 题为 `generated_pending_review`。本轮尚未完成人工答案/引用质量审核，不能报告答案正确率或答案质量提升。

## 运行路径与哈希

- 原始报告：[report.json](../backend/data/evaluation/selection_c_public/draft_20260910T092014171489Z/report.json)
- 运行目录：`backend/data/evaluation/selection_c_public/draft_20260910T092014171489Z/`
- dataset SHA-256：`950b8639b459092512f6d4a885440e8eaf22ed828309cc612fbdc8add5c290c1`
- corpus snapshot：`52aca085e534f74883e2f4ef3acd2cf2e5a65001205de05e07f093477aba1895`
- Parent snapshot：`bd17ce27f0e245ea0066a769670994d9acaae41d3840395125d259a030502786`
- source code SHA-256：`d2ca6e43d683fdaa9e1ed405bc885e95235e0d9fb92c9245d341881ce4d189a2`

## 工程验证

- 全套测试：`379 passed, 6 skipped, 1 warning`
- Ruff format/check：通过
- `git diff --check`：通过
- 未修改或提交代码；默认策略仍为 `reranker_top_k` + `original`，C 仅通过评测参数显式启用。

结论：C 可作为 P2 的真实链路验证产物保留；默认上线仍需人工审核 48 个生成答案及引用，并单独评估两例连接错误。P1.1 B/D 不进入真实链路。
