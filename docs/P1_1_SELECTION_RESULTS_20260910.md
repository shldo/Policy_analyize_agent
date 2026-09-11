# P1.1：保护主干加有限 RRF 补入离线对照

日期：2026-09-10。结论：固定的 `reranker_protected_rrf_backfill_v1` 已完成实现和 B/D 同候选回放，但该首版方案在 MC02 产生退化，未进入真实链路。按预先约定选择 C（原 Top-K + P2）进行后续真实链路验证；不继续围绕个别题调节 6+2 名额。

## 固定策略

- 保护 reranker 排序前 6 个有效、唯一 Child。
- 剩余 2 个位置在同一查看池中按已有 RRF 顺序补入。
- 每个补入槽优先选择尚未覆盖的 section；没有新 section 时允许同 section 回填。
- 无有效 RRF 时按 reranker 顺序补齐；缺失结构按 Child 独立处理。
- 最终仍按原 reranker 顺序输出；不使用题号、gold、问题关键词或语义 coverage 标签。

## 四组同候选结果

| 组 | Child 选择 | Packing | Complete@5 | Complete@20 | Macro EGC@5 | Macro EGC@20 | 平均 packed tokens（50/43） |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| A | 原 Top-K | original | 36/43 | 40/43 | 89.84496% | 94.26357% | 5052.80 / 4989.14 |
| B | P1.1 | original | 36/43 | 39/43 | 89.49612% | 94.10853% | 5120.90 / 5064.28 |
| C | 原 Top-K | P2 | 36/43 | 40/43 | 89.84496% | **95.03876%** | 5316.42 / 5246.19 |
| D | P1.1 | P2 | 36/43 | 39/43 | 89.49612% | 94.88372% | 5508.24 / 5471.81 |

平均值的 50/43 分母分别代表全部题目和 evidence-group 评分题目；Complete 与 EGC 始终使用 43 题评分分母。所有组均为 50 题、43 题可评分，`generation_calls=0`。

## 恢复、退化和损失

- A：相对源 baseline 无变化；selected → packed Child 损失 31。
- B：恢复 `DEV2-CS07` 一组 EGC（`0 → 1/3`），但 `DEV2-MC02` 由完整退化为 `0.6` EGC，Complete@20 `40 → 39`；selected → packed 损失 37。
- C：仅恢复 `DEV2-MC04` 一组 EGC（`1/3 → 2/3`），无退化；selected → packed 损失 `0`。
- D：保留 MC04 恢复并恢复 CS07 一组 EGC，但仍有 MC02 退化；selected → packed 损失 `0`。
- 四组均无重复 packed Child、无超预算。

P1.1 的 Parent 正文观测如下（全题 / 计分题）：

| 组 | 完整扩展 Parent | 仅 Child、未扩展正文 |
| --- | ---: | ---: |
| A | 251 / 218 | 23 / 13 |
| B | 263 / 227 | 30 / 23 |
| C | 266 / 230 | 38 / 27 |
| D | 280 / 243 | 50 / 38 |

这说明回填会增加 Child 证据占用并减少部分 Parent 正文扩展；因此本轮只确认证据覆盖变化，不宣称生成上下文或答案质量无退化。

## 与旧 P1 实验参考

旧 P1 `reranker_rrf_reciprocal_rank_v1` 公共结果为 Complete@20 `40/43`、Macro EGC@20 `95.42636%`、Complete@5 `37/43`。本轮 P1.1 固定 6+2 方案没有超过该参考，也没有超过 C 的离线 EGC，因此不替换默认 Top-K。

## 产物与下一步

- A：`backend/data/evaluation/selection_replay_p11/selection_20260910T091709827324Z/`
- B：`backend/data/evaluation/selection_replay_p11/selection_20260910T091723957235Z/`
- C：`backend/data/evaluation/selection_replay_p11/selection_20260910T091739171604Z/`
- D：`backend/data/evaluation/selection_replay_p11/selection_20260910T091754493224Z/`

四组使用同一保存候选、同一 Child/Parent 快照；没有重新检索或调用模型。后续真实链路验证使用 C，并显式传入 `--selection-strategy reranker_top_k --packing-policy per_document_backfill_v1`。P1.1 代码和测试保留为实验策略，但默认仍为 `reranker_top_k` 与 `original`。

C 的真实链路结果见 [C full-50 报告](SELECTION_C_PUBLIC_RESULTS_20260910.md)：50/50 题处理完成，48 题生成、2 题在生成阶段发生 `OpenAIConnectionError`；Complete@20=`40/43`、Macro EGC@20=`95.03876%`，与离线 C 一致。C 尚未完成人工答案和引用审核，不能据此宣称答案质量提升。
