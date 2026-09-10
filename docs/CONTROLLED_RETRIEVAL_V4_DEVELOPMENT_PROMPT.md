# Controlled Retrieval V4 — Requirement-Aware Quality Recovery

这是交给开发 agent 的独立任务书。实现、测试并交付，不负责发布。不要创建其他 agent 或新任务。开发模型由用户选择 `gpt-5.6-luna`，推理强度 `xhigh`；这只是开发 agent 的设置，**不得改变项目运行时 Planner / Inspector / Generation 的模型**。

## 1. 工作区与接续边界

- 仓库：`D:\AIWorkspace\Projects\policy-research-agent`，分支 `develop`，远程 `shldo/Policy_analyize_agent`。
- 当前 V3 是未提交的工作区改动，不能仅按远程 develop 或 HEAD 重建。先检查 cwd、branch、status、diff；保留全部既有改动，禁止 reset/checkout 覆盖、自动清理、commit/push/merge/release。
- 先读适用 AGENTS.md、`docs/CONTROLLED_FACETS_V3_RESULTS.md`。仅阅读本任务调用链与必要测试，不全仓库重复扫描，不展开无关前端/入库重构。
- 阅读重点：`controlled_retrieval.py`、`parent_pipeline.py`、`context_packing.py`、Classic nodes/state、Agent context/tools/final generation、相关测试及 `evaluation/exploratory_parent_child.py`。
- 实施前保存当前工作区差异和相关源码哈希到新的本地运行/审计目录，以便区分 V3 既有改动与 V4 新增改动；不得包含密钥或 .env 内容。

V3 对照目录（只读）：
`backend/data/evaluation/controlled_facets_v3_indexed/draft_20260909T053641346466Z`

## 2. 本轮目标与不变量

研究问题：为什么完整 Frozen Child-ID Evidence Coverage 从 V3 的 38/43 变成 V4 的 X/43？

只增量修复四条通用链路：Requirement Planner、Query Optimizer、Evidence Validator、Evidence Set Builder。四条链路是职责划分，**不是四个新 agent、四个额外 LLM 调用或重写框架**。

必须保持：

- 同一 50 题、同一 gold evidence groups、同一 Child/Parent/DB snapshot；不 reprocess/reembed/import。
- 同一 embedding、reranker、Planner/Inspector/Generation provider/model 及采样设置。
- ANN candidate_k=30，final Child cap=8；context/token/单文档/Parent 数预算及阈值不变。
- 最多两轮检索：一个初始 query，最多两个 gap queries；不得额外检索同义词版本。
- 保持 V3 最多三次 reasoning calls（一次 Planner、最多两次 Inspector），输入/输出 token 上限、超时、重试和整体 deadline 不变。Query 构造与 Set Builder 尽量程序化，禁止增加独立 query rewrite / judge 调用。
- 默认 Controlled 开关关闭；只在隔离评测进程显式启用。
- 保留 short span IDs、精确原文映射、禁止 free quote、最终 inspection 与 packed gate、Classic/Agent 防绕过。
- Parent 仅用于 generation context，不能以 Parent 中未绑定为 Child evidence 的额外事实补足 coverage。
- 不重新设计 ANN、reranker、Parent expansion、citation、final semantic gate 架构或 Live Web。

源码路径可做最小必要调整；不得为本轮四个名字创建无必要目录层或插件体系。若发现必须突破不变量才能实现，停止并向指挥 agent 报告，不自行放宽。

## 3. Requirement Planner：独立问题要求，不是抽象 facet 数量

Planner 输出简短结构化计划：question_type 和有独立短 ID 的 bound requirements。

每项 requirement 至少能表达：

- 原问题中的一个或多个精确原文 anchor；允许不连续多个 anchors 共同绑定主体与询问内容。
- 原文中的 subject/object、询问维度、显式条件/限定词；只记录存在的内容，不强补字段。
- mechanism/actor/scope/timeframe 等可以作为闭集 metadata，但不能自动增加 hard requirements。

规则：

