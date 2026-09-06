# 项目重建与评测任务清单

记录日期：2026-09-05。工作目录：`D:\AIWorkspace\Projects\policy-research-agent`。

本文件是静态代码核对后的任务提取，不代表功能已在新环境运行通过。本轮只新增计划文档，没有修改数据库、前后端业务代码或启动服务。数据库和页面的最终业务改动尚未给出，不能据此默认进行整库重构或 UI 重做。

### 执行更新：本地启动阶段

2026-09-06 CI 与本地测试修复：修复 Ruff 超长行及 21 个未格式化文件，`ruff check .` 与 `ruff format --check .` 均通过；推送提交 `32bb7ff` 至 GitHub main。补齐 `PERSISTENCE_BACKEND=memory` 时使用 LangGraph `MemorySaver` 的启动分支，避免本地无数据库时强制连接 PostgreSQL。容器后端重建并 healthy；无数据库的测试环境中 190 项通过、5 项跳过，12 项仍属于需要真实数据库凭据的集成测试，未纳入本轮 CI 修复。

2026-09-06 标签 v2：视觉核对 7 个关键 PDF 页面，区分精确证据页与跨页片段起始页；补齐当前 8 题的重叠及跨文件等价答案。v2 同标签比较结果为 Dense/Rerank Hit@5 均 8/8，MRR@10 为 0.854/1.000；4 项指标测试通过。样本小且无独立测试集，不作为简历最终指标。下一步扩充难题与独立测试集，并处理引用页码只取 page_start 的产品问题。

2026-09-06 标签 v3：新增 5 道跨技术标准与新加坡 Agentic AI 框架的英文检索题，视觉核验对应 PDF 页面；13 题开发基线 Hit@5 均 13/13，MRR@10 为 Dense 0.833、Rerank 1.000。仍是开发集，无独立测试、拒答集或生成质量评分；下一步应扩大问题覆盖并修复引用只取 page_start 的产品问题。

2026-09-06 引用范围修复：Citation 增加 page_end；后端检索/Agent 引用保留片段页范围，前端显示 `Page start-end` 并从起始页打开 PDF。后端镜像重建、前端 Vite production build 通过；容器内直接断言验证单页与跨页引用。没有改动数据库数据或检索排序。

2026-09-06 评测更新：新增 8 题开发检索对比程序与 3 项通过的指标测试，真实执行完成。已标注 Hit@5 两路均 8/8，已标注 MRR@10 为 0.625 / 0.875；AU04 人工复查发现等价证据标签遗漏，不能据此报告实际质量提升或退步。下一优先级为版本化补齐标签、PDF 页码核验及扩充题集。详见 EVAL_BASELINE_DEV.md，原始逐题结果仅存本地 data/evaluation。

2026-09-06 语料构建更新（覆盖此前未推送/单文档状态）：首次独立提交 3473dc5 已推送新 GitHub main，无旧历史。定向下载 DTA 三份官方 PDF，并导入旧项目新加坡文件；现有 5 份英文文件全部 ready，202 chunks / 202 vectors / 0 missing。重跑清单跳过全部已完成文件。仍不启用 Web Search；未清空或迁移数据库。见 CORPUS_BUILD.md 的来源、复现步骤和验收限制。

2026-09-06 后续推进：按用户要求暂不配置或验收 Web Search。经 Web 反向代理验证 Direct SSE 正常完成，历史接口可恢复两条 complete 消息、5 条引用和 3 个建议；未登录历史访问返回 401。已核对引用片段/预览子串关系及核心回答原文。新增 EVAL_SEED.md：5 道有证据的开发草案题、1 道待全文核验的拒答候选题、评测约束及引用预览不足。尚未进行浏览器交互验收或正式指标计算。

2026-09-06 最新状态（覆盖本节旧记录）：DeepSeek 已保存并真实调用成功；本地 embedding 实测 384 维。首份澳大利亚 PDF 已通过应用服务入库，ready / 17 chunks，完成服务层真实检索与带编号引用的生成。首次 rerank 因模型下载 DNS 失败回退 dense，补齐缓存后新进程验证 5 个结果均有重排分数；尚无正式指标、浏览器端到端验收或 Web Search 验收。详情见 CORPUS_PREFLIGHT.md 顶部。

