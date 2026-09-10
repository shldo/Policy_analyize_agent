# Controlled Retrieval V4 设计说明

## 目标与边界

V4 只修复现有受控检索的四条职责链路：需求计划、查询构造、Child 证据校验和证据集合选择。Planner 与 Inspector 仍是现有调用，Query Optimizer 和 Evidence Set Builder 都是程序逻辑，不增加 agent、独立 query rewrite 或 judge 调用。

保持 V3 的运行不变量：默认 `controlled_retrieval_enabled=false`；ANN candidate cap 30、最终 Child cap 8、现有 context/token/Parent 预算和阈值不变；一条原始 query 加最多两个 gap query；Planner 加最多两次 Inspector，共最多三次 reasoning calls；Parent 只进入生成上下文，不能充当 Child coverage。

## 四链路契约

1. Requirement Planner 输出 `question_type` 和按顺序编号的 `r1..rN` requirements。每项包含一个或多个来自原问题的精确 `anchors`，可选的 subject/object/dimension/conditions，以及闭集 metadata。程序校验 anchor、ID、数量和比较双方；枚举要求不能用同一个整句重复冒充多个事项。
2. Query Optimizer 只接受 requirement 的原文 anchor、Child/span 原文或 section metadata 中实际出现的术语，以及预声明白名单映射。程序构造最终 gap query，并记录 requirement、来源、原文术语和 fallback；无效建议退回原问题与该 requirement 的原文 anchor。最多按未满足 requirement 顺序选择两个去重 query。
3. Evidence Validator 将每项规范化为 `complete|partial|missing` 和 `answer_bearing|supporting|background|missing`。`complete` 必须有至少一个有效 `core_bundle`；bundle 内 Child/span 是 AND，多个 bundle 是 OR。yes/no/modality 使用 `affirmative|negative|conditional|not_established` 闭集结论。空 background/supporting 安全归一为 missing，非法 span/quote/requirement 继续 fail closed。
4. Evidence Set Builder 只使用最后一次 inspection 的 core bundles，先在 Child cap 内选择能覆盖最多独立 requirements 的确定性 core 集合，再加入 supporting/filler。不同 requirement 之间允许共享 Child；core bundle 被 packing 丢失时 coverage 失败。Parent pipeline 和 Agent 最终 gate 都按选中的 bundle 校验，而不再要求所有可替代 bundle 同时存在。

## 风险与验证

主要风险是旧 trace/测试仍只有 `supported + evidence`，因此保留读取兼容并把旧 evidence 解释为单一 core bundle；新运行只产生 V4 字段。合成测试覆盖 planner 绑定、query 来源、否定/推荐/例外、OR/AND、跨 requirement 共享、supporting 不挤占 core、stale inspection、packing 丢失和 Classic/Agent fail-closed。完成后运行相关 pytest、Ruff 和 diff 检查；正式冻结后只做离线汇总，不继续改质量策略。
