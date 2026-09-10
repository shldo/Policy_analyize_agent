# 部分回答策略：生成许可与完整证据分离

日期：2026-09-10。

## 产品行为

默认允许基于检索上下文回答有依据的部分，不再因为一个子问题缺证据而阻断整题。缺失部分由回答明确指出，不能把未找到证据说成现实中不存在该事实，也不能把部分答案标为完整支持。

这是政策研究助手的行为调整，不是声明模型能够自动判定所有答案正确。

## 数据字段

| 字段 | 含义 |
|---|---|
| `generation_allowed` | 存在已打包且有来源的上下文，允许模型尝试回答有依据的部分；不是相关性/正确性证明 |
| `coverage_sufficient` | 仅当有效的 Controlled 检查和最终打包证据共同支持全部要求时为 true |
| `coverage_status=not_assessed` | 默认 Classic 未运行完整性 Inspector，或 Inspector 验证无效；不得声称已验证完整覆盖 |
| `coverage_status=partial` | Controlled 验证后仍有缺口，但上下文可用 |
| `coverage_status=complete` | 通过有效的完整性检查且证据在最终上下文保留 |
| `coverage_status=no_context` | 没有可用上下文，仍不能编造答案 |

新默认路径中，`evidence_sufficient` 不再用于生成路由，保持与已验证完整性一致。旧严格配置保留历史语义供对照，不据其布尔值计算新的完整性指标。

## 链路变化

BM25 + vector → RRF → reranker → 非空 Child → Parent expansion / token packing → 有上下文则生成 → 支持的内容引用、缺失的部分说明。

新默认路径不再用统一向量距离、reranker 阈值或最短字符数否决所有来源的候选。这些分数仍保留用于观察，不被 RRF 分数替代。相关性排序不保证证据正确，模型仍必须仅根据实际上下文回答；上下文完全不支持问题时，允许模型说明无法回答，不要求强行形成“部分答案”。

Classic、Agent 文档工具和最终 Agent context packing 已区分生成许可与证据完整性；Controlled 定向检索也遵循新策略。权限过滤、引用身份、token budget 保留；Live Web 检索实现未修改。

## 配置

```dotenv
RAG_ALLOW_PARTIAL_ANSWERS=true
```

默认 true。设为 false 可复现旧严格 Gate 路径。未更改 Controlled 的默认关闭状态。现有后端进程需重启加载配置。

## 测试

- 新增测试覆盖：BM25 命中的距离不再一票否决；无上下文仍阻断；部分覆盖允许生成但完整标志为 false；Inspector 错误不认证覆盖；Agent 最终打包缺证据不再整题拒答；所有 persona 加入部分回答指令。
- 原严格 Gate 测试通过显式 false 配置继续运行，没有删除其断言，也没有修改 benchmark/gold。
- 本轮全套测试：358 passed、6 skipped、1 条依赖弃用 warning。

## 本轮评测设计

使用 `policy-parent-child-dev50-v1` 的原 50 道 development 题和同一 5-PDF/332-Child 库；不改问题、gold evidence groups、模型、向量与 Parent。

每题只召回、重排一次；同一批 ranked candidates 分别进入：

1. 旧严格 Gate + packing；记录可否生成、保留的 Child 和覆盖指标，不再调用一次生成。
2. 新部分回答策略 + packing；记录同样指标，并实际调用配置的生成模型。

额外保存 dense、BM25、RRF、reranked 和 packed 各阶段指标。两组上游完全相同，因此差异只能说明 Gate/打包保留变化，不能声称 embedding 召回得到改善。

结果目录：`backend/data/evaluation/hybrid_partial_answers/draft_20260910T021612893235Z/`。

只有映射成功的可回答题进入 evidence 指标分母；未完成无答案复核的题不得用作正式拒答正确率。`generated_pending_review` 只表示 API 返回文本，既不等于完整答案，也不等于答案正确。引用语法检查不等于引用语义正确。

最终分数和抽查结论见[50 题结果](PARTIAL_ANSWER_RESULTS_20260910.md)：全部完成，43 题评分，
RRF Complete@20 为 41/43、reranker 为 42/43、最终上下文为 40/43；旧/新 Gate 的最终覆盖相同。
