# 最后一轮工程收尾结果

日期：2026-09-11

分支：`develop`
结论：`needs-fix / environment-blocked`

本轮目标是修复确定性接口问题、补齐可信的离线审计和可复现 Demo 交接，不追逐召回率或完整题数。没有修改题库、gold/evidence groups、Child/Parent/向量快照、运行时模型、检索参数、默认策略或冻结数据库；没有 commit、push 或部署。

## 修改记录

### A：状态与生成接口

- Direct SSE 不再向 `ChatHistoryRepository.finalize_message` 传递不支持的冗余参数；只保存仓储签名支持的 `coverage_status` 和 `answer_status`。
- `complete + coverage_sufficient=false` 在结果和 history 归一化时都降为 `not_assessed`，历史读取不会把执行完成误升级为证据完整。
- suggestions 使用独立的 `suggestions_allowed` 权限信号；允许 Classic 的有依据部分回答，不改变 coverage 事实。
- 新增 autospec direct-stream 回归，实际跑过 `run_retrieval → generate_answer_streaming → finalize_message → SSE` 链路。

### B：引用编号与审计

- `Citation.number` 进入 API/history schema。
- 前端显式编号优先；旧的全量无编号响应仍按数组顺序兼容。显式编号不连续时，未知编号保持不可点击，不按 `number - 1` 猜测，也不重新编号。
- `validate_answer_citations` 保留身份检查边界：合法编号不等于语义支持。
- 新增离线审计工具 [build_answer_audit.py](../backend/evaluation/build_answer_audit.py)，只读取已保存 C 检索和 B 生成产物，不调用模型、不读取 gold 进入运行时。

审计产物：

- [审计索引](../backend/data/evaluation/closeout_e1_answer_audit_20260911_r2/INDEX.md)
- [审计 JSON](../backend/data/evaluation/closeout_e1_answer_audit_20260911_r2/audit.json)
- [8 题 agent review 与 42 题证据 recheck 索引](../backend/data/evaluation/closeout_e1_agent_review_20260911_r2/INDEX.md)
- [agent review 汇总](../backend/data/evaluation/closeout_e1_agent_review_20260911_r2/report.json)

真实结果：50/50 逐题记录，0 个未解析引用号，50/50 的生成输入 hash 匹配源 question/context/citations；数据库快照没有被脚本冒充核验，状态为 `not_checked`。审计字段“已登记历史问题”是 1 项，不表示错误率是 1/50。`DEV2-UN02` 的 `[6]` 确认解析到 Child `3c867de1-2f08-4c34-9f39-de6d1591fa0f`（Policy for the Responsible Use of AI in Government），不能把它当作 AI Technical Standard 的支持证据。

8 道重点题完成了 39 条原子主张的 agent review：30 supported、6 not_verifiable、2 partial、1 unsupported；没有人类签核。其余 42 题完成了 513 条主张的 evidence-traceable recheck，但仍是 `provisional`，沿用保存的机器候选作为 triage，严格质量分母排除这 42 题。当前没有可诚实报告的全 50 题独立 faithfulness、答案正确率或引用语义正确率。

审计工具已改为：输入 hash 与数据库快照分开报告；输出目录非空时拒绝覆盖；数据库未实际检查时写 `null/not_checked`。没有用关键词、正则或引用编号冒充语义证明。

### C/D：安全与 Demo 交付

C 的 admin secret 服务端校验、migration 020 和权限测试沿用前一轮实现；D 的启动说明、错误提示、状态文案和默认 `reranker_top_k + original` 沿用并在本轮交接中明确。P2 `per_document_backfill_v1` 仍须显式配置，不是默认行为。

Demo 步骤见 [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md)。当前没有运行中的隔离 API/前端和可确认的隔离数据库，因此没有把旧浏览器截图冒充当前版本验收；当前浏览器全路径验收为 environment-blocked，详见 [UI 验收记录](UI_ACCEPTANCE_20260911.md)。

## 真实验证

### 本轮不产生新的模型调用

- F1–F4 代码修复、单测、审计生成均为离线操作。
- 审计使用既有 C source：`backend/data/evaluation/selection_c_public/draft_20260910T092014171489Z/`。
- 生成输入使用既有 B full generation：`backend/data/evaluation/closeout_b_full_generation/diagnostic_20260910T113645096608Z/`。
- 不重跑 50 题、不重跑失败题、不修改历史评测结果。
- 8 题 review 已暴露 UN02、UN06 的引用语义问题；由于当前环境没有可用的运行时模型凭据，本轮没有执行“同输入的一次局部生成修复”，也没有篡改已保存答案。

