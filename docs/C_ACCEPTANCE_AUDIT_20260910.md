# C 恢复、答案审核与 UI 验收：2026-09-10

## 结论与边界

**恢复完成；审核发现阻塞，暂不更改默认策略或发布。** 原 Top-K + P2 的工程接入可以保留，但不能宣称最终答案质量已通过。

- MC01、CS06 各进行一次 generation-only 恢复，2/2 成功。与原 48 个成功答案合并有 50 个可审答案；不是首轮 50/50 成功。
- 50/50 完成模型辅助初审；23 份通过初审结构校验、27 份 `needs_adjudication`。后者主要为 judge 的断言引用不是答案精确子串，不能当作已通过审核。
- 本助手额外阅读并核对恢复答案及高风险答案/Child，确认下列缺陷。**没有人类审核者签字，也没有完成独立的全量逐断言人工签核。** 不把模型辅助初审称为人工审核，不报告未经核定的答案正确率。
- 真实浏览器验收发现并修正“已生成但显示已拒答”文案；其他实测与限制见下表。
- 数据集、embedding、reranker、Child/Parent 数据没有调整；冻结数据库只读复核得到 `corpus_unchanged=true`、`parents_unchanged=true`。
- 默认仍为 `reranker_top_k + original`，本地隔离验收实例显式使用 P2。未 commit、push、部署。

## 1. 恢复与追溯

原始运行：`backend/data/evaluation/selection_c_public/draft_20260910T092014171489Z/`。

恢复目录：`backend/data/evaluation/selection_c_recovery/recovery_20260910T095739636008Z/`。

恢复脚本只接受 `status=error, stage=generation` 且具有已批准 context/citations 的记录；校验模型 target 一致，保存原 row/report hash、question/context/citations hash、当前实际 messages hash、错误类型和次数。未重新检索，未覆盖原失败记录。每题显式调用一次，关闭 SDK 自动重试，90 秒超时。

限制：原运行没有保存历史 prompt messages hash，故能证明 saved inputs 与模型 target 一致，不能证明未记录的历史 prompt 逐字节一致。恢复产生的新答案仍须审核。

修正评测器状态：调用前写 `attempted`；生成异常写 `error`，不再保留误导性的 `not_run`；成功、错误均保存 `attempt_count`。旧运行不可回写成成功。

## 2. 从原始逐题数据重算证据链路

以下均为同一 C 运行的 43 道有 frozen evidence groups 的题；不是重新调用检索所得。

| 阶段 | Complete@5 | Complete@20 | Macro EGC@20 |
|---|---:|---:|---:|
| 混合候选 | 35/43 | 41/43 | 97.36434% |
| Cross-encoder 重排 | 36/43 | 42/43 | 98.13953% |
| selected Child | 36/43 | 40/43 | 95.03876% |
| gated Child | 36/43 | 40/43 | 95.03876% |
| packed Child | 36/43 | 40/43 | 95.03876% |

注意：最终只有最多 8 个 selected Child，最终阶段的 @20 实际覆盖该列表的全部成员；不能理解成最终塞入了 20 条。selected→packed 丢失为 0 只证明已选证据被保留，不能证明选择阶段没有丢证据。

| 题目 | 重排 @20 EGC | selected / packed EGC | 定位 |
|---|---:|---:|---|
| MC04 | 100% | 66.67% | 候选证据存在，Top-K 选择仍丢一组 |
| MC06 | 20% | 20% | 检索/重排窗口缺口，不能靠 packing 补齐 |
| CS07 | 100% | 0% | 所需组落在 Top-8 外；不是已经恢复 |

**纠正历史概括：CS07 在这一 C 运行的最终证据中没有恢复。** 不把其他策略/运行的 CS07 结论移植到 C。P2 回填不会产生未选 Child，继续增大 Parent context 不能直接解决此处 selection loss。

## 3. 答案审核材料与发现

