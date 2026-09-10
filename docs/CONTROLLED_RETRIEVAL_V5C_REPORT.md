# Controlled Retrieval V5-C 中文报告

## 结论

V5-C 不通过。

本轮完成了 V5-B 的 8 个 scored fallback 诊断、保存响应离线重放、合成回归和一次受控 full-50。8 个原始 fallback 全部是应保持 fail-closed 的 Planner 语义契约违规，没有安全的格式归一化修复。受控 full-50 没有新增 false sufficient，但接口目标未达成：error fallback 为 `13/50`、scored 为 `10/43`，均未达到 `≤1/50`。

同 V5-B 的源码、数据集、Child/Parent 快照、运行时模型和检索预算哈希一致；V5-C 与 V5-B 的差异包括 Complete@5 增 1、fallback 增 2，属于同配置下的模型响应随机差异，不能作为改进宣称。

## 1. V5-B 8 例 fallback 分类

完整故障表见：`backend/data/evaluation/controlled_retrieval_v5c_audit/v5c_fault_table.md`。

| case_id | 失败阶段 | 原始错误 | 分类 | 是否安全修复 | 处理 |
|---|---|---|---|---|---|
| DEV-AU02 | Planner validation | `Invalid requirement anchor` | required anchor 非问题原文可回溯片段 | 否 | 保持拒绝，不能模糊匹配 |
| DEV-TS02 | Planner validation | `Invalid requirement anchor` | required anchor 非问题原文可回溯片段 | 否 | 保持拒绝，不能改写要求 |
| DEV2-EX06 | Planner validation | `Invalid requirement plan` | requirements 为空 | 否 | 保持拒绝，不能补造要求 |
| DEV2-MC02 | Planner validation | `Invalid requirement anchor` | 多个 required anchor 非原文片段 | 否 | 保持拒绝，不能凭空绑定 |
| DEV2-MC07 | Planner validation | `Invalid requirement plan` | requirements 为空 | 否 | 保持拒绝 |
| DEV2-MO03 | Planner validation | `Invalid requirement plan` | requirements 为空 | 否 | 保持拒绝 |
| DEV2-MO04 | Planner validation | `Invalid requirement plan` | requirements 为空 | 否 | 保持拒绝 |
| DEV2-MO06 | Planner validation | `Invalid requirement plan` | requirements 为空 | 否 | 保持拒绝 |

8 例中没有 JSON 截断、结构损坏、超时、连接或服务故障；也没有 optional 字段缺失、单值/列表包装或预声明枚举别名可安全归一化的案例。3 个 unscored fallback（UN04/UN05/UN06）同样是空 requirements，不计入 43 题分母。

## 2. 本轮修改与边界

V5-C 没有新增运行时代码、提示词、检索策略或语义质量策略修改。已有 V5-A 的确定性规则保持不变：optional 字段可丢弃为无绑定、字符串与单元素列表可兼容、已声明枚举可大小写归一、重复项去重；required requirement、required anchor、比较双方和条件语义仍必须可回溯，否则拒绝。

本轮新增的是离线审计和报告文件，不覆盖旧运行目录：

- `backend/data/evaluation/controlled_retrieval_v5c_audit/`
- `backend/data/evaluation/controlled_retrieval_v5c_formal/draft_20260909T105539685251Z/`
- 本报告及指导 MD 的状态更新

没有 commit、push、merge、release、数据库写入或 benchmark 特判。

## 3. 验证结果

- 相关测试：`34 passed`。
- 合成回归：10 项全部通过，覆盖最小 schema、optional 缺失、单值/列表、枚举大小写、多 requirement 保留、虚构 anchor、缺必填语义、损坏 JSON、normalization 不提升 evidence、最终 gate 不可绕过。
- 全套测试：数据库正确连接配置下 `310 passed, 6 skipped, 1 warning`。默认测试容器地址指向 localhost 时曾出现 12 个数据库连接失败；切换到现有数据库容器网络地址后 14 个相关数据库测试全部通过。
- Ruff check：通过。
- Ruff format check：通过。
- `git diff --check`：通过；仅有既有 LF/CRLF 提示。
- 离线重放 V5-B：50 个保存响应中 39 个接受、11 个拒绝；scored 拒绝 8 个、unscored 拒绝 3 个；兼容重放没有丢失 requirement，MC10 仍接受。该结果不是新 benchmark 成绩。

## 4. V5-B / V5-C / V3 指标

| 指标 | V3 长期基线 | V5-B | V5-C |
|---|---:|---:|---:|
| Complete@20 | 38/43 | 38/43 | 38/43 |
| Macro EGC@20 | 93.72093023255813% | 92.5581% | 92.5581% |
| Complete@5 | 36/43 | 37/43 | 38/43 |
| Macro EGC@5 | 91.9767% | 91.9767% | 92.5581% |
| final sufficient | 32/43 | 31/43 | 31/43 |
| 全量生成 | — | 32/50 | 32/50 |
| error fallback | 2/50；scored 1/43 | 11/50；scored 8/43 | 13/50；scored 10/43 |