### 测试与检查

在临时、明确命名的 `policy-closeout-test-db` pgvector 容器中加载现有 schema、018 和 020；测试结束后已删除容器，未连接 `policy-parent-child-db`。

- 全套 Python：`413 passed, 6 skipped, 2 warnings`（含本轮新增的审计输入 hash/防覆盖测试）。
- 临时库只预置了一个合成普通用户以运行 history FK 用例；5 个旧 embedding shim、1 个 isolated parent-child opt-in 是既有 skip。
- 新状态/引用测试：14 passed；direct-stream autospec 测试：1 passed。
- `ruff check app evaluation tests`：通过。
- `ruff format --check app evaluation tests`：通过，250 个文件已格式化。
- `git diff --check`：通过；仅有工作区换行风格提示。
- `python -m compileall -q app evaluation`：通过。
- `npm run build`：通过；Vite 只有现有 bundle 大小提示。

第一次在无数据库环境运行全套测试时，测试在首个真实 DB history 用例等待连接后被停止；该次不计入通过，随后使用临时隔离库完成了上面的全套结果。

## 关键文件与哈希

以下是本轮交付时的 SHA-256，供审查者核对未提交工作区：

| 文件 | SHA-256 |
|---|---|
| `backend/app/modules/chat/contracts.py` | `C862F043E46B3AA85F865AFFB94F9787B19E39BE3600D717DDDDB79A82135810` |
| `backend/app/modules/chat/router.py` | `D30EA3C1DD95D116EEA8A73099EEE854F628DF02923BB795CD06C5555037E714` |
| `backend/app/modules/chat/schemas.py` | `915B924B5472C1C9D3AE232871D63D8509E3856E4DC43B277C26C60B81DAD982` |
| `backend/app/modules/chat/history_repository.py` | `5EDBA5B289EB9A5FA311DDEFF52A2B37879FFE39DDED2252D6CEDA02EB8D29E0` |
| `frontend/src/pages/ChatPage.jsx` | `23D1FF0466474B249538B7CADAAF818915C32A431AA047EA1922466DE001D661` |
| `frontend/src/components/CitationList.jsx` | `F3C1DB3D279E421043419B54CCC4AEECEBA19E5CFE04957354027552EEB04AC3` |
| `backend/evaluation/build_answer_audit.py` | `6CEA8696A0DF5802868D0442AF8389D93705011CA9C3000625FDBCDA069B5765` |
| `backend/evaluation/build_agent_review.py` | `D44DAECC36BC9434D72314E4CD4053EB63A2AD499E3C6D99164F514FD7AC6DB7` |
| `backend/tests/test_answer_audit.py` | `BEA389B8CE1A47AC38A6BFF9C5A3E27B49C49A47AFE2EEFAFEB22FBF865AB65D` |
| `backend/tests/test_chat_status_contract.py` | `73E3D04A56B8A995CC77999458E20312CEA00F5F5589D817FA2C1845547FC106` |
| `backend/tests/test_suggestions.py` | `456C033AFDA0F1ADA745CD865020B104C0E645C6F4586F0F24020DC7A2CF9BA5` |

工作区已有此前 P0/P1/P2、Controlled Retrieval、A–D 收尾的未提交改动；本报告不把聚合 diff 冒充为本轮全部新增。`git status` 和完整差异应由指挥 agent 审核后再决定是否提交。

## 剩余限制与放行意见

- 50 个答案仍未得到人类签核；8 题已有 agent review，42 题只有 provisional evidence recheck。
- UN02/UN06 的 Parent–Child 语义引用风险不能由编号检查解决；已有具体错配已记录，局部生成修复尚未执行，不能宣称 B 已完成语义修复。
- 当前 strict quality metrics 只覆盖 8/50 题、39 条主张；42 题 recheck 的 513 条主张不进入严格质量分母。
- `coverage_status=not_assessed` 或 `partial` 允许有依据的部分回答，但不能标记 complete；`generation_allowed=true` 也不代表完整支持。
- C 历史检索指标 `Complete@20=40/43、Macro EGC@20=95.03876%` 沿用，不是本轮新成绩；本轮没有召回率提升实验。
- migration 020 必须在目标隔离/部署库按流程应用；代码不会自动修改旧库。
- 当前没有本轮版本的真实浏览器全路径证据，不能宣称客户/公网上线。

因此本版本适合作为带人工复核边界的本地研究辅助 Demo；不适合作为无人审核的政策合规决策系统或公网正式发布版本。