标准沿用交接文档 §13.3 的 groundedness、relevance、completeness、citation correctness/completeness 及政策主体/条件/例外/期限/义务强度规则。这是项目验收准则，不是行业统一认证。judge 使用与生成相同的 DeepSeek 模型，有同模型偏差，不能独立放行。

- 初审原始响应：`backend/data/evaluation/selection_c_review/review_20260910T100022718962Z/`。
- 可读送审包：[INDEX.md](../backend/data/evaluation/selection_c_review/reviewer_pack_20260910/INDEX.md)。50 题每题包含原答案、reference、真实 Child ID/页码/quote、机器意见和待签核栏。
- 机器候选标签：44 `pass_complete`、4 `pass_partial`、2 `needs_revision`。**这些不是认可的通过数量**；其中包含 27 份结构校验未通过的记录，且存在下述已确认的 judge 判断问题。

| 问题 | 已核对的发现 | 处理意见 |
|---|---|---|
| CS07 | 原答案称摘录没有 alternatives assessment / media-specific provisions；实际 selected/packed gold coverage=0，主要使用泛设计原则与 Criterion 33，未回答所需替代方案与 Statement 8 条件性要求 | 标记 needs_revision/incomplete；先解决 selection，不准把 gold 塞进生成 prompt 或直接修写答案冒充运行结果 |
| UN02 | 答案引用 [6] 支撑 incident remediation 与 operationalise 12个月义务，但 Child `3c867de1-2f08-4c34-9f39-de6d1591fa0f` 只包含相关段落后半及 staff training；[3] Child `1cfeebd1-3ed8-43a4-9ced-0fd7dfbc1432` 不含声称的生效日期 | 真实 Child citation mismatch，不能因为 Parent 有内容就视为引用正确 |
| UN05 | [6] Child `572c800c-ad73-46ac-a0cb-5483516089e8` 从 Criterion 80 尾句起，主要为 81–82；不支持所引用的 Criterion 79 和 80 详细条件 | 引用精确性 major；去掉不必要扩写或只引用真正支持的已选 Child |
| UN06 | [2] Child `1f4ce752-af68-4651-9f32-841d5300a617` 是数据版本/Archives Act片段，不含答案所引 Criterion 21 内容 | 引用错配需修正；不得用“同一文档”代替 Child 级支持 |
| MC06 | 回答明确承认缺少 Dayos tiers，是诚实部分回答；但引 [8] 的 Read/Edit/Bash/MCP 权限属于特定案例，仍需检查是否被泛化为框架通则 | 不因为缺 gold 就直接判 hallucination，也不能给完整回答标签 |
| MO05 | 用户只问 test coverage 与 testing bias 是否都 required；judge 以未展开另外两个 criteria 降分 | 不接受额外未问维度作为必答项。gold 不改，审核问题相关性单列 |
| MC03 / SG01 | 可见固定“Evidence Gaps”模板生成了与前文相抵触或无助于问题的缺口表述 | 生成表达与一致性缺陷；固定输入做 prompt 对照 |
| MC01 / CS06 | 恢复答案覆盖相关流程/责任安排；CS06 区分 should 与 mandatory，但答案很长、存在大量未问缺口 | 恢复成功≠人工签核；保留原答案与待复核状态 |

UN 类仍是 `unresolved_candidate`，不能靠生成器或 judge 的一句“没有”升级为 whole-corpus confirmed absence。judge 对 UN02/UN05 建议直接回答“否”的意见不采纳：限定 available material 的证据不足更安全。

## 4. 实际 UI 验收

使用真实 headless Edge + Playwright（非 API mock）；前端 localhost:5300、后端 localhost:8000。单独数据库 `policy_ui_acceptance_20260910` 从 frozen testdb 复制，普通合成测试账号；没有在冻结库写用户/聊天。Playwright 浏览器状态和凭据只在 ignored 私有测试文件中，不可提交或发送。

截图和可见文本：`backend/data/evaluation/ui_acceptance_20260910/`。