当前状态更新：用户启动 Docker 后，db/backend healthy、web running。数据库实查用户/文档/片段均为 0，模型与搜索密钥未配置。已执行应用 PDF 解析器及六个测试文件（47 项通过，首次网络缓存失败已排除）；未入库、未调用真实模型/搜索服务。具体过程、复现命令和限制见 CORPUS_PREFLIGHT.md 最新进展部分。

最新一轮推进：Docker Desktop 再次启动失败，原因是本机 dockerInference 通信文件错误；此前 healthy 为历史验收结果，不是当前运行状态。已准备四份 PDF 本地副本并完成哈希及文本可提取性初检。用户已有 DeepSeek API，暂无搜索服务 API。详情见 CORPUS_PREFLIGHT.md；未执行数据库升级、文档入库、真实问答或联网验收。

- 远程仓库已由用户提供并配置为 origin：https://github.com/shldo/Policy_analyize_agent 。本地文件夹名称保持 policy-research-agent。git ls-remote 成功且未返回分支/标签，远端当前为空。尚未提交或推送；下方初始清单中“等待仓库地址”已解除。

以下状态覆盖下方初始盘点中的“未开始”说明：

- 已确认第一阶段采用本地 Docker Compose，后续兼容云部署。
- DB01：已补 Compose 迁移 018 挂载；独立空卷初始化成功，SQL 验证 token_usage 存在，数据库 healthy。已有数据库升级尚未实测。
- ENV01：部分完成。已启动 Docker Desktop，增加 .env.local.example 和 docs/LOCAL_SETUP.md，Compose 配置校验通过。网页计划端口 8080，数据库实际端口 55432，均绑定本机。
- 前后端未运行：构建拉取 Python/Node/Caddy 元数据时 auth.docker.io 连接超时；主机 curl 也超时。待 Docker Hub 网络恢复后重试。
- 当前缓存数据库镜像为 PostgreSQL 15.4 / pgvector 0.5.1；仓库检索代码包含 halfvec 路径，需在接入高维模型前升级并固定兼容镜像版本。当前数据库启动通过不代表全部向量路径兼容。
- 后端测试、前端构建、模型问答、真实语料及评测基线均未完成。没有删除原始数据或修改系统代理。
- 网络后续检查：Clash 127.0.0.1:7890 可连接 Docker Hub；在构建进程配置 HTTP_PROXY/HTTPS_PROXY 后，Python/Node/Caddy 元数据获取成功。
- 最新验收：Compose 构建退出码 0；前端 npm ci/build 完成、后端依赖安装完成；db/backend healthy、web running。http://127.0.0.1:8080/ 返回 HTTP 200，/api/v1/health 返回 status=ok、database=configured。以上覆盖前文“前后端未运行”的历史状态。尚未运行完整测试、模型问答或 UI 交互验收。
- 云部署前需处理已发现的具体权限缺口：backend/app/modules/auth/service.py 中管理员注册 secret 校验被注释，公开部署前应恢复受控管理员创建并补测试；本阶段只绑定本机。

## 1. 已完成与当前状态

| 编号 | 状态 | 工作与证据 |
|---|---|---|
| C01 | 已完成 | 原项目工作树复制到独立目录；256 个源文件做过逐文件哈希核对，包含 compose.yaml 本地修改 |
| C02 | 已完成 | 初始化独立 main 分支，未导入旧 Git 历史；当前没有提交、没有远程仓库 |
| C03 | 已完成 | 接入 .agenthub/manifest.yaml、AGENTS.md、CLAUDE.md 和 docs；补充密钥忽略规则 |
| C04 | 已完成 | 未复制依赖、缓存、数据库、上传文件、密钥、简历和课程提交包；proposal.pdf 保留作原始规格参考 |
| C05 | 已完成 | 现有评测脚本静态检查及社区/GitHub 简历与评测资料调研；尚未产生真实基准分数 |
| C06 | 已完成并暂停 | 旧项目中已有单页简历 v3 PDF 和 LaTeX；不在新代码库内。本轮不恢复制作 |
| C07 | 尚未完成 | 新环境安装依赖、恢复语料、启动验证、测试运行、GitHub 关联与首次提交 |

