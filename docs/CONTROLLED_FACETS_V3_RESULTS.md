# Controlled Retrieval V3 — 受控 Facets 与最终覆盖门控

## 范围与对照

在 `develop` 上增量修改；未提交、未推送或发布，默认开关不变。

- V2：`backend/data/evaluation/controlled_spans_v2_compact/draft_20260909T023658169102Z`。
- V3：`backend/data/evaluation/controlled_facets_v3_indexed/draft_20260909T053641346466Z`。
- 同一 50 题，43 题有冻结证据映射（13 legacy + 30 新增）；其余 7 题不进入覆盖率分母。
- 同一 Child/Parent 快照、embedding、reranker、生成模型、ANN 30、Child 8、最多两轮与两个补查 query。
- 不修改题目、gold evidence groups、阈值、默认开关、数据库内容或旧运行目录。
- 使用现有 full-corpus Classic RAG core runner；不声称该运行等价于完整 Agent 路由端到端评测。

## 核心设计

1. **需求拆分**：1–5 个原文 anchor，每个 anchor 选择闭集 facet 类型；总计不超过 12 个。类型为 mechanism、condition、exception、actor、purpose、comparison_dimension、timeframe、obligation、scope。每个 facet 有独立 need_index，不允许自由生成实体、quote 或 query。
2. **证据检查**：supported 必须同时声明 direct_support 和 complete_support；否则降为 background 或 partial。所有 required facets 均充分支持才算完整。保留短 span ID 到原始 Child/原文的精确映射，结构 metadata 只传一次。
3. **覆盖融合**：只用最后一次 inspection 的证据绑定，不保留旧 inspection 的优先占位。以能完整覆盖的 facet 数/新增 Child 数选择证据 bundle，优先复用可覆盖多个 facets 的 Child；必须保留同一 facet 需要的全部 Child。
4. **打包**：Controlled 模式保留融合优先级，不再无条件按旧 reranker 分重排。仍先装 Child 证据、再增加 Parent context，不改 token/块数/单文档限额。
5. **统一停止**：distance/reranker 仅作为候选资格过滤。检索阶段的 coverage_sufficient 是 provisional stop reason；最终 `coverage_sufficient` 仅在 `coverage_stage=packed` 且全部必要 Child 仍在上下文时为真。检查错误、超时、缺 plan 均不能由旧 gate 放行。
6. **Classic / Agent**：Classic 的 chat 分支不能绕过 semantic gate；Agent ToolMessage 携带 compact coverage contract，最终再次打包后校验。子查询充分不等于原问题充分；没有与原问题匹配的完整 contract 时保守拒答。Live Web 的非 Controlled 行为保持原状。

注意：direct_support/complete_support 仍是模型判断，不是逻辑证明。严格契约不能消除全部语义误判，必须对照冻结证据并审核实际答案。

## 修改文件

| 文件（仓库相对路径） | 职责 |
|---|---|
| `backend/app/modules/documents/controlled_retrieval.py` | anchored facets、四态检查、最终 inspection 融合、阶段 trace |
| `backend/app/modules/chat/rag/parent_pipeline.py` | 公共语义 gate 与 packed coverage 校验 |
| `backend/app/modules/chat/rag/context_packing.py` | 可选保留 coverage 优先级，非 Controlled 默认行为不变 |
| `backend/app/modules/chat/rag/graph/nodes.py` | Classic 生成前防绕过 |
| `backend/app/modules/chat/rag/graph/state.py` | 保留 coverage trace |
| `backend/app/modules/chat/rag/agent/tools.py` | compact coverage contract 传递 |
| `backend/app/modules/chat/rag/agent/context.py` | Agent 二次打包与原问题范围核验 |
| `backend/app/modules/chat/rag/agent/graph.py` | 覆盖未成立时不调用最终生成 |
| `backend/evaluation/exploratory_parent_child.py` | 空结果也显式传递 trace；不改评分、题库或 gold |
| `backend/tests/test_controlled_retrieval.py` | stale evidence、marginal coverage、partial/background、anchor/编号、multi-child |
| `backend/tests/test_parent_pipeline.py` | packed 丢证据、legacy gate 绕过、Classic chat premature stop |
| `backend/tests/test_agent_parent_context.py` | 二次打包、原问题/子查询范围、旧成功状态失效 |

## 验证

- 修改前：288 passed、5 skipped。
- 修改后：304 passed、5 skipped；Ruff lint/format 通过。
- 保留一个原有 Starlette deprecation warning。
- 第一轮诊断目录 `controlled_facets_v3/draft_20260909T053338299605Z` 因 facet 编号接口歧义定向终止，未覆盖，不计入质量对照。检查器将同一 broad need 的多个 facets 合并回答；改为显式独立 need_index 后全量重跑。

## 指标口径

- 完整证据：最终 packed Child 覆盖全部冻结 gold groups；使用 at_20（实际最多 8 Child，因此包含整个最终选择），同时补充 at_5。
- 平均 Evidence Group Coverage：逐题覆盖比例的宏平均，不是答案正确率。
- false coverage_sufficient：有 gold 映射、系统声明充分，但最终 packed gold coverage 不完整。V2 依据旧 stop reason，V3 依据最终 packed coverage flag；另报 V3 provisional stop，以免口径混淆。
- 停止原因按 50 题统计，包括无映射问题；fallback 单独统计 inspection_or_retrieval_error。
- 同时报告门控拒答与生成数量，不能将拒答增加当作回答质量改善。

## 实测结果