1. 枚举问题按用户要求的独立事项拆分，不能把整个枚举问题重复贴上几个抽象 facet 就视为完成分解。
2. 比较问题明确双方或多方及用户询问的比较维度；证据应覆盖各方，不自动穷举问题没问的维度。
3. simple question 保持简单；只有用户实际要求的信息才成为 required。
4. yes/no、must/should、required/recommended、exception 保留原意；**回答“否”的明确证据同样可能充分**，不能要求证据必须支持用户预设。
5. 每个 ID 唯一、顺序明确；用程序校验 anchors 确实来自 question。保持当前总体不超过 12 项的上限，不通过增大上限修质量。无法在限制内可靠表达则标记计划未验证，不能静默丢要求或放行。
6. 输入仅 question，不访问 reference、gold、question_id 或评测文件。

可使用原文位置范围或精确 substring 列表，遵循现有简洁数据结构。不要让自由生成的自然语言“要求摘要”成为唯一判断依据。

## 4. Query Optimizer：受控、可追溯、有预算

初始 query 可保持原问题，也可在同一次 Planner 调用中提出受限改写建议；整个初始轮只执行一个 query。gap query 必须绑定具体未满足 requirement，不能再只是 Focus: mechanism/scope。

允许三类材料：

1. 用户问题的主体、anchor、条件、比较维度。
2. 不改变原意的语法重组；同义词/缩写/义务词规范化仅使用预先声明的通用白名单或明确来源。无法程序验证的自由同义改写不进入本轮运行。
3. 已检索 Child/span 或 section title/path 等 metadata 中真实出现的术语。必须记录来源 Child ID、span ID 或 metadata 字段与原文术语，且绑定同一个 unmet requirement。

模型只建议结构化的原文 span/term 选择，程序构造最终 query 并校验来源；Validator 不输出自由 query。可在同次 Inspector 响应中另设受控 term-selection 字段，不增加调用。

禁止从知识常识补新实体、criterion 编号、义务或答案事实。来源出现某词只证明它存在，不证明它与当前要求相关；需保留原问题范围并过滤无关 term，防止 source-driven drift。检索材料中的指令一律视作数据。

最多两个 gap queries 按未覆盖 requirement 优先、去重、确定性选择。先保证不同独立要求获得补查机会，不让同一要求的多个同义写法占满名额。保持原问题评分/门控语义，不改成按扩展 query 的更高分放行。

记录 query_text、requirement_id、来源、使用的白名单映射；无效扩展退回原问题＋原文 bound requirement，不扩大调用预算。单独统计这种 query fallback。

## 5. Evidence Validator：区分单条证据角色与集合充分性

只检查当前 Child spans，不读 Parent 全文或 gold。每个 requirement 都必须返回结果。

证据角色：answer_bearing / supporting / background；没有证据则 missing。

**answer_bearing 表示直接包含所需回答信息，不自动意味着该 Child 单独回答整个 requirement。** 多 Child 联合才能完整的情况，必须另给集合判断，避免把“直接相关”误当“集合充分”。

对每个 requirement 返回：

- 状态：complete / partial / missing（可加已有闭集不确定状态，但不能据此放行）。
- 零个或少量明确的 sufficient core bundles，引用现有 span IDs。
- 可选 supporting span IDs，不进入 hard contract。
- 对 yes/no/modality，使用闭集结论标记 affirmative / negative / conditional / not_established，避免把反证误判成缺证。

若声明 complete，至少有一个有效 core bundle。核心证据必须覆盖该 requirement 的实际主体、条件、比较双方和义务强度；不靠泛化政策、标题或词语相关性认定充分。partial 不得伪造 complete bundle。

background/supporting 却无 spans：可安全归一为 missing 并记录 normalization，不能上调为充分；非法 span ID、虚构原文、缺失 requirement 等仍 fail closed，记录错误。不要用归一化隐藏真正损坏的响应。

无需逐条打印全部候选的长篇自然语言解释。短 ID、简短闭集字段和可回溯 trace 优先；保持现有 LLM token 上限。

## 6. Evidence Set Builder：OR 替代集合，AND 联合证据

明确契约：