| 用例 | 实测结论 | 证据 |
|---|---|---|
| 登录、政策库 | 通过；5 文档 ready，显示共 332 Child | login / sources |
| 选单文档→Direct→SSE答案 | HTTP 200，有训练要求与引用；但旧 UI 同时称“已拒答” | direct（修复前） |
| 修复后重开历史、引用抽屉 | 通过；改成 coverage not confirmed，不再宣称已拒答；可见 Child quote 与页码 | reopen（修复后） |
| 多轮追问 | HTTP 200；正确以政策生效为12个月起算事件，带引用 | followup |
| Agent / Document Analysis 跨库要求 | 能生成诚实部分回答，但没有执行全库搜索：该模式代码只绑定 selected-document 工具 | agent + agent-sse.txt；这是现有模式边界，不是全库检索损坏 |
| Agent / Open Discussion 全库 | HTTP 200；真实调用 selected-document 与 full-corpus，最终12条引用，展示澳洲/新加坡两份来源及 wider-library 提示 | full-corpus + full-corpus-sse.txt |
| 无选中文档输入 | Document Analysis 下禁用输入；不能将这个模式用作全库入口 | agent-no-source |
| 网络故障 | 用 Playwright abort 明确注入连接失败，无生成调用；页面显示 Failed to fetch，可再次发送，不出现伪成功答案 | network-error |

引用按钮可见且抽屉可打开；尚不能据此宣称所有 PDF 页码定位和各种屏幕布局全部通过。网络故障文案仍过于技术化。登录自动化按 label 定位失败，改用实际表单输入定位后成功；需进一步检查标签关联和可访问名称，不据此断言所有表单存在缺陷。

多工具全库样例的累计 token usage 为 49,664（跨 Agent 多次调用总数，不是单次6000-token RAG预算）。它证明链路可执行，不证明答案全面正确：输出仍有将澳洲适用范围概括成所有 agencies、为新加坡 voluntary 性质引用泛问责 Child 等待复核问题。该 UI 样例不是新增 benchmark 题，不纳入43题指标。

另外，代码复核发现 `auth/service.py:create_user` 的 admin secret 校验被注释，而公开 register router 仍传入请求 role。**这是公开部署前的安全阻塞**；本轮没有创建 admin 账号验证，也没有擅自进行权限改造。

## 5. 下一阶段实施细则（按顺序，停止扩大参数试探）

### R1：先统一应用状态语义与模式边界

目标：从 graph → router/SSE → history → frontend 保留三种独立状态：`generation_allowed`、`coverage_status`（not_assessed/partial/complete）和生成执行状态。`evidence_sources` 只能表示来源，不能推导 complete。

具体检查：`chat/router.py` 当前 Agent 汇总使用 `evidence_sufficient = bool(evidence_sources)`；实测工具返回 false 而最终 citations 事件变 true。删除这个推导所代表的完整性语义，兼容旧字段/历史记录为 unknown，不新增数据库快照重建。检查 Agent tools 中按 generation_allowed 附加 sufficient reminder 的措辞，不能继续声称已经覆盖整题。

保留“缺一个子问题仍可回答其他部分”。不得重新全题 fail-closed。前端只有明确 generation withheld 才显示拒答；unknown 不显示 complete。Document Analysis 明确 selected-only；全库模式必须明确可见，不通过放开 web search 偷渡功能。

验收：新增 router/SSE/history/frontend 合同测试，覆盖 partial但生成、complete、unknown旧记录、无context、网络错误；selected/全库/多轮一致。先离线测试，不调用50题生成。

### R2：固定 C context 的 generation/citation 修复

只改变生成指令/输出格式，不动 retrieval、pack、gold、模型。优先改成“直接答案→条件/义务强度→必要引用→仅与问题有关的缺口”，不要强制每题六段研究报告。

