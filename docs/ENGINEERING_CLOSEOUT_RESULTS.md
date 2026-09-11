# Engineering Closeout Results

> 2026-09-11 final deterministic repair and audit addendum: see
> [FINAL_ENGINEERING_CLOSEOUT_20260911.md](FINAL_ENGINEERING_CLOSEOUT_20260911.md).
> The current audit addendum records 8 agent-reviewed cases and 42 provisional
> evidence rechecks; it does not constitute human sign-off or a full 50-case
> semantic quality metric.

日期：2026-09-10

分支：`develop`
基线提交：`fc9aa91b205563814b5dd86f63dc5b5ef960aefc`

## 结论

本轮完成了可复现 Demo 所需的 A–D 工程收尾，但不构成公网发布或政策答案质量签核。

| 范围 | 状态 | 说明 |
|---|---|---|
| A 状态合同 | 已实现，隔离数据库已验证 | API、SSE、history、Agent/Direct、UI 使用同一组状态；旧记录保守为 unknown/not_assessed。 |
| B 生成与引用 | 工程实现完成，语义审核 pending | 固定输入 8 题诊断和一次 50 题 generation-only 均完成；编号/身份检查通过，但没有自动声称语义支持。 |
| C 注册安全 | 已实现，单测通过 | admin 注册必须提供配置的 secret；普通注册仍默认为 user。未在冻结库创建账号。 |
| D Demo 交付 | 可复现条件已文档化 | 前端构建通过，错误提示与覆盖文案已更新；本轮未再次执行浏览器验收，历史 UI 产物不能替代当前版本复验。 |

整体判定：`needs-fix / environment-blocked`。在隔离数据库、已应用聊天状态迁移、有效模型凭据和人工答案复核完成前，不建议作为公网或客户正式政策决策系统上线。作为带人工复核边界的本地研究辅助 Demo，可以按 [Demo Runbook](DEMO_RUNBOOK.md) 运行。

## 1. 接手核对与冻结范围

接手时工作区已经存在大量未提交改动，当前 diff 同时包含此前 P0/P1/P2、Controlled Retrieval、UI 和本轮收尾内容；本轮没有 reset、clean、commit、push、merge 或部署，也没有把聚合 diff 冒充成本轮单独新增。当前仍在 `develop`，工作区保持 dirty。

已核对并保留以下冻结材料：

- 题库、gold/evidence groups、Child/Parent、向量数据库快照和模型配置未改动。
- C 检索原始产物：`backend/data/evaluation/selection_c_public/draft_20260910T092014171489Z/`。
- 既有 recovery/review/UI 产物未覆盖；新的生成产物写入新目录。
- C 原始检索口径沿用：50 总题、43 个 evidence-group 计分题；Complete@5 `36/43`、Complete@20 `40/43`、Macro EGC@20 `95.03876%`。
- 本轮没有重新检索，因此没有更新上述检索质量成绩，也没有宣称召回率提升。

默认行为仍是 `reranker_top_k + original`；P2 `per_document_backfill_v1` 仍是显式实验策略，不在本轮改成默认。

## 2. 工作包 A：状态合同

新增 `backend/app/modules/chat/contracts.py`，统一以下字段：

- `generation_allowed`：是否允许进入生成，不等于完整或正确。
- `coverage_status`：`not_assessed / partial / complete / no_context`。
- `coverage_sufficient`：只有明确完整验证且最终 packed evidence 仍存在时才为 true。
- `answer_status`：`pending / streaming / generated / withheld / error / unknown`。
- `evidence_sufficient`：仅作为兼容字段，不再从非空来源列表推断。

覆盖规则：

- 有 Child/source 不再自动等于 complete。
- `partial` 可以生成诚实的部分回答，但不能标记完整。
- `no_context` 且实际拒答时，状态为 withheld。
- 中断、provider 异常、取消不会因为已经产生 token 就写成 generated。
- 旧 history 缺少新字段时为 `unknown/not_assessed`，不会从旧 `status=complete` 或旧 `evidence_sufficient` 反推完整覆盖。

持久化变更：

- 新增 `backend/database/migrations/020_add_chat_status_contract.sql`，仅添加 nullable 列和约束，幂等、无 DROP、无旧记录回填。
- `backend/database/init.sql` 与 `compose.yaml` 已接入新字段/迁移顺序。
- 后端启动时只读检查三列；缺失时抛出明确的“需要 migration 020”错误，不自动改库、不吞掉 DB 写入异常。

