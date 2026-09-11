# 给下一位 Agent：Policy RAG 工程收尾实施方案

日期：2026-09-10。用户已明确：优先完成可复现、可演示、有边界的工程应用，不再以提高 Complete@5/20 或追求满分作为本轮任务。

## 0. 任务指令与完成定义

你是实现 Agent。请基于现有工作区做增量收尾，不重写项目。依次完成：

1. 统一生成/覆盖状态，修复 API、SSE、历史和 UI 的误报。
2. 修复已确认的生成冗长与 Child 引用错配，允许诚实的部分回答。
3. 收紧公开注册的管理员权限入口，补必要授权测试。
4. 完成真实 UI、启动文档、回退说明与交付报告。

**完成目标是“可供面试/客户 Demo、有人工复核边界的研究辅助工具”，不是无人审核的政策合规决策系统。** Complete@5=36/43、最终 Complete@20=40/43 不必提高；已知引用错配、权限越界和状态说谎则不能包装为已解决。

本方案优先于 `NEXT_AGENT_HANDOFF.md` §14.3 的旧执行顺序：**旧 R3 selection 优化转入 backlog，本轮不做**。不创建新一代 Controlled Retrieval，不重启 Planner/schema 优化实验。

### 范围冻结

禁止修改：benchmark题干、reference/gold/evidence groups、embedding/reranker模型、向量/Child/Parent快照、ingestion/chunking、BM25/RRF/Top-K/selection算法、阈值和token预算、补查轮数、Live Web Search配置。

- 默认 `reranker_top_k + original` 保留；P2 `per_document_backfill_v1` 仅显式验收，不静默设为默认。
- 允许修改：状态合同、生成与引用指令/轻量校验、聊天状态存储、注册授权、相关UI文案、测试和文档。
- 数据库只允许**聊天状态增量schema迁移**在隔离副本验证；不改冻结库、不重入库、不触碰文档/向量表。
- 不升级依赖、不换数据库、不新增常驻LLM Judge、不引入自由语义Planner、不做大规模模块移动。
- 不 commit/push/部署；先交付diff和结果。用户另行授权后再执行版本发布操作。

## 1. 接手前必须核对

工作区：`D:\AIWorkspace\Projects\policy-research-agent`；仓库 `shldo/Policy_analyize_agent`。

制定本方案时为 `develop`，HEAD `fc9aa91`，**大量收尾/P1/P2变更尚未提交**。只拉 GitHub develop 不等于拥有本工作区。先看 git status/diff，保留用户和其他Agent未提交改动，不reset/clean/覆盖。

先读：

- `AGENTS.md` 与其要求的共享规则；不要改AgentHub。
- `docs/C_ACCEPTANCE_AUDIT_20260910.md`。
- `docs/NEXT_AGENT_HANDOFF.md` §13–14，注意历史结论与本方案优先级。
- 下表对应代码和已有tests，不凭文件名猜调用链。

### 已验证基线（不是本轮须追求的新指标）

| 项目 | 当前记录 |
|---|---|
| frozen corpus | 5 PDF，332 Child |
| 题目 | 50总题，43有可评分evidence groups |
| C最终证据 | Complete@5=36/43；Complete@20=40/43；Macro EGC@20=95.03876% |
| C未完整题 | MC04=2/3；MC06=1/5；CS07=0/3 |
| 上游定位 | MC04/CS07在reranked@20已完整但selection丢失；MC06在该窗口仅20% |
| 生成 | 原始48成功、2连接失败；后续复用context恢复2/2，共50个可审答案 |
| 审核 | 50题机器辅助初审；23结构合法、27待裁决；没有全量人类签核 |
| 工程 | 上轮390 passed、6 skipped、1既有warning；前端build通过 |

不要写“CS07已恢复”，不要写“50/50首轮成功”，不要把初审44个pass_complete候选当成44道人工审核通过。

### 产物定位

以下目录相对 `backend/`：