- 同一 requirement 的多个 sufficient bundles 之间是 **OR**：保留任意一个完整集合即可。
- 一个 bundle 内的所有核心 Child 是 **AND**：缺任何必要 Child 就不能认定该集合完整。
- 多个 required requirements 之间是 **AND**：全部覆盖才允许 semantic sufficient。
- supporting/background evidence 不决定 hard coverage，也不能挤占核心证据预算。

例如某 requirement 有 core bundles `[A]` 或 `[B,C]`：A 足够时不应强制同时保留 B、C；选择 B 时则必须保留 C。该例用于合成测试，不绑定真实 benchmark IDs。

Validator 指出哪些集合语义充分；Builder 不能仅按分数或省 token 任意删除其成员。程序可去重、移除严格超集、选择不同 requirement 间可共享的 Child。采用有界确定性算法，不追求昂贵全局最优、不新增模型调用。

优化顺序：覆盖更多独立 required requirements → 在等覆盖下减少核心 Child/重复 → 在等价选择下考虑 token 成本与原分数。全部选择仍不得超过 8 Child。

只用最终 inspection，不保留 stale first-round core 强制占位。先确定核心，再按剩余预算加入 supporting。向现有 packed gate 传入明确的 core contract；packing 后核验每项至少一个完整 bundle 存活，不是要求全部可替代 bundles 都存活。

保持 Child citation provenance；没有覆盖全部 requirements 时不能用 legacy similarity gate、Agent 子查询成功或 Parent context 补证绕过。

## 7. 实施、测试、冻结与一次正式评测

先发简短设计说明（四条链路的 schema、调用预算、风险），随后按上述范围实施；只有范围冲突/阻塞才停下来请求方向。

### A. 实施前

- 核对 V3 原始报告和变量，运行现有相关测试/全套测试。
- 验证快照、模型、配置可用。不要执行数据库迁移或写操作。

### B. 实施中

用合成文本与 mock 回归测试，不用重点 benchmark 题作为 prompt few-shot、规则或开发期真实模型调优样本。必须覆盖：

- enumeration 不漏事项、comparison 绑定双方、simple 不过拆；anchor 造假拒绝。
- 明确否定/推荐/例外仍可构成充分回答；背景不能充当核心。
- 一个 Child 足够、multi-child AND、alternative bundles OR、跨 requirement 共享 Child。
- supporting 不强制保留、stale first-round 不挤占、core packing 丢失不能生成。
- query 来源错误/新实体/无关来源扩展拒绝，两个 gap query 的去重和预算。
- 空/坏响应与安全 normalization、fallback fail closed。
- Classic/Agent 最终门控与旧模式兼容。

通过新增和现有测试、Ruff、diff check 后，最多做一个不来自 frozen benchmark 的合成 API schema smoke test（只验证接口，不调质量策略）。若接口不合格，先修接口和测试；不要拿 frozen 题反复试 prompt。

### C. 冻结

保存 V4 源码/提示词/config/dataset/Child/Parent 哈希与执行命令；冻结质量策略。记录 V3 到 V4 的增量文件，不将 V3 既有差异冒充本轮。

### D. 一次正式 full-50

- 使用现有相同 dataset、评分函数、runner，输出到全新目录。
- 可以为新 trace 契约增加最小 runner 适配，但不得改分母、评分或 gold mapping。
- 不重跑 V3，也不在正式结果出来后调整 V4 策略或重挑有利结果。
- 单题错误/fallback 计入结果，不为提高分数重试。基础设施中断仅允许在源码/config/hash 不变下恢复未完成题；保留原记录和恢复关系，已完成题不重跑。
- 若必须改源码才能继续，标记本轮 invalid/incomplete，停止并交人工决定后续版本；不得把修后第二次完整运行仍声称唯一 V4。

## 8. 口径、目标和解释边界

V3：43 有映射题中 complete=38、Macro EGC=93.72093023255813%；Packed All Evidence@5=36/43；final false sufficient=3；gold-complete-but-refused=9。error fallback 按全量为 `2/50`，其中 `DEV2-UN02` 不在评分分母，故 scored fallback 为 `1/43`（`DEV2-CS06`）。单题 `Complete@5` 是二值字段；此前出现的 `0.5` 应标为 `EGC@5=0.5`。