最终 Agent 打包会按最终保留的 Child ID 过滤 document citations；没有把旧 Child 重新编号或把 Parent 背景自动升级为 Child 证据。

## 3. 工作包 B：固定输入生成与引用

实现内容：

- `prompts.py` 与 Agent final prompt 共用简洁的直接回答、条件/期限/义务强度、邻近 Child 引用和明确缺口规则。
- 移除强制六段式和未被问题询问的泛化缺口清单倾向。
- `validate_answer_citations()` 只检查引用编号和最终 Child 身份；`semantic_support_checked=false` 是有意保留的审计边界。
- 新增 `backend/evaluation/generation_diagnostic.py`，只读取既有 C 运行的 question/context/citations，不读取 gold、review 或候选修正版。
- 每题最多一次生成调用，SDK retry 和外层 retry 均为 0；没有新增检索调用。

### 固定 8 题诊断

目录：`backend/data/evaluation/closeout_b_diagnostic/diagnostic_20260910T111949449678Z/`

| 项目 | 实际结果 |
|---|---:|
| 题目 | 8 |
| 单题生成调用 | 1 |
| 成功生成 | 8/8 |
| 检索调用 | 0 |
| 外层重试 | 0 |
| 引用身份检查通过 | 8/8 |
| 未知引用编号 | 0 |
| 语义支持自动检查 | 0；均为未验证 |

### 一次 50 题 generation-only

目录：`backend/data/evaluation/closeout_b_full_generation/diagnostic_20260910T113645096608Z/`

| 项目 | 实际结果 |
|---|---:|
| 题目/单次调用 | 50/50 |
| `generated_pending_review` | 50 |
| 检索调用 | 0 |
| 外层重试 | 0 |
| 引用身份检查通过 | 50/50 |
| 未知引用编号 | 0 |
| 语义支持自动检查 | 0；不作语义签核 |
| 延迟 | 最小 0.53s，平均 2.69s，最大 13.22s |
| token usage/cost | unavailable；本工具没有把 provider usage 当作 0 |

这 50 题只是固定上下文上的生成工程回归。它不改变 Complete/EGC，不证明 UN02/UN05/UN06 的 Parent–Child 错配已经消失，也不把 `generated_pending_review` 变成人工 `pass_complete`。既有风险题、部分覆盖题和答案引用仍需逐断言人工审核。

## 4. 工作包 C：注册权限

`backend/app/modules/auth/service.py` 恢复了服务端 admin secret 校验：

- 未配置 secret、请求缺失/为空/错误均拒绝。
- 正确 secret 使用 `hmac.compare_digest`。
- 拒绝时不创建 repository 用户，不记录或回显 secret。
- 普通注册不需要 secret，默认 role 仍为 user。

测试覆盖未配置、缺失、空值、错误、正确 admin secret 和普通注册。未在现有冻结数据库创建测试 admin，也没有修改已有账户。

## 5. 工作包 D：UI 与交付

前端：

- history、SSE、citation drawer 读取新的覆盖/答案状态。
- `not_assessed`/`partial` 显示“Evidence coverage not confirmed”类提示，不显示成完整或直接拒答。
- 网络 fetch 中断显示 `Connection interrupted. Please retry.`，不把 provider 原始异常或密钥展示给用户；不自动重发。
- Document Analysis 保持 selected-only，Open Discussion 保持 full-corpus；没有顺带启用 web search。

本轮 `npm run build` 通过。历史 UI 验收产物在 `backend/data/evaluation/ui_acceptance_20260910/`，但状态合同和文案在本轮有更新，因此没有把历史浏览器结果冒充当前版本的完整浏览器验收。当前 UI 状态为“构建已验证、浏览器复验 pending”。

## 6. 测试与真实验证

### 自动化测试

使用临时独立 `ankane/pgvector` 数据库容器加载 schema、migration 018 和 migration 020；未连接或写入现有 `policy-parent-child-db` 冻结快照。前一轮 A–D 的完整测试结果（历史记录）：

- `406 passed, 6 skipped, 1 warning`。
- 唯一 warning 是既有 Starlette/AnyIO 弃用提示。
- 6 skipped 为项目既有隔离数据库/可选测试，不以 skip 计 pass。
- 迁移、聊天 history 集成测试在临时库执行；现有冻结库没有执行迁移。

离线环境下的工具检查：

