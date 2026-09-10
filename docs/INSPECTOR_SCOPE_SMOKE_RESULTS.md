# Inspector 独立范围验证 — 2026-09-10

结论：6个预先固定的合成案例全部通过。本轮没有修改生产代码或提示词，没有正式50题成绩。

## 方法

新增 `backend/evaluation/inspector_scope_smoke.py`，在单独评测进程替换 orchestration callback，直接使用生产 `retrieve_controlled` 内的 Inspector、真实模型客户端、原文span映射、Validator和Builder。每题只调用一次Inspector，共6次；不执行Planner、embedding、ANN、reranker或答案生成。数据库只用于既有模型配置读取，没有数据写入。

题目、人工要求和Child均为固定合成数据。expected字段只在调用结束后比对，不传给模型。原始合成文本、问题、模型结构响应、规范化inspection与核心集合全部保存在：

`backend/data/evaluation/controlled_retrieval_v6_audit/inspector_scope_20260910_01/`

生产源码SHA256：`21097f7bce4179e6bf939f407eb84f01e1815b3283cf05ac813a4ee3cd1e6bad`。

## 结果

| 案例 | 预期 | 实际 |
|---|---|---|
| 完整场景支持 | complete | complete |
| 错误范围，另指未提供章节 | 不充分 | missing |
| 纯主题背景 | 不充分 | missing |
| 明确否定义务 | complete，negative | complete，negative |
| 比较只有一方数据 | 一方complete、一方不充分 | complete / missing |
| 身份与保留要求需要两条证据 | complete，bundle必须含两个Child | complete，两个AND成员保留 |

6/6是本次合成检查通过数，不是回答准确率、不是真实政策证据覆盖率。错误范围案例有明确不适用提示，短上下文比真实长文档容易；不能由此证明CS07等问题已解决。尚未验证Planner与Inspector组合、真实候选池噪声和端到端packing/generation。

## 下一步

当前有理由结束反复字段修补，冻结这个候选版本并准备一次同配置50题回归；回归前核对dataset/Child/Parent/model/config哈希。依然不保证超过38/43，不以合成测试替代真实回归，不调整gold或阈值。正式回归后按阶段解释变化，尤其检查错误放行与完整却拒答；结果未改善则保留失败结论，不追加调参后重算同一版本。