- `data/evaluation/selection_c_public/draft_20260910T092014171489Z/`
- `data/evaluation/selection_c_recovery/recovery_20260910T095739636008Z/`
- `data/evaluation/selection_c_review/review_20260910T100022718962Z/`
- `data/evaluation/selection_c_review/reviewer_pack_20260910/INDEX.md`
- `data/evaluation/ui_acceptance_20260910/`

这些产物被gitignore，另一工作区可能没有。缺失时先报告需要复制的明确目录；可继续不依赖它们的状态/授权单测，但不得重造“同一基线”或擅自全量重跑。不要复制或提交 `private-test-user.json`、`private-browser-state.json` 或环境密钥。

## 2. 工作包 A：状态合同（第一优先）

### A1. 已确认原因

- `chat/router.py` Agent路径存在 `evidence_sufficient = bool(evidence_sources)`：把“有来源”误当“充分”。
- `chat/schemas.py:ChatResponse` 默认 `evidence_sufficient=True`，可能让缺字段记录自动变成通过。
- `parent_pipeline.py` 已有 `generation_allowed / coverage_sufficient / coverage_status`，Classic允许partial时通常是 `not_assessed`，无需新增Judge。
- Agent工具子查询可允许生成，但它的完成度不等于原始复合问题完成度；最后一次工具也不一定代表整题。
- `pack_agent_messages` 最终可能丢Child；最终UI/citations不能仍宣称被丢Child可用于作答。
- 历史表只有legacy sufficiency和执行status，新状态没有贯穿保存与恢复。

### A2. 最小语义合同

沿用现有枚举，不另造同义状态机：

| 字段 | 含义与规则 |
|---|---|
| `generation_allowed` | 此模式允许进入生成；不是答案完整或正确。文档模式有可用context可为true；Open Discussion既有通用知识边界需保留并明确标识 |
| `coverage_status` | `not_assessed / partial / complete / no_context`。旧消息缺值→not_assessed；不能将未知误写partial，更不能写complete |
| `coverage_sufficient` | 仅当原问题有有效的完整覆盖验证，且最终pack仍保留所需证据才为true；可从规范化coverage_status派生 |
| `answer_status` | `pending / streaming / generated / withheld / error / unknown`，从真实执行分支产生，不从答案文字、引用数或coverage推导 |
| `evidence_sources` | 仅表示 internal/full_corpus/web 来源；不得决定coverage完整性 |
| `evidence_sufficient` | 保留兼容字段，但不得默认true或继续负责是否允许部分回答；新响应最多映射已确认的coverage_sufficient |

新字段允许nullable兼容历史。API字段名若因现有约定需要调整，只能一处定义统一适配，写映射表，不要每条路各自起名。

**关键约束：** 不为了显示complete而新加语义评估。Classic默认not_assessed是可接受状态；“未确认完整”不代表系统不能给有依据的答案。

### A3. 修改位置与策略

1. `chat/schemas.py`：新增兼容字段、修正默认值；确认HTTP/SSE/history都输出同一合同。
2. `chat/rag/graph/state.py`、`graph/nodes.py`：从实际生成/拒答/失败分支给出状态；不改retrieve/selection。
3. `chat/rag/agent/state.py`、`agent/tools.py`、`agent/context.py`、`agent/graph.py`：保留最终pack的Child ID/coverage结果，供最终输出使用。若现有函数只返回messages，用小型内部结果结构或兼容wrapper传元数据，不重复打包、不从system prompt反向解析。
4. `chat/router.py`：逐一检查同步、Direct stream、Agent stream、resume、error以及历史写入分支。去掉来源集合→充分性推断；中途stream失败仍是error，不能因已有部分token当generated。来源与引用以最终保留结果为准，不因coverage未知把来源清空。
5. Agent reminders / auto-finalize文案：`generation_allowed=true`不能声称“检索闸门已确认覆盖整题”；保持现有补查预算，不新增轮次。
6. `chat/history_repository.py`：新状态贯穿add/finalize/list；保留现有执行`status`语义，不把`status=complete`解释为证据complete。
7. `frontend/src/pages/ChatPage.jsx`：同时更新SSE映射、历史映射、提示、引用抽屉、错误状态。不只修当前回答，刷新页面也要一致。