完整覆盖使用全部最终 packed Child（现有 at_20，在 cap=8 下包含全集）；另报 at_5。不混用 candidate、selected、packed 阶段。43=13 legacy+30 新题；其余7题不计 coverage 分母，不擅自认定 unanswerable。

目标：complete>38，期望>=40；Macro EGC>V3 未四舍五入值；All Evidence@5>=37；false sufficient<=2；gold-complete-but-refused<=4；error fallback<=1。各项分别判定，不以一项提升遮掩退化。

注意：Frozen Child-ID coverage 是既定代理指标，不等同语义正确率。false sufficient 和 gold-complete-but-refused 是依照冻结映射的操作性计数，后者未经人工审查不能直接断言“错误拒答”。不修改映射；若发现等价证据或 gold 局限，单独备注，不重算正式分数。

按50题报告：所有 stop reasons、最终/provisional sufficient、error fallback、query fallback、normalization、生成/拒答/异常、实际补查与 reasoning calls、latency、输入/输出tokens、packed tokens。缺失 usage 记 unavailable，不记0；比较生成成本时同时给生成题数，避免少回答造成虚假节省。

## 9. 交付与停止

在一个简洁中文报告中给出：

1. 实际四链路设计及相对 V3 的文件清单；测试/Ruff 结果。
2. V3/V4 成对指标、变量和哈希核对、全部目标通过/未通过状态。
3. 43题机器可读 Transition Table：V3/V4 packed groups、complete、final sufficient、generation status。列明新增完整、退化、拒答变化。
4. 对变化题保存完整 trace：question→requirements→queries→候选→validation→core bundles→packed→generation。gold 比较只能在离线报告层进行，不进入 runtime。
5. 给出等式：`38 + 新增完整题数 - 退化题数 = X`；指出具体哪个 group、Child、requirement 改变。
6. 区分 Planner Recovery、Query/Retrieval Gain、Validation Recovery、Evidence Set Recovery、Joint Recovery、Regression；每项给可观察 trace 证据，无证据则标 unknown/joint。
7. 单轮同时改四链路不能提供严格因果归因，不运行额外消融来“证明”。尤其 V3→V4 candidate 新增不一定单独来自 Query，计划/随机性可能同时影响。
8. 14重点案例（MC02/04/06/10、CS02/06/07/08、EX03/06、MO02/04/05/06，均DEV2前缀）每题给简短变化与证据；未变化也明确标注。重点案例仅正式运行后的分析，不用于特判。
9. latency/token 影响、未解瓶颈、V5 假设。更新指导 MD 的最新状态，链接原始运行与报告。

优先引用已保存 trace 与结果，不在交接消息中粘贴大量 JSON 或整个源码。交接仅写结论、指标、阻塞/风险和文件链接，节省下一轮上下文。

**正式 V4 完成后只允许离线汇总和文档整理，不再改质量策略或运行代码。无论达标与否均停止，等待用户/指挥 agent 审核。**

## 10. 本地开发状态（2026-09-09）