- `ruff check app tests`：通过。
- `ruff format --check app tests`：通过（226 个 Python 文件已格式化）。
- `git diff --check`：通过（Git 仅提示工作区换行风格）。
- `python -m compileall -q app evaluation`：通过。
- `npm run build`：通过；Vite 仅提示现有大 bundle warning，不影响构建退出码。

### 调用预算

本轮真实模型调用为固定 8 题诊断一次 + 一次 50 题 generation-only，共 58 次单题生成；无检索调用、无外层重试、无自动 Judge、无第二轮 50 题。模型为运行时解析出的 `deepseek/deepseek-v4-flash`，没有修改模型、采样参数或检索配置。

## 7. 质量与风险清单

仍需保留/人工复核的项目：

- UN02、UN05、UN06：历史审核已发现 Parent 事实挂到不支持该事实的 Child；本轮只完成引用身份检查，不宣称语义修复。
- MC06：证据仍是 partial，不能因生成成功标成 complete。
- CS07：C 运行的 selected/packed 覆盖仍为 `0/3`；不能写成已恢复。
- MC04：C 运行由 reranked full 变为 selected/packed `2/3`；P2 的历史回放只减少 selected→packed 损失，不等于上游选择恢复。
- Parent 正文扩展与 Child 证据的关系仍需人工检查，Parent-only 事实不得自动获得 Child citation 身份。
- 50 题答案没有全量独立人工签核；8 题有 agent review，42 题为 provisional evidence recheck。生成器的 `valid_identity` 不是 faithfulness、relevance 或 completeness。
- 当前 UI 没有用本轮新版本做浏览器全路径复验；需要隔离 DB、端口和测试账号。
- 现有冻结数据库没有 migration 020；启用新后端前必须在目标隔离/部署库按迁移流程应用。代码会明确阻止缺迁移启动，不会静默降级。
- 检索覆盖与答案质量没有因为本轮而重新计分；C 的 `40/43`、`95.03876%` 只作为历史基线。

## 8. 哈希与路径

代码基线：`fc9aa91b205563814b5dd86f63dc5b5ef960aefc`。当前关键文件 SHA-256：

| 文件 | SHA-256 |
|---|---|
| `backend/app/modules/chat/contracts.py` | `036458BAF88A5643F30255E50239910787C0E3935BC797AF81D42A58A93308B6` |
| `backend/app/modules/chat/router.py` | `7EF7E670912C45CF62E1260256CE377E33376A72CBACBBA7D778FA0A1730C2C8` |
| `backend/app/modules/chat/rag/generation.py` | `ACC99046D0CC1FCB3935B37E5F1558EDFD5C73446F80F9016F68E1864C0D83B3` |
| `backend/app/modules/auth/service.py` | `19EC22A80B17FE8368E891D899B14667057F77964B4060F1E4509CA37C30DAE4` |
| `backend/app/main.py` | `A378DC6AA4983B2A020CFC9E4A1BCCC793ACE5127CCCFE5800266BACEB17E935` |
| `backend/database/migrations/020_add_chat_status_contract.sql` | `B422814CFE97356E0C5A860D20B0C5D2355376FB76EACF89E79668A221ED3F12` |
| `frontend/src/pages/ChatPage.jsx` | `7D810D6DBD12EA82DAD4CB20999FD9CD71E063F05882C305EC2A3535E51C2477` |
| `backend/evaluation/generation_diagnostic.py` | `74FB45982D6171699EF02C1AB9215BB76B15F6DA823EB46DE421B87CA6F20CCB` |

评测产物哈希：C source report `89E17FB48FE2898DA1F5FDE92B2BEFA3A966998101919207CE96711A773BFBE9`；8 题 report `9E33BC11F75322C89AED095C0DD7A55A50F0FCA66A8EF388FB26CE2002A6755F`；50 题 report `B450CC7FB794C940AAC7779A9FAD5023BB34A3C0152C6930BACADA8DA8EBEC62`。

## 9. 交接决定

- 可保留：状态合同、最终 Child citation 过滤、简洁生成规则、admin secret、回放/诊断工具、默认 `original` 回退。
- 不默认启用：P2 packing 实验；不重启 P1.1/selection 调参。
- 不可宣称：召回率提升、答案质量提升、50 题人工通过、无幻觉、可公网部署。
- 下一步最高优先级：在隔离库应用 migration 020 后执行当前版本浏览器验收，并在有授权模型凭据时对已发现的 UN02/UN06 进行一次同输入局部修复验证；若发现语义引用错配，降级为“检索与原文核对 Demo”，不通过重跑碰运气解决。
