# Controlled Retrieval V6：原文绑定与证据集合认证

2026-09-10：生产Inspector固定合成范围检查6/6通过，未改生产策略、未运行正式50题。详见 [Inspector隔离验证](INSPECTOR_SCOPE_SMOKE_RESULTS.md)。可进入冻结候选版本与真实回归准备阶段，不代表整体质量或上线验收通过。

最新接手修复见 [范围保留与比较焦点修复](CONTROLLED_RETRIEVAL_SCOPE_FIX.md)。已增加不可由模型覆盖的question_scope和subject×dimension焦点；8题第二次开发smoke可解析且枚举独立，场景角色标签仍不完美。未运行正式50题，未证明Inspector语义质量提升。以下保留此前阶段记录。

## 本轮范围与状态

本轮只处理确定性契约缺陷并做可审查的小规模合成回归，不运行 frozen benchmark 的正式 50 题。数据库、模型、题库、gold mapping、快照、candidate/rerank 上限、token/调用预算、Query Optimizer 和生成架构均未改变。

当前结论：V6-A 的三处已复现确定性缺陷已修复并通过贯穿测试；V6-B 已加入 Planner 契约简化和必要的确定性兼容恢复，但 Planner-only smoke 仍有共享范围和字段语义问题，因此不允许据此宣称 Planner 可用或进入 full-50。

## 已实现的确定性约束

1. `build_evidence_set` 只接受按顺序的 `r1..rN`、`complete|supported`、answer-bearing inspection 项；错误 ID、partial/missing 和非 alternative bundle 不得进入 core contract。候选 Child 仍可保留给后续上下文，但 `selected_core_child_ids` 和 `uncovered_requirements` 保持 fail closed。
2. 合法 OR bundles 仍可选择任一完整替代集合；单个 bundle 内的所有 Child/span 成员仍是 AND，选择不能用子集替代完整 bundle。
3. 明确标记为 complementary 的多个 bundles 被拒绝，不能分别冒充 OR 替代集合。若语义上确实是互补证据，应由 Inspector 返回一个包含全部 AND 成员的 bundle。
4. comparison Planner 计划允许一个主体对应多个 requirement；每个 requirement 必须绑定一个主体和一个维度/对象，所有主体的维度集合必须一致且完整匹配。若 `subject_spans` 缺失，只有 anchor 精确且唯一匹配已声明 comparison subject 时才程序恢复，并记录来源。enumeration 单 requirement 只有在保留 subject/object/dimension/condition 等范围绑定时才可接受；重复整句不能冒充分解。这仍只是部分结构约束，不证明枚举语义完整。
5. requirement ID 不再依赖模型提供；缺失时由程序生成 `r1..rN`，历史正确的显式 ID 仍只接受规范顺序。yes/no 或 modality 不能只绑定疑问词/义务词；单一内容 anchor 可在有 modality 时恢复为 object，并记录来源。exception 必须绑定 object/subject/condition，或明确引用前一 requirement 的 object。
6. Planner 使用 `qID` 或 `start_id/end_id` 词范围恢复 anchors：`anchor_spans`、`subject_spans`、`object_spans`、`dimension_spans`、`condition_spans`、`modality_span` 和 `comparison_subject_spans`。程序依据 catalog 还原原文；新的 span 字段不接受模型自行计算的字符偏移。旧的字符串字段暂保留兼容读取。
7. 同一 Child 的不同 span 可以被多个独立 requirement 共享；覆盖按 Child 集合认证，不能因为共享 Child 而丢掉各自 requirement 的 span 约束。

## 不能由程序单独证明的语义

- 枚举是否真的包含问题要求的所有事项，除重复/空/过宽结构外仍需要 Planner 语义判断。
- 通用条款是否只提供场景的部分支持，仍需要 Inspector 根据 bound subject、dimension、condition 判断；程序不会把 topical/general evidence 自动升级为 complete。
- 两个 evidence bundles 在内容上是互补还是独立替代，必须由 Inspector 正确表达；程序只拒绝显式的 complementary 多 bundle 违规，不用关键词特判。
- enumeration 的共享范围是否完整、scenario 范围是否被正确标为 condition 而非 object、comparison anchor 是否包含足够询问内容，仍需要 Planner 语义审查；不因结构合法而自动放行。

Inspector 提示已要求每个 bound requirement 独立返回，complete 的单一 bundle 必须覆盖该项全部绑定内容；否则只能 partial/missing，不能依赖一个 broad requirement 的 `complete=true`。`bundle_relation` 已写入 Inspector 契约并贯穿适配、校验和 Builder：单个 complementary bundle 可作为一个 AND 集合，多于一个的 complementary bundles fail closed，不得被默认为 OR。

## 验证

- controlled retrieval 相关测试：`41 passed`。
- parent pipeline、agent context、controlled retrieval 合计：`55 passed, 1 warning`。
- Docker 测试容器内全套测试：`331 passed, 6 skipped, 1 warning`。Windows 主机直接运行全套时有 12 个既有数据库测试因无法解析 Docker 内部主机名而失败；不是本轮代码断言失败。
- Ruff check、Ruff format check、`git diff --check`：通过。
- V6-B Planner-only smoke 已保存原始 Planner JSON、规范化计划、错误位置和逐题人工审查，目录见 `backend/data/evaluation/controlled_retrieval_v6_audit/planner_smoke_20260909T210741/`。原 5 题加 3 个预先固定的迁移表述共 `8/8` 结构上可解析：comparison 2×2、完整 yes/no、exception 对象关联得到改善；但 enumeration 丢失共享范围，scenario 的 object/condition 角色仍不稳定，comparison anchor 质量也有风险。`8/8` 不能算语义通过，也不是正式质量成绩。上一轮包含 Inspector 的 5 题诊断仍保留在 `smoke_20260909T201133/`，前一版 5 题 Planner-only 记录保留在 `planner_smoke_20260909T210053/`。
- 本轮未运行正式 full-50；没有新的 benchmark coverage、EGC 或 fallback 成绩。

## 后续优先级

下一步优先审查 Planner 的共享范围表达和 anchor/subject/object/condition 角色契约；只允许通用接口改进，不对 MC04/MC06/CS07 做特判。不得用题目 ID、gold Child 或失败题内容特判；不换模型、不扩库、不扩大 k，也不承诺覆盖指标必然超过 `38/43`。