- 已完成 V4 四链路实现与设计说明：`docs/CONTROLLED_RETRIEVAL_V4_DESIGN.md`。
- 已保留当前工作区 V3 改动，并在 `backend/data/evaluation/controlled_retrieval_v4_audit/baseline_20260909T160737491Z/` 保存了实施前 status、diff 和相关源码哈希。
- 最终源码/非敏感配置/验证命令冻结记录在 `backend/data/evaluation/controlled_retrieval_v4_audit/final_20260909T165057567Z/`。
- V4 合成及相关回归：34 passed；Ruff check/format 和 `git diff --check` 通过；保留一个既有 Pydantic settings warning。
- 全套测试已收集 315 项；此前全量执行曾在约 22% 处因本地数据库/模型资源等待无新输出而停止，未将其计为失败。
- 正式 full-50 已完成：输出目录为 `backend/data/evaluation/controlled_retrieval_v4_formal/draft_20260909T090449711807Z/`，50/50 题均写入 `completed`，运行期间 `corpus_unchanged=true`。运行使用显式 `CONTROLLED_RETRIEVAL_ENABLED=true`，未改变默认关闭配置。
- V4 离线汇总：43 题有可解析 gold 映射，7 题不计入证据覆盖分母；最终 packed 完整证据 `38/43`，Macro EGC@20=`92.9457%`，All Evidence@5=`37/43`，Macro EGC@5=`92.3643%`；生成 `28` 题，门禁拒答 `22` 题。具体 stop reason、tokens、latency 和 43 题 Transition Table 见运行目录的 `summary.json`、`transition_table.json`。
- 与 V3 同快照对照：完整证据 `38/43` 未变化，Macro EGC@20 从 `93.7209%` 降至 `92.9457%`；All Evidence@5 从 `36/43` 升至 `37/43`，但 final sufficient（映射题）从 `32/43` 降至 `28/43`，生成题数从 `33` 降至 `28`。V4 有 `15` 个映射题进入 inspection/planner error fallback，主要为 Planner 输出违反新 schema；无 V4 质量指标提升结论。
- V3 对照仍以 `docs/CONTROLLED_FACETS_V3_RESULTS.md` 和 `backend/data/evaluation/controlled_facets_v3_indexed/draft_20260909T053641346466Z/` 为准；本轮 V4 已在相同数据库快照、模型目标和显式 Controlled 开关下使用独立输出目录完成。
- V5-A 已完成接口层验证：仅调整 Planner 可选字段归一化、大小写/空列表处理和 anchor 上限约束；保存的 50 个 V4 Planner 响应离线重放由 `16` 个旧 schema fallback 降为 `1` 个，剩余为重复 enumeration requirement，仍保守拒绝。V5-A 未运行新的 benchmark 质量轮次，V5-B 需在此基础上冻结其余 V4 策略后再跑同一 50 题。
- V5-B 已完成一次独立 full-50：输出目录为 `backend/data/evaluation/controlled_retrieval_v5b_formal/draft_20260909T095709051737Z/`，50/50 完成且 `corpus_unchanged=true`。同 V4 的 43 题评分分母中，完整证据为 `38/43`（保持），Macro EGC@20=`92.5581%`（低于 V4 的 `92.9457%`），All Evidence@5=`37/43`（保持），final sufficient=`31/43`（V4 为 `28/43`），gold-complete-but-refused=`10`（V4 为 `12`）。error fallback 为 `11/50`、scored 为 `8/43`，未达到 ≤1/50；Planner 仍有 8 个 scored invalid plan/anchor fallback。MC04 仍为 false sufficient，且新增 MC06/CS07 仍显示生成放行但 gold coverage 不完整。该轮不支持上线结论。
- V5-C 先完成了对 V5-B 保存响应的离线逐题重放，记录在 `backend/data/evaluation/controlled_retrieval_v5c_audit/v5c_offline_replay_summary.json` 与 `v5c_fault_table.md`。V5-B 的 8 个 scored fallback 全部属于必须继续拒绝的语义/契约问题：4 例 required anchor 不是问题原文中可精确回溯的片段，4 例 requirements 为空；没有发现可由 optional 字段归一化、单值/列表包装或枚举大小写映射安全修复的候选。3 个 unscored fallback 也都是空 requirements。合成 10 项回归全部通过，故不修改 Planner 校验或语义策略；正式运行前没有发现 JSON 截断、超时或服务错误。
- V5-C 随后在同一数据集、Child/Parent 快照、模型目标、embedding/reranker、candidate/rerank 上限和预算下完成一次新 full-50，输出为 `backend/data/evaluation/controlled_retrieval_v5c_formal/draft_20260909T105539685251Z/`，50/50 且 `corpus_unchanged=true`。结果为 Complete@20=`38/43`、Macro EGC@20=`92.5581%`、Complete@5=`38/43`、Macro EGC@5=`92.5581%`、final sufficient=`31/43`、生成=`32/50`、false sufficient 仍为 `DEV2-MC04/MC06/CS07`；但 fallback 为 `13/50`、scored=`10/43`，未达到 ≤1/50。相同源码与配置下相对 V5-B 出现随机响应差异：Complete@20/EGC@20/final sufficient 未变，Complete@5 增 1，但 fallback 增加 2；不能将其宣称为质量或接口改善。V5-C 结论为“不通过”，错误放行仍是主要风险，详见 `docs/CONTROLLED_RETRIEVAL_V5C_REPORT.md`。
- V5-C 离线诊断已覆盖 MC04、MC06、CS07：三题均被 Inspector 判为 complete、coverage_sufficient 提前成立，均未触发 gap query；主优先级假设是 independent requirement / comparison subject / condition-dimension 与 evidence bundle 绑定过宽，导致缺少独立证据时提前停止，而不是本轮扩大 query。V6 只修已证实的绑定主因，不在 V5-C 中实施。
- 下一轮只进入 V6 诊断：冻结 Query、检索参数、Validator、Evidence Set Builder 和 V5-C 的 fail-closed Planner；先用 MC04、MC06、CS07 trace 区分 Plan 遗漏、Validator 误判、融合/打包丢失，再只修已确认的独立 requirement 绑定与充分性主因。V6 必须同时报告完整证据/Macro EGC、false sufficient、gold-complete-but-refused、gap→补查→缺失证据→最终 packed 的链路，不以增加拒答单独宣称质量提升。
- V6-A 修复了三处已复现的确定性缺陷：`bundle_relation` 从原始 Inspector JSON 经适配器、Validator 到 Builder 全程保留；packed gate 现在核对最终 inspection 认证的任一存活 OR bundle 及其全部 AND 成员；comparison 允许同一主体对应多个独立维度 requirement，并校验主体/维度绑定。Planner 新 span 字段改用 `qID`/`start_id,end_id`，不接受模型自行计算的字符偏移；审计记录保存原始结构化响应、规范化计划/检查摘要和归一化错误位置。单个 complementary bundle 可作为一个 AND 集合，多 bundle complementary 仍 fail closed。
- V6-A deterministic 回归：controlled retrieval `36 passed`；parent pipeline、agent context、controlled retrieval 合计 `50 passed, 1 warning`；Docker 测试容器内全套 `326 passed, 6 skipped, 1 warning`；Ruff/format/diff check 通过。Windows 主机直接执行全套的 12 个失败是 Docker 内部数据库主机名不可解析造成的既有基础设施问题。
- 固定 5 题非 benchmark smoke 已保存原始 Planner/Inspector 响应、规范化结果和逐题人工审查，见 `backend/data/evaluation/controlled_retrieval_v6_audit/smoke_20260909T201133/`：yes/no、enumeration、negation/exception 仅结构上被接受；其中 yes/no 只绑定了 `Does`，不能算语义通过。comparison 因模型未绑定 `subject_spans` fail closed；scenario 因被分类为 enumeration 但未独立拆分 fail closed。该结果不是质量成绩，且不证明枚举完整或 Inspector 语义充分性正确。
- V6-B 已在 V6-A 基础上做 Planner 契约简化：comparison 可从唯一精确 subject anchor 恢复主体并记录来源；单一 scenario requirement 可保留多个条件；yes/no 不能只绑定疑问词/义务词；exception 可引用前一 requirement 的共享对象。Builder、packed gate、Query、检索配置保持冻结。
- V6-B Planner-only smoke 已保存原始 Planner JSON、规范化计划和逐题人工审查，见 `backend/data/evaluation/controlled_retrieval_v6_audit/planner_smoke_20260909T210741/`。原 5 题加 3 个预先固定迁移表述共 `8/8` 结构上可解析，但 enumeration 丢失共享范围，scenario 的 object/condition 角色仍不稳定，comparison anchor 质量有风险；因此不是语义通过，也不是质量成绩。前两轮记录仍保留在 `planner_smoke_20260909T210053/` 和 `smoke_20260909T201133/`。
- V6-B 回归结果：controlled retrieval `41 passed`；parent pipeline、agent context、controlled retrieval 合计 `55 passed, 1 warning`；Docker 测试容器全套 `331 passed, 6 skipped, 1 warning`；Ruff/format/diff check 通过。
- V6 正式 50 题闸门仍未通过，本轮没有新的 benchmark 成绩；下一步只继续审查共享范围与 anchor/subject/object/condition 角色契约，不对 MC04/MC06/CS07 做特判。
