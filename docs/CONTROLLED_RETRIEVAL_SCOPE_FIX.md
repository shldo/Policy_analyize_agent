# Planner 范围保留修复（2026-09-09）

## 本轮实际修改

由主 agent 接手增量修复，未改数据库、模型、检索阈值、Builder、packed gate 或冻结题库，未提交/发布。

1. 每个规范化 requirement 的 `question_scope` 由程序直接赋为完整原问题，模型不能覆盖。这样共享范围、否定和场景限定不会因可选语法字段漏词而从契约消失。
2. comparison 的焦点由已验证的 subject + dimension 构造，不再将 `Compare` 当作检索焦点；旧 anchor 留在 `original_anchors`，保留恢复来源。
3. Inspector 明确区分“原问题范围”和“证据”：原问题是每项要求的权威范围；可选 subject/object/condition 是提示而非全部条件。范围中含某词不证明证据支持它，不自动上调充分性。
4. Inspector 请求只发送一次原问题，不重复发送每个 requirement 的 question_scope，控制输入开销。
5. Planner 明确示例 q0 不是默认选择，并用非 benchmark 的通用例子解释枚举应独立拆分、场景条件不需要强制拆成不同问题。

这不是精确语法分析器。object/condition 角色仍可能不稳定；当前修复保证原文含义的完整来源保留，不声称模型已经正确理解或充分取证。原 Inspector 本来就接收 question；本轮新增的是可审计 scope 契约与明确使用规则，不是证明它能解决 CS07 的新证据机制。

## 验证

- 新增4个测试先复现失败，再修复：共享枚举范围、comparison焦点、碎片化角色下的完整场景范围、模型不能覆盖范围。
- 全套：336 passed、5 skipped、1既有warning（显式数据库测试环境）。
- Ruff检查通过；未运行正式50题。
- 原8题保持不变，进行了两次开发期 Planner smoke，均保留结果，没有覆盖历史。

第一次：`backend/data/evaluation/controlled_retrieval_v6_audit/planner_scope_fix_20260910_01`。
目录名日期是命名失误；report实际开始时间为2026-09-09 UTC。8题可解析，但枚举被合为1题，因此未计语义通过。

第二次：`backend/data/evaluation/controlled_retrieval_v6_audit/planner_scope_fix_20260909_02`。
补通用枚举示例后，8题可解析，要求数依次为1、2、4、1、2、1、4、1。

## 第二次逐题检查

| 类型 | 观察 |
|---|---|
| yes_no | 发布行为、agencies和义务保留，不再只有疑问词 |
| enumeration | oversight/logging独立；safe AI use完整原文在每项scope中保留，condition字段仍只给safe AI |
| comparison_2x2 | Alpha/Beta × cost/speed四个明确焦点；Compare不再作为唯一anchor |
| scenario | safeguards焦点及完整供应商/敏感客户数据范围保留；语法角色仍碎片化，不能宣称角色标注正确 |
| negation_exception | 第二项通过已有明确来源恢复watermarking对象；完整原问题保留 |
| yes_no_variant | 同类完整命题保留 |
| comparison_variant | Orion/Nova × cost/speed四项明确绑定 |
| scenario_variant | supplier/private customer records条件及safeguards焦点保留 |

本轮可以确认范围保留与comparison焦点错误已修复；不能用8题单次结果证明Planner普遍可靠。未调用检索/Inspector，因此不存在新的证据覆盖、答案质量或错误放行成绩。

## 下一验证点

冻结当前Planner修改，接下来用固定合成Child测试Inspector是否实际遵守scope（完整支持、缺场景条件、背景、否定、比较缺一方）。不能继续只看Planner字段名称，也不能把完整原问题当作“证据已完整”。这一验证通过前不进行正式50题或默认启用。