原目录：`C:\Users\Lucifer\Desktop\UNSW\9900\Project\capstone-project-26t2-9900-w11c-bread`。简历位于原目录 `output/resume/`。历史进度文档 PROGRESS.md 为继承资料，不能当作新项目实时完成状态。

## 2. 已有代码能力：继承实现，待回归验证

以下是现存实现，不是本轮新开发或已通过验收的功能。

| 能力 | 代码位置（相对项目根目录） | 验证重点 |
|---|---|---|
| 文档解析、切分、入库 | backend/app/modules/documents/ | PDF/DOCX/文本、页码来源、入库失败与去重 |
| pgvector 检索 | backend/app/modules/documents/repositories/embeddings.py | 选中文档/全库范围、权限、距离与候选数量 |
| 重排及失败回退 | backend/app/modules/documents/service.py、backend/app/modules/reranking/ | 配置生效、重排失败回退、实际模型记录 |
| 证据判断 | backend/app/modules/chat/rag/evidence.py | 动态阈值、证据不足和不同回答模式 |
| LangGraph ReAct | backend/app/modules/chat/rag/agent/{graph,state,tools,prompts}.py | 工具预算、路由、引用归并、终止条件 |
| 人工确认与状态恢复 | backend/app/modules/chat/rag/checkpointer.py、backend/app/modules/chat/router.py | interrupt/resume、会话隔离、断连恢复 |
| SSE、Token、历史 | backend/app/modules/chat/{router,schemas,history_repository}.py | 完成/失败记录、Token 字段、历史重放 |
| 对话 UI | frontend/src/pages/ChatPage.jsx、frontend/src/api.js | 已有流式回答、引用、轨迹和人工确认，不重复建设 |
| 文档库与模型设置 UI | frontend/src/pages/LibraryPage.jsx、frontend/src/pages/manage/ | 检索配置、上传状态、模型切换 |
| 后端测试 | backend/tests/ | 已有文件不等于全部运行通过；记录新环境结果 |

## 3. 已确认的代码缺口与直接任务

优先级：P0 为启动/基线前置，P1 为第一版评测，P2 为后续增强。所有任务默认未开始。

| ID | 优先级 | 修改位置 | 任务 | 验收标准 |
|---|---|---|---|---|
| DB01 | P0 | compose.yaml；backend/database/init.sql；backend/database/migrations/018_add_token_usage_to_chat_messages.sql | 补齐 token_usage 建库/升级链路。Compose 目前只挂载 001–017，init.sql 未包含该字段，而 history_repository.py 已读写它 | 全新独立数据库可写入和读取聊天 Token；旧库升级方案可重复执行；不得清除原库 |
| ENV01 | P0 | compose.yaml；.env.production.example；backend/.env.example；README.md；backend/README.md | 明确新项目数据库、卷、端口、配置和启动流程；核验模型服务及文件存储 | 新目录启动成功、健康检查通过；导入一份文档并完成带引用问答；记录命令与环境 |
| E01 | P1 | backend/scripts/evaluate_retrieval_recall.py | 从人工短文本内存相似度评测，扩展为调用真实检索服务的独立评测入口；保留原合成用例作为冒烟测试 | 经真实切分/入库/pgvector；输出逐题证据 ID、排名、Recall@5/10、MRR@10；未检索到结果正确计零 |
| E02 | P1 | backend/scripts/evaluate_reranker.py；backend/app/modules/documents/service.py；backend/app/modules/reranking/ | 对齐线上可配置重排服务。当前脚本直接实例化 TextCrossEncoder 且候选数固定为 3；新增可配置实验参数 | 同一候选集对比重排前后结果；记录实际模型、是否回退；区分候选 Recall@20 与最终 Recall@5 |
| E03 | P1 | backend/scripts/evaluate_evidence_threshold.py；backend/app/modules/chat/rag/evidence.py | 消除评测脚本硬编码阈值与线上动态配置不一致；分别处理本地/API 重排评分尺度 | 实验记录实际阈值；在开发集选择阈值，在保留测试集报告无答案拒答率与有答案误拒率 |
| E04 | P1 | backend/scripts/evaluate_embeddings.py；评测公共模块（拟新增） | 抽离测试数据加载和公共指标；消除 runpy + 相对路径依赖；评测输出配置快照 | 从文档约定入口运行；模型维度与参数可追踪；数据为空/标注缺失明确失败 |
| CI01 | P1 | .github/workflows/lint.yml；backend/pyproject.toml | 当前 CI 仅 Ruff，scripts 被 Ruff 排除；增加必要的后端测试与评测纯计算检查，按修复情况纳入脚本检查 | CI 不调用收费模型；检查召回指标、多证据/空结果等边界；后端回归结果可查 |
| FE01 | P1 | frontend/package.json；前端测试配置与用例（拟新增） | 当前 package.json 仅 dev/build/preview，没有测试入口；补核心交互测试 | 覆盖引用点击、SSE 完成/错误/中断、人工确认恢复；前端 build 和测试可运行 |
| CI02 | P1 | .github/workflows/lint.yml 或新增 workflow | 接入前端构建和关键测试，保存必要测试产物 | PR 可看到前后端结果；外部模型在线评测与快速 CI 分开 |