### A4. 聊天表迁移

检查现有 `backend/database/migrations/` 编号后，新增下一个文件；当前最高019，不假定接手时仍未占用020。

建议对 `chat_messages` 增加nullable `generation_allowed boolean`、`coverage_status text`、`answer_status text`；无需持久化可派生的coverage_sufficient。若已出现同等专用元数据容器可复用；**不要把字段塞进citations_json/token_usage/reasoning_steps**。

迁移需幂等，保持旧消息可读，不回填为complete，不删除字段或重写旧答案。现有 `status=complete` 仅能说明旧执行结束，无法确定是否曾拒答，因此旧answer_status保守为unknown。同步真实的新库初始化入口，不依赖代码中可能已失效的 `supabase/local_schema.sql` 路径。

在新隔离副本测试迁移与回退：回退旧应用时保留新增nullable列即可，不需要破坏性drop。运行时检查迁移前置条件，缺列给明确提示，不悄悄吞DB写入异常。禁止对 frozen testdb 执行迁移。

### A5. 必须新增的回归用例

- 有context、coverage=not_assessed、成功生成 → 显示可用答案/覆盖未确认，不显示拒答或完整支持。
- coverage=partial、成功生成 → 仍允许作答，不能整题拒绝。
- 原问题有效complete且最终证据保留 → complete；只有子查询complete → 不可直接complete。
- 最终pack丢所需Child → 不能complete，丢失Child不能出现在可引用结果中；不重新编号已有Agent引用造成错配。
- no_context、实际withheld → 明确拒答；Open Discussion的无文档回答不得伪装document-grounded。
- source list非空但coverage未知 → 不充分；legacy字段缺失/null/true都不能使新coverage自动complete。
- 流中断、provider错误、用户取消 → 明确状态，历史刷新不变成generated。
- 相同样例对照HTTP、SSE final metadata、DB读回、UI状态；覆盖Direct/Agent/full-corpus/resume。

## 3. 工作包 B：固定输入的生成与引用修复

### B1. 本轮要解决什么

已知 UN02、UN05、UN06：答案中的事实来自Parent，却给了不支持该事实的Child引用。重点不是编号能否解析，而是引用是否真的支持相邻断言。

先读 `C_ACCEPTANCE_AUDIT_20260910.md` §3 的确切Child ID及原答案。不更改这些错误产物，不把修好的人工答案当新运行。

### B2. 第一版实现（保持轻量）

- 修改 `chat/rag/prompts.py` 的研究者默认结构：问题直接答案→必要条件/期限/义务强度→对应引用→仅与所问内容有关的缺口。用户明确要求完整报告时仍可组织报告，保留policymaker/student用途，不统一抹掉角色。
- 去掉强制六段式和“没问也列一堆不知道”的倾向。没有缺口就不强行输出Evidence Gaps；不写前文已回答、后文又称证据不存在的矛盾。
- 在 Classic `generation.py` 和 Agent `agent/prompts.py` 中共用相同的引用语义规则，避免只修一条路径。
- Parent用于理解上下文；事实若只能在Parent找到，不能把它挂到同Parent的任意Child。第一版不要自动升级全部Parent正文为新引用，不做全库citation二次检索。
- 生成只陈述最终已选Child能支持的政策事实；未支持的细节不扩写。合成推论可明确标为synthesis，但不能伪装成原文义务。
- must/should/may、主体、例外、时间起点不能省略或强化。不能把“公共政策适用对象中的一类”泛化为所有政府机构。
- 对缺失子问题准确写 `The available material does not establish ...`，不写“全文没有”。不为了回答是非问句而强行给未经全文确认的No。

`context_packing.py` 已存在“仅引用supporting Child”的提示，不能只重复添加一句就宣布修复；需要实际固定输入对照。

### B3. 轻量引用完整性检查