**结论：未达到“提升完整证据覆盖率”的质量目标，不建议开启默认或发布。**
融合的 selection_budget 和最终门控有所改善，但完整覆盖没有增加，前 5 证据排序略退化，回退与保守拒答增加。

| 指标 | V2 | V3 |
|---|---:|---:|
| 完成运行 | 50/50 | 50/50 |
| 全部映射题完整证据 | 38/43 | 38/43 |
| 全部映射题平均 EGC | 93.72% | 93.72% |
| 新增题完整证据 | 25/30 | 25/30 |
| 新增题平均 EGC | 91.00% | 91.00% |
| Packed All Evidence@5 | 37/43 | 36/43 |
| Packed EGC@5 | 92.36% | 91.98% |
| 最终 false coverage_sufficient | 4 | 3 |
| 检索阶段 provisional false sufficient | 4 | 4 |
| selection_budget | 4 | 1 |
| round_limit | 5 | 9 |
| no_new_evidence | 5 | 4 |
| inspection/retrieval error fallback | 0 | 2 |
| time_budget | 0 | 0 |
| 检索阶段 coverage_sufficient | 36 | 34 |
| 打包后 coverage_sufficient | 36（未强制门控） | 33 |
| packed_coverage_incomplete | 未独立门控 | 1 |
| 实际补查题数 | 11 | 14 |
| 生成回答 | 50 | 33 |
| 门控拒答（未调用答案生成） | 0 | 17 |
| gold 已完整但门控拒答 | 0 | 9 |
| 平均检索及打包时间 | 11.24 s | 13.60 s |
| 平均 packed tokens | 4662.40 | 4557.56 |

两轮 `corpus_unchanged=true`，dataset、Child snapshot、Parent snapshot 哈希一致：

- Dataset：`950b8639b459092512f6d4a885440e8eaf22ed828309cc612fbdc8add5c290c1`
- Child snapshot：`52aca085e534f74883e2f4ef3acd2cf2e5a65001205de05e07f093477aba1895`
- Parent snapshot：`bd17ce27f0e245ea0066a769670994d9acaae41d3840395125d259a030502786`

同一轮中未修改运行代码；模型接口仍有随机性、服务时延波动，单轮对照不证明统计显著性。33 个生成结果的引用编号检查未发现非法编号，但未完成全量答案/引用语义审核，不能报告答案准确率提升。

### 统计口径修正

- V3 error fallback 全量为 `2/50`：`DEV2-CS06` 与不进入 43 题评分分母的 `DEV2-UN02`；因此 scored fallback 是 `1/43`，不能写成 `2/43`。
- 单题 `Complete@5` 是二值字段；任何 `0.5` 应表示 `EGC@5=0.5`，不是 Complete@5。

### 失败题与原因

- **MC02：60% → 60%；MC06：20% → 20%；CS07：1/3 → 1/3。** 三题仍为最终 false sufficient，均只执行原 query。检查器把不完整支持当成完整，未触发 gap retrieval；不足不是最终 packing 才引起，候选池本身的 gold coverage 已不足。
- **MC04：2/3 → 2/3。** 原 inspection 仍错误认为充分，但必要 Child 在打包后丢失，V3 拦住了生成。因此 false sufficient 从 4 降到 3 主要是门控收益，不是 Inspector 判断准确性提升。
- **CS08：1/2 → 1/2。** 完整覆盖仍未解决。
- **过宽 anchor 仍存在。** MC02 将整个枚举问题作为单一 anchor，再挂 mechanism/timeframe/scope，未把四类 deliverables 独立绑定；MC06 未把两个比较对象分别绑定证据；CS07 虽拆出 8 个 facets，仍将 alternatives 与 user-transparency 合在一个 anchor。这说明“更多抽象 facet 标签”不等于“更多独立可验证要求”。
- **保守拒答 9 题**：MC10、CS02、CS06、EX03、EX06、MO02、MO04、MO05、MO06（均为 DEV2 前缀）。这些题最终 gold 已完整；需要复核计划是否过度要求、inspection 是否误判。不能只因模型标 partial 就断言真实证据不足。
- **两次 fallback**：CS06 返回 background 却未附 span ID，违反证据契约；UN02 返回空 requirements。均保留原始输出，未放宽校验来掩盖错误。

### 下一轮建议（本轮未实施）

1. 优先修正 **requirement binding**，而非增加检索轮数：将用户原文中并列任务/比较对象拆成独立的原文 span anchor；在该 anchor 下绑定 facet。对仍把完整枚举问题作为单一 anchor 的计划标为未验证，不能仅凭抽象标签宣布完整。
2. Inspector 明确逐个 bound requirement 检查，要求相应对象与适用范围在现有证据中成立；保持短 ID、精确原文映射，不允许自由事实补全。避免仅增加布尔字段或更长 prompt。
3. 区分“可安全归一为 missing 的无证据状态”和真正损坏的响应；评估消除 background+空 spans 的接口回退，但不得把其转换成 supported。
4. 用已有单测与同一冻结 50 题再对照，并观察 complete-but-refused 负担；不降低阈值、不删难题、不增加补查轮数来追指标。

### 审核材料

- 新运行 `report.json`：模型、哈希、逐题阶段覆盖与结束状态。
- 新运行 `summary.json`：按阶段聚合指标。
- 新运行 `answers_review.md`：33 份模型回答及 17 份门控响应、实际 Child 引用。
- 同目录逐题 JSON：plan、原始模型结构输出、每轮证据、最后 inspection、packing、generation 状态。