DB01 为静态发现的初始化不一致，尚未通过启动复现；实施时还应检查是否存在其他实际运行中的迁移机制。

## 4. 数据库、后端、前端后续改造范围

### 数据库

- DB02 / P0：先确认原始政策文档和数据库备份位置、保留数据范围；在隔离数据库恢复，校验文档、片段、向量、权限和聊天记录关系。当前新目录没有迁入运行数据。
- DB03 / P0：明确新版业务实体及字段变更需求，再编写增量迁移、数据兼容策略和验收 SQL。具体表改动待需求，不能先删除旧表。
- DB04 / P1：建立评测语料快照与来源映射。记录文档 hash、版本、页码/段落定位；切分策略变化时重新映射证据，避免用失效 chunk_id 比较。
- DB05 / P2（条件任务）：只有确定需要在线查询评测历史时才设计评测表。首版用 JSONL 数据集和 JSON/Markdown 报告即可，无须立即新增 eval_runs 等表。

### 后端

- BE01 / P0：在业务变更前更新 backend/docs/API_CONTRACTS.md，明确请求、响应、SSE 事件和兼容方式；改表影响 repository/service/schema 的位置逐项列出。
- BE02 / P1：在文档服务检索入口和 chat/router.py 记录分阶段耗时、候选/重排结果、实际模型、工具结果与 Token；优先供离线报告使用。区分首个 SSE 事件、首个回答 Token、完整回答耗时，暂停等待用户的时间单独统计。
- BE03 / P1：建立 direct RAG 与 ReAct 场景评测，覆盖选中文档、全库、网络、证据不足、人工确认、工具失败、预算耗尽和跨会话隔离。分别报告各类任务，不能合并成没有定义的“准确率”。
- BE04 / P1：为数据库/API 的实际改动扩展 backend/tests/test_chat_history.py、test_chat_router.py、test_chat_resume_router.py、test_document_search.py、test_document_service_reranking.py、test_agent_tools.py 等相关测试；不预先重写全部测试。
- BE05 / P2（实验后决定）：若失败分析证实召回瓶颈，再比较切分参数、查询改写或混合检索；不将 BM25/GraphRAG/多 Agent 当作默认新增功能。

### 前端

- FE02 / P0：用户尚未给出改版页面和交互细节。需求确定后按 API 契约修改 frontend/src/api.js、ChatPage.jsx、LibraryPage.jsx 及对应管理页面。
- FE03 / P1：后端字段变更时同步 CitationList.jsx、DocumentDrawer.jsx、HistoryPage.jsx；验证已有引用、轨迹、Token、恢复状态的兼容与错误提示。
- FE04 / P2（可选）：如确有产品需求，再增加评测结果页/实验对比页；离线评测不依赖建设后台看板。

