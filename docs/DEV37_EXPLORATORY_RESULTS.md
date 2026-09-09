# 新增 37 题真实模型探索性测试

日期：2026-09-08。报告目录：
`backend/data/evaluation/exploratory/draft_20260908T045925676069Z/`。

## 范围和限制

使用 Dev50 中新增的 37 道 draft，旧 13 题没有混入本次分母。冻结五文档、332 Child，
现有 DeepSeek `deepseek-v4-flash`、embedding `BAAI/bge-small-en-v1.5`、
reranker `BAAI/bge-reranker-base`，ANN 30，rerank 后至多 8 个进入 Child gate。
Web Search 关闭，未改阈值、chunk、提示词、参考答案或业务数据库。

运行的是 full-corpus 检索 → rerank → Child gate → Parent packing → 实际生成的 Classic RAG 核心链路，
不是前端请求、HTTP/认证链路或 Agent 工具规划成功率。模型输入不含参考答案。
本次 31 道可回答草稿中 MC05 严格锚点映射失败，仍实际运行，只排除 ID 检索计分。
6 道无答案候选仍未全文确认，不计算正式拒答准确率。

## 已发现的问题（具体输出已复核，不是自动语义评分）

### 最终运行结果

37/37 completed，37 次实际生成成功，无记录的 API 错误；语料与 Parent 快照校验未变。
37 题引用编号均未越界，但没有完成全量引用语义审核，不能报告“引用正确率 100%”。

以下仅计 30 道可映射的 answerable draft（31 道中 MC05 排除）；6 个 unresolved candidate 不在分母。

| 阶段 | Hit@5 | 证据组覆盖@5 | 全部证据具备比例 |
|---|---:|---:|---:|
| ANN 前 5 | 80.0% | 67.39% | 53.33% |
| Child 重排前 5 | 100.0% | 91.0% | 83.33%（25/30） |
| Child gate 后 | 100.0% | 91.0% | 83.33%（25/30） |
| 最终 packed Child 引用集 | 70.0% | 53.94% | 40.0%（12/30） |

重排 MRR@10=0.8928。最终引用集指标为 Child ID 锚点覆盖，不是答案正确率，也不证明 Parent 正文没有任何相关表述。
本轮各集合最终指标在 @5/@10/@20 相同；不是直接比较不同 K 得出的损失结论。

| 类别 | 可计题数 | 重排 All Evidence@5 | packed 全证据 |
|---|---:|---:|---:|
| multi-child | 9（另 1 映射失败） | 6/9 | 1/9 |
| cross-section | 8 | 6/8 | 1/8 |
| exception | 7 | 7/7 | 5/7 |
| modality | 6 | 6/6 | 5/6 |

6 道无答案候选都生成了回答，未编出所问的金额、日期、错误率、Recall 门槛或保留年限；
但多题对整个 corpus 的缺失作过强断言。只能报告这一观察，不能评分为已确认的正确拒答。
仍未完成全量人工/独立 judge 语义评分；本次不宣称整体回答质量达标。

1. **上下文打包丢失已找到的证据。** CS01、CS02、MC09、EX02 的 gate 后证据组完整，
   packed Child citation 集却不完整。分别只保留 2、3、2、2 个 Child 引用，且 truncated=true。
   CS01 回答遗漏培训交付；CS02 未回答显式重审触发；MC09 未回答 explainability testing；
   EX02 明明检索到了内部评估工具的替代条件，却回答“摘录未说明”。
2. **Token 预算过保守且正文重复计费。** 当前 generation_tokens 使用 UTF-8 字节上界，
   不是 DeepSeek 实际 tokenizer；8192 的预算实际约束的是字节上界单位。Parent 正文后又附完整
   supporting Child，造成内容重复。按最大相关分逐 Parent 贪心装入，未先保住多方面必要证据。
   上述案例 packed 上界为 6817–8093，并不等于模型真实 input tokens。
3. **义务强度与建议混杂。** MC10 先说明 Criterion 21 为 Recommended，后又写
   “Log AI predictions and actions taken as a mandatory component”。MO04 又建议将推荐项
   升格为内部要求；必须区分模型自行提出的建议与源文档义务，不能把引用编号正确当作内容正确。
4. **缺证据回答过度宣称已检查全文。** UN01/02 没编出金额或会议日期，但宣称 corpus
   “does not contain”。本链路只看到检索片段，没有完成全库缺失性证明，正确应限定 available excerpts
   “do not provide sufficient evidence”。同时 fixed researcher 报告模板导致简单问题回答冗长。

## 下一步建议（本轮没有实施修复）

- 优先做 evidence-first packing：先保留完整、去重的 supporting Child，再用剩余预算扩 Parent；
  不基于测试 gold 决定线上选择，不将 Parent 当作 evidence。
- 校准生成 token estimator，分别报告实际模型用量与保守上界；减少 Parent/Child 文本重复。
- 扩展选择策略考虑不同问题方面的证据覆盖，仍保留完整 Child provenance；不能只提高 ANN K。
- 修复后对同一 37 题、同一 snapshot 做固定条件对照，观察 gate→packed 的证据保留率和真实答案变化。
- 收敛问答提示词：先直接回答，明确 not-required / recommended / mandatory，明确局部缺证据边界。
- 最后审核新增参考答案和无答案候选，再发布正式指标。暂不继续扩 5–10 PDF。

## 产物

- `report.json`：配置、数据与代码指纹、全部选题和运行状态。
- `DEV2-*.json`：逐题候选及距离、重排分数、gate、Parent、上下文、引用、真实模型答案、阶段指标。
- `summary.json`：草稿检索指标和运行数量；不包含伪造的语义正确率。
- `answers_review.md`：问题、草稿参考答案、实际回答及引用原文，供逐题审核。

新增两个隔离评测入口和两项测试，既有严格 reviewed benchmark 不放宽。272 项测试通过、5 项既有跳过。
所有运行错误应保留；正文中的个案审阅不能被换算成未完成审核的整体正确率。