复用现有citation_checks/引用解析逻辑，先保障：编号存在、对应final packed Child、引用身份不变、quote来自真实Child、Agent编号允许不连续但不能重绑定。语法/身份检查与语义审核分别记录。

不要用关键词交集/正则冒充语义蕴含检查，不根据quote包含几个词就标supported。不要默默给模型补引用；若编号非法，显式记录citation validation warning，不能显示“已验证”。不得因一条引文有问题又恢复整题强制拒答。

无需为本轮设计复杂JSON claim Planner、在线评审多Agent、自动多次重写。若一次prompt修复仍不能消除已知语义错配，最多进行一次有明确原因的局部修正，再如实报告剩余问题，转为需要核对原文的检索辅助Demo；不无限试错。

### B4. 分阶段验证和调用预算

1. 无API单测：prompt角色兼容、直接/Agent共用规则、非法/缺失/跨Parent误绑定ID、最终pack丢引用、历史映射。
2. 诊断集固定8题：UN02、UN05、UN06、MC06、MO05、CS07、MC01、CS06。题目不改；只复用原C的question/context/citations，恢复题沿用其对应原输入。生成器不得接触gold、review或候选修正版答案。
3. 记录context/citation/model/prompt hash、次数、耗时、token、原错误，保存新目录。每题一调用，SDK重试与外层重试不能叠加；连接失败单独登记，最多显式恢复一次，不覆盖首次结果。
4. 诊断集通过已知错误检查后，跑一次50题generation-only；8题如输入/prompt完全相同，可复用结果并明确标注来源，再跑剩余42题。若修改过prompt则不能混为同一版本。
5. 不做第二轮无差别50题重跑或50题同模型Judge自动评分。优先逐断言审查已确认错配题和发生明显变化题，其余报告实际审核覆盖；需要全量独立签核时明确pending，不能造人类审核。

预期：retrieval分数不变，答案更短、更少不相关事实、引用错误减少。**CS07仍可能partial，MC06仍可能只覆盖20%——本轮允许，不要求把它们答全。** 不从gold偷补信息。

## 4. 工作包 C：注册权限与最低部署安全

明确问题：`auth/service.py:create_user` 中admin secret校验被注释，`auth/router.py`公开register仍把请求role/secret传入；调用者可申请admin而没有相应校验。

最小修复：恢复现有管理员注册校验，服务端执行，配置secret缺失/空、请求secret缺失/空或错误均拒绝；正确secret使用 `hmac.compare_digest` 比较并且不记录。普通注册默认user保持不变。不要只隐藏前端admin选项，不改已有用户role，不自动降权/删除账号。

保留现有合法管理员初始化方式，并文档说明；不要引入一套新RBAC/OAuth。检查项目已有settings是否有危险开发默认值，若存在公开部署风险写清运行前置条件；不要生成或打印用户密钥。

测试：普通注册、合法admin、未配置/空/错误secret拒绝、拒绝时repository不创建用户、普通用户不能调用admin保护的设置/导入接口、未登录与越权返回合适错误。拒绝响应不回显secret和数据库异常。

在mock/隔离测试账号上验证，不在主库创建admin做演示，不改现有账户。公开部署保持未授权状态；修复安全漏洞不是授权上线。

## 5. 工作包 D：UI与可复现交付

不改搜索策略。Document Analysis维持selected-only；Open Discussion现有full-corpus能力保留，不顺带开启web。让用户能看懂模式范围，不因测试员在错误模式跨库就把系统判失败。

把 `Failed to fetch` 等提示改为简明英文用户说明，例如 `Connection interrupted. Please retry.`；不输出provider原始报错或密钥。不要自动循环重发，避免重复聊天和API开销。

验收用真实UI和真实隔离API，覆盖：