保留 Parent 帮助理解，明确事实引用只指向 supporting Child。现有 packer 已有此提示，因此不能声称再加一句提示必然解决。先对 UN02/05/06 等固定输入做离线可追溯对照：每条新增政策事实定位真正 Child；没有支持则不扩写。不得把 Parent ID 当 Child，或静默把 Parent 整段升级为 retrieved evidence。

自动检查先做编号/ID/精确quote/来源有效性，语义支持由可追溯逐断言复核。若采用结构化断言/证据绑定，先在独立输出 adapter 验证，不再把复杂 Planner schema 塞回主检索。不增加无限 judge/重写循环；限制一次生成及显式一次纠正实验，分别记成本。

验收：三例确认错配不再复现；MC06 诚实 partial 保留；MO05 不惩罚未问维度；UN不升级confirmed；没有新增虚构/义务反转。然后固定全部50份输入跑一次新目录 generation regression。报告实际审查分母，不拿 judge 自评代替人工认可。

### R3：只解决 selection 的确定性证据流失

从已保存 ranked pool 离线回放，输出每题 gold group 在 candidate/reranked/selected/packed 的首次位置与丢失原因。gold 仅用于离线诊断，运行时 selector 不能读取。

优先 MC04 与 CS07：它们 ranked@20 已完整。不要复用已使 MC02 退化的固定6+2；比较原 Top-K 与一个有明确覆盖/去冗余信号的受控策略。保持相同模型、候选池、K、6000预算，新增 CS07、MC04、MC02、CS08 以及重复同section案例测试。未有可靠覆盖信号时先保留原排序，不伪造semantic coverage。

验收：所有43题逐题差异，不能只看均值；selected完整题提升且旧完整题不退化，packed不再丢失selected证据。先做离线、再做全量检索回归，最后才生成。MC06另立retrieval-gap诊断，不拿它解释selection失败。

### R4：应用复现收尾与独立安全项

- 在明确的全库模式实际验证 search_full_corpus、跨文档引用和最终合并；分析模式下的selected-only是预期约束，文案需准确。
- UI错误改成人能理解的提示，保留请求/错误ID且不泄露provider密钥；修复表单标签绑定，补移动端与PDF页码点击验证。
- 独立修复公开注册提权风险并补 role/secret/非admin权限测试，再考虑服务器开放；不要将它混入检索效果实验。
- 完成审查后，用户授权才启用P2或推送。旧结果与私有浏览器状态不提交。报告、脚本、tests可跟踪；ignored评测产物需明确交接复制。

## 6. 本轮文件与验证

新增 generation recovery、saved answer review、可读审核包导出、真实 UI acceptance 脚本；新增6个恢复输入合同测试。修改 exploratory evaluator 状态、ChatPage 的分析模式提示与引用抽屉提示。未修改 retrieval/reranker/embedding/gold。

UI脚本执行会写测试账号/聊天，故新增显式环境确认 `UI_ACCEPTANCE_ISOLATED_DB_CONFIRMED=1`；只有确认本地API连接隔离副本后才能设置。不要对主数据库运行此脚本。

收尾时停止本轮临时前端与 `policy-ui-acceptance-v2-20260910` 后端容器；保留隔离数据库、容器与测试产物供复核，未删除政策文件或冻结数据。重新运行需先启动隔离实例，不能直接假设localhost端口属于测试环境。

- 相关测试：14 passed。
- 全套：390 passed、6 skipped、1 条既有 Starlette/AnyIO warning，使用隔离副本数据库。
- 首次全套误用容器 localhost 默认 DB，12 项数据库连接失败；配置到隔离副本后全套通过，未隐藏首次失败。
- 前端生产 build 通过，现有 >500kB bundle warning 保留。
- Ruff check / format check（248文件）及 git diff check 通过；Windows换行提示不属于检查失败。
- 冻结 Child/vector 与 Parent fingerprint 对原 C 运行仍一致。

人工签核、全模式UI放行和发布仍是独立状态。此报告不会将“已经执行审核”写成“审核通过”。