## 5. 评测与交付任务

| ID | 工作 | 产物与验收 | 依赖 |
|---|---|---|---|
| DATA01 | 定义黄金数据格式与评分口径 | question_id、问题类别、语料版本、来源证据、参考答案、是否可回答、数据分组；标注规则可复用 | 业务场景确认 |
| DATA02 | 真实政策数据集 | 先 50–100 题核验流程，按覆盖情况扩充；开发/测试隔离；包含跨文档、无答案和近似干扰问题 | DB02、DATA01 |
| BASE01 | 保存修改前基线 | 环境可用后保存代码/数据/模型配置快照和逐题结果；原始分数未知，不预填 | ENV01、DB01、E01、DATA02 |
| EVAL01 | 检索对照实验 | 纯向量 vs 同候选重排；Recall/MRR、分类型结果、耗时、失败案例；无答案题单独评测 | BASE01、E02 |
| EVAL02 | 回答可靠性 | 引用是否支持对应结论；回答覆盖、拒答/误拒；若用 LLM judge，记录模型和提示词并人工抽检 | DATA02、E03 |
| EVAL03 | Agent 场景评测 | 定义任务成功条件，逐次运行轨迹、工具调用/恢复结果；离线模拟与真实模型结果分开 | BE03、环境可用 |
| PERF01 | 性能与成本 | 固定输入、模型、并发及冷热启动条件；报告样本数、TTFT、端到端 P50/P95、Token；成本只在价格与用量齐全时计算 | BE02、功能稳定 |
| REPORT01 | 可复现实验报告 | 数据与环境、参数、基线对比、逐题 JSON、汇总 Markdown、复现命令、限制及失败分析 | EVAL01–03、PERF01 按阶段交付 |
| DEMO01 | Client/Demo 验收 | 需求编号、任务、验收条件、反馈、修复记录；仅在有实际计时对照时报告人工效率提升 | 核心功能稳定 |
| GIT01 | 首次提交与远程关联 | 新仓库 URL 尚未提供；检查初始快照后提交、关联、推送，保留独立历史 | 用户提供新 GitHub 地址 |
| CV01 | 恢复简历迭代 | 从报告中选 2–3 个可解释指标，写明测试集口径；不照搬网络示例分数 | 用户恢复简历制作、REPORT01 |

指标注意：Hit@K 不等于多证据 Recall@K；Ragas LLM Context Recall 与 ID 召回不同；Faithfulness 不等于完整正确率。不要将 mock 测试通过率写成真实 Agent 成功率。工具失败、超时、模型调用失败应计入并单列，不能悄悄从分母排除。

## 6. 执行依赖和阶段验收

1. 范围确认：数据库变更、页面变更、保留语料、目标用户与任务；冻结首版 API/数据集口径。
2. 基础恢复：DB01 + ENV01 + DB02，独立环境跑通原能力，保存现状快照与测试结果。
3. 可测量基线：DATA01/02 + E01/E04 + BASE01；原则上先留基线再做检索优化。若业务结构必须先改，注明结构变更并保存可比较的数据版本。
4. 业务改造：DB03 + BE01/BE04 + FE02/FE03，按用户确定范围实施，前后端契约同步。
5. 评测增强：E02/E03 + BE02/BE03 + EVAL01–03 + PERF01；失败分析驱动下一轮优化。
6. 交付固化：CI01/02 + FE01 + REPORT01 + DEMO01；GitHub 信息具备后完成 GIT01。
7. 简历恢复：用户恢复流程后实施 CV01，目前继续暂停。

## 7. 尚待用户提供、不能自行推断的需求

- 数据库要改变哪些业务对象/字段，旧数据需要保留哪些；原语料或备份在哪里。
- 后端要新增、删除或改变哪些业务流程，是否仍保留政策研究定位。
- 前端要改哪些页面、语言、布局和交互。
- 新 GitHub 仓库地址；实际模型服务和可接受的评测调用预算。

这些信息不阻止继续细化文档与本地静态检查，但决定实际业务实现范围。当前任务提取已完成，表中开发任务尚未执行。