V5-C 的 gold-complete-but-refused 为 10 题：`DEV-AU02`、`DEV-SG02`、`DEV2-CS04`、`DEV2-EX04`、`DEV2-EX06`、`DEV2-MC01`、`DEV2-MC07`、`DEV2-MO03`、`DEV2-MO04`、`DEV2-MO05`。

相对 V5-B，Complete@20 没有新增或退化；final sufficient 恢复 `DEV-TS02`、`DEV2-CS02`、`DEV2-MO06`，退化 `DEV-SG02`、`DEV2-EX04`、`DEV2-MC01`。这些是随机响应导致的 gate/generation 变化，不是 V5-C 质量策略收益。V5-C 相对 V5-B 没有新增 false sufficient，三题仍为 `DEV2-MC04`、`DEV2-MC06`、`DEV2-CS07`；MC10 保持完整并生成。

V5-C stop reasons：`coverage_sufficient=32`、`inspection_or_retrieval_error=13`、`no_new_evidence=4`、`round_limit=1`。Planner validation errors 为 `Invalid requirement anchor=4`、`Invalid requirement plan=9`；query fallback 为 `0`，与 error fallback 分开统计。reasoning calls=`88`，输入/输出/总 tokens=`290063/9644/299707`，平均 retrieval=`9.0106s`，平均 total=`13.1925s`，平均 packed tokens=`4581.6`，最大=`5959`；generation usage 在 runner 输出中 unavailable。

V5-C 正式 trace 没有输出 normalization event；本轮没有新增归一化规则，因此不以“0”冒充额外接口收益。对正式运行保存响应做离线 raw-vs-normalized 推断：37 个 Planner 响应可解析，其中 31 题发生已有规则的归一化，类型计数为单值转列表 27、optional 非绑定/非法值丢弃 12、枚举/未知 modality 归一 7、metadata 非法/未知键丢弃 1；这些不是新 benchmark 分数，且运行时 trace 未逐项记录，是现有可观测性限制。明细见 `backend/data/evaluation/controlled_retrieval_v5c_audit/v5c_formal_normalization_summary.json`。

## 5. MC04 / MC06 / CS07 的 V6 诊断

详细机器可读结果见：`backend/data/evaluation/controlled_retrieval_v5c_audit/v6_trace_diagnosis.json`。

- MC04：一个 broad requirement 包含多个条件；Inspector 判 complete，core contract 选择单一 bundle，coverage_sufficient 提前成立，没有 gap query。优先怀疑 Validator 的条件独立绑定和 Evidence Set bundle 认证过宽。
- MC06：虽然列出两个 comparison subjects，但主体、自治维度和人工检查被压成一个 requirement；Inspector 以一个 complete item 通过，没有 gap query。优先怀疑比较双方没有独立认证。
- CS07：两个 requirement 均被判 complete，但 bundle 可共享同一 Child；最终 packed 缺少第二 requirement 的 gold Child，仍没有 gap query。优先怀疑跨 requirement 隔离和共享 Child 的绑定规则。

最高优先级的通用 V6 假设是：在 Validator 认证前，必须按独立 requirement、comparison subject、condition/dimension 和 evidence bundle 做绑定；当前 broad complete item 或跨 requirement 共享 Child 可在缺少独立证据时提前将 coverage_sufficient 置 true，使补查根本不会执行。V6 只验证并修复这一通用主因，不对本轮三题做特判。

## 6. 哈希与原始路径

- V5-C 原始 full-50：`backend/data/evaluation/controlled_retrieval_v5c_formal/draft_20260909T105539685251Z/`
- V5-B 对照：`backend/data/evaluation/controlled_retrieval_v5b_formal/draft_20260909T095709051737Z/`
- V5-C 离线审计：`backend/data/evaluation/controlled_retrieval_v5c_audit/`
- 数据集 SHA256：`950b8639b459092512f6d4a885440e8eaf22ed828309cc612fbdc8add5c290c1`
- Child 快照 SHA256：`52aca085e534f74883e2f4ef3acd2cf2e5a65001205de05e07f093477aba1895`
- Parent 快照 SHA256：`bd17ce27f0e245ea0066a769670994d9acaae41d3840395125d259a030502786`
- runner source hash：`eb07608fbec685e0c675cf8b85c53c4b6c7b0dbb8510b5f8d9f604c5488e832f`
- 本轮开始前相关文件哈希：`backend/data/evaluation/controlled_retrieval_v5c_audit/pre_formal_source_hashes_sha256.txt`

最终状态：V5-C 不通过，停止在离线汇总，等待指挥 agent 审核；下一轮只进入 V6 独立 requirement 绑定/充分性诊断。