| 场景 | 必须看到 |
|---|---|
| 登录/政策库 | 能登录、5文档可用，普通账号权限正确 |
| Direct单文档 | 回答、条件、Child引用，unknown不被标完整/拒答 |
| 多文档/Agent full-corpus | 在正确模式调用对应工具，来源范围与最终引用一致 |
| 多轮和刷新 | 当前问题的状态与证据独立，历史状态无误升级 |
| 已知partial | 有依据的部分仍回答，缺口清楚，不显示complete |
| 引用抽屉/PDF | 显示Child原文/页码；实际点击PDF检查页码，不只看到按钮就通过 |
| 网络异常/中断 | 显式错误、可人工重试、无伪成功、历史不变成完成 |
| 窄屏/表单 | 核心控件可访问，标签关联可读；不借机重新设计UI |
| 默认/实验 | 默认original一条smoke；P2显式配置一条smoke，不能用P2通过代替默认可用 |

UI回归建议6条左右真实问答覆盖主要路径，网络注入无需API。不要做全UI50题重复生成。不以单次UI成功推算SLA或大规模质量。

优先复用 `evaluation/ui_acceptance.cjs`，识别其中本机Playwright/端口假设；设置 `UI_ACCEPTANCE_ISOLATED_DB_CONFIRMED=1` 前必须核实连接隔离库。不得把浏览器凭据提交给另一个工作区。临时服务由本轮创建的才可停止，保留数据方便复核。

更新启动说明：依赖、环境变量名称（非值）、Docker/DB迁移顺序、API与前端入口、模型资源位置、示例问题、模式边界、故障排查、如何停止/重启、如何切回original。新机器缺模型/API/ignored数据时报告明确前置条件，不能假装可以零配置复现。

## 6. 验证顺序、停止条件与交付

每个工作包先复现已知缺陷→新增小测试→最小实现→相关测试。完成A/B/C再跑全套、Ruff check/format、diff check和前端build；数据库测试只能在隔离库。390是历史基线，报告本轮真实通过/失败/skip及首次失败原因，不为了凑数跳过失败。

没有调用检索就不要声称重新测得36/43；读取不可变产物只能称“沿用/重算原始基线”。本轮预期证据ID和retrieval参数不变，使用hash/差异检查证明，不用又跑多套检索实验。

### Demo-ready的验收条件

- 不再有“生成成功却写withheld”“有来源自动complete”“旧历史自动complete”。
- 公开注册不能无凭证提权；未授权操作测试通过。
- 三例已确认Child错配实际复核不再出现；至少没有新增已知虚构/义务反转/越界引用。自动编号合法不能代替此项。
- 诚实部分回答保留；不要求CS07/MC06补齐，不要求指标提高。
- 主要UI和启动流程可复现，剩余错误/未测项显式列出。
- 允许残留：检索召回缺口、not_assessed、人工复核边界、已记录的非阻塞性能/样式问题。

若仍有引用语义错误：标记 `needs_fix` 或降低为“检索与原文核对Demo”，不要反复重跑至碰巧好看。对客户正式使用/公网部署不能宣称已验收，后续授权与人工政策复核独立。

### 最终必须交付

1. `docs/ENGINEERING_CLOSEOUT_RESULTS.md`：工作包A–D完成矩阵、修改文件/职责、实际调用链、新字段和migration、兼容/回退、测试与UI证据、模型调用/成本、明确剩余限制。
2. `docs/DEMO_RUNBOOK.md`：从现有项目启动Demo的具体步骤、配置检查、已知限制与场景脚本；不能包含secret。
3. 新运行目录与可读审核记录：问题、原答案/新答案、真实Child依据、支持/不支持原因、审核方式及未签核状态；原目录不覆盖。
4. 更新 `NEXT_AGENT_HANDOFF.md` 和主指导文档，标明selection/新PDF扩容/Agentic改造已暂缓。
5. 最终回复明确：Demo-ready / needs-fix / environment-blocked，且分别报告状态、引用、安全、UI。不要只写“全部tests通过”。

在这些范围内自主实施；不要每完成一个文件就让用户确认。遇到需要修改冻结材料、扩大模型调用、生产迁移或发布的新权限时停止并说明，不自行扩张任务。
