# 政策 RAG 全链路架构选型与升级对比清单

后续工程变更（2026-09-10）：根据用户明确要求，词法分支已升级为 SQLite FTS5 BM25，
并与向量通过 RRF 融合，默认启用。见[工程实现说明](HYBRID_RETRIEVAL_IMPLEMENTATION.md)。
下文关于 PostgreSQL FTS/默认关闭的描述保留为选型时的历史状态，不代表最新运行代码。

日期：2026-09-10。对象：`policy-research-agent`，当前 `develop` 工作区。

本文是选型与实施指导，不代表已经实施、上线或获得新增 benchmark 成绩。本轮只新增本文，不修改运行时代码、默认开关、数据库、模型或原评测集。工作区已有未提交修改，本文描述的是所检查工作区，而不是仅描述分支 HEAD。

## 1. 结论：采用成熟组件，固定证据契约，允许替换编排

推荐：**模块化单体 + 可重放的结构化文档中间层 + Parent–Child + 可插拔双路检索 + Child 重排/证据检查 + 证据优先的 token 打包 + 有来源约束的生成**。先保有稳定的单轮 RAG，再把有界的 Agentic Retrieval 接到同一检索服务上。

“一次跑通”应指安装、导入、查询、引用、测试可以重复执行，不代表任何模型组合首次就达到完整证据目标。没有统一规定 PDF 必须用哪个解析器、Child 必须多少 token、政策 RAG 必须用 Milvus 的行业配方。

LangChain 官方区分固定检索后生成、Agentic 和混合验证流程；这是架构分类，不是质量认证。我们的选择是保留可预测主链路，把规划与补查作为增强，而不是让所有请求都先通过复杂 Planner。[官方架构说明](https://docs.langchain.com/oss/python/deepagents/retrieval)

### 建议的两个运行配置

| 配置 | 用途 | 编排 | 失败行为 |
|---|---|---|---|
| Stable Policy RAG | 常规查条款、查适用范围、查期限 | 原问题检索 → 重排 → 证据检查 → 打包 → 生成与引用检查 | 证据不足明确说明；不声称完整回答 |
| Controlled Policy RAG | 多文档比较、多个条件/例外、复杂研究 | 复用主链路；规划、检查缺口、定向补查、有界停止 | 规划/验证错误与无证据分别记录；严格模式仍 fail closed |

这不是提议把当前 Controlled 错误偷偷降级为 Classic 放行。若将来允许“只回答有证据部分”，必须是明确的新输出策略，标注未回答部分，并单独评测；不得计作 `coverage_sufficient=true`。

## 2. 本轮核对到的项目事实

| 模块 | 已有实现/代码默认 | 结论 |
|---|---|---|
| PDF | `pypdf` 提取正文；低文本页用 Tesseract OCR；PyMuPDF 补 layout hints | 不是没有解析工具；复杂版面、表格和脚注应单独抽样验收 |
| 结构切分 | structure-aware 开启；Child target/max/overlap 为 320/380/50；Parent 600–1500 | 已是 Parent–Child，不应重新写一遍 |
| Embedding | 默认 `BAAI/bge-small-en-v1.5`，384 维；输入预算 512 | 英文模型与英文政策匹配，不需要因“英文”强制换云 API |
| Contextual header | LLM header 默认关闭；结构 prefix 有预算 | 保留当前方向，不增加无验证的逐 Child LLM 调用 |
| 词法检索 | `retrieve_lexical()` 用英文 `ts_rank_cd`，正文 OR-term 匹配 | 是 PostgreSQL FTS，**不是 BM25**；默认候选数量为 0 |
| 过滤 | 词法分支可按 document IDs、审批与访问等级过滤 | 已有基础；不能据此推断所有政策时间/地域字段都已参与检索 |
| Reranker | 模块默认 `BAAI/bge-reranker-base`，支持 provider 配置 | 保留为固定对照，实际运行需导出 active config |
| Parent/packing | 公共 `parent_pipeline` 解析 Parent、token 打包；Controlled 检查打包后 coverage | 不应恢复字符硬截断或另建第二条 Full Corpus 实现 |
| 上下文 | 默认 6000 tokens、8 parents、每文档 5 parents | 是当前起点，不是行业最优值 |
| Controlled | 默认关闭，工作区含实验修改 | 不能把 smoke 通过写成正式 50 题通过 |

以上默认值不等同于环境变量、持久化配置覆盖后的实际运行参数。任何正式对照必须导出最终生效配置、代码 revision/dirty diff、模型版本和 corpus hash。

## 3. 文档进入知识库：逐层选型

| 环节 | 本项目建议 | 替代模式 | 代价/风险 | 验收方式 |
|---|---|---|---|---|
| 来源采集 | 上传与指定官方 URL 导入；保存原件、URL、下载时间、内容 hash、来源类型 | 全网自动抓取 | 重复版本、链接失效、非权威来源混入；不作为第一阶段依赖 | 重试不重复入库；来源可追溯；失败文件明确列出 |
| 导入作业 | 独立 worker + 持久化状态、幂等、失败重试 | API 请求内同步完成；复杂分布式队列 | 同步易超时；复杂队列增加部署成本 | 进程重启后可恢复；失败不显示 ready |
| PDF 解析 | 保留现有 extractor；通过适配器并行试验 Docling，验收后再选复杂 PDF 默认解析器 | 纯文本解析；云文档解析 | 新解析器有资源/模型下载成本；云方案有隐私与费用问题 | 代表性双栏、表格、脚注、扫描页、跨页列表逐项核对 |
| OCR | 只对需要的页面执行；检测乱码与异常阅读顺序，不能仅看字符数 | 所有页面强制 OCR | 慢，且原本正确的数字和专名可能被改坏 | 页级错误率、日期/编号准确率、OCR 触发原因 |
| 中间表示 | 保存有版本的 ParsedBlock：正文、标题、列表、表格、脚注及来源位置 | 只保存扁平 text/Markdown | 扁平化后难以定位丢失、恢复表格和准确引用 | 能从 Child 回到原 PDF 页/位置；清洗前后可比较 |
| 清洗 | 保守去重复页眉页脚，保留原文映射 | 大规模正则删数字、短行、references | 可能删除条款编号、脚注例外和适用条件 | 删除内容抽样审查；例外/脚注召回测试 |
| 表格 | 保留表头、行列关系、caption；检索文本中重复必要表头 | 全表转一长串；只做图片检索 | 扁平串易把主体、日期、要求错配 | 用表格问题检查答案能否定位正确行列 |
| 结构树 | 标题层级、字体、位置、编号综合检测；失败回退现有切分 | 纯 regex；LLM semantic chunking | 前者误把列表当标题；后者成本和边界不稳定 | 层级准确率、列表误识别、跨页标题、脚注归属 |
| Parent | 逻辑 section 优先；超长按下级结构拆分，不跨 section 凑长度 | 固定大块 | 固定大块破坏条件/例外关系 | 碎 Parent 比例、超大比例、条款完整性 |
| Child | 保留 320/380/50 起点；段落→句子→token；只在同 Parent overlap | 更小切片；大段整段 embedding | 小块缺语义、大块稀释相似度；都应比较而非凭感觉 | 无跨 Parent；证据可定位；分布与检索效果 |
| 脚注/交叉引用 | 保留附件、脚注、显式条款引用关系；按需扩展引用目标 | 默认忽略；全量知识图谱 | 忽略可能漏例外；全图谱会扩大工程范围 | 需要引用目标的测试能保留完整证据链 |
| Embedding 输入 | title + section path + Child；只 embed Child | LLM header；全文 Parent embedding | 额外成本、输入截断、检索精度下降 | 用实际 embedding tokenizer 检查完整输入，记录溢出 |
| 入库发布 | 新 index generation 构建、校验完成后再切换 active 指针；旧版可回滚 | 原地覆盖当前 chunks | 中途失败可能使数据库与索引不一致 | 无半成品对外可见；回滚测试；删除一致性 |

Docling 提供结构化文档表示，以及结构驱动和 token-aware 的 chunking，适合作为可替换解析/结构输入。它不自动保证符合我们的 Parent、Child 和引用契约，仍需适配与测试。[Docling 官方 chunking](https://docling-project.github.io/docling/concepts/chunking/)；[技术报告](https://arxiv.org/abs/2408.09869)

**关键：不要一边换解析器，一边换 Child 大小、embedding 和 gold 映射。** 先在独立文档副本上做解析验收，冻结输出，再进入下一阶段。

## 4. 政策 metadata：不仅是标签

| 字段 | 用途 | 约束 |
|---|---|---|
| `document_version_id`、source hash | 可复现、避免混版 | 不用文件名充当唯一版本 |
| jurisdiction、issuer | 地域与发布主体 | 用户明确指定可过滤；模型推断不宜直接硬过滤 |
| publication/effective/repealed dates | 回答某时点要求 | 发布不等于生效；未知值保持未知 |
| supersedes / superseded_by | 新旧政策关系 | 基于明确证据或人工确认，不凭下载时间判断 |
| entity scope | 适用主体 | 问题未说明主体时必要澄清，避免擅自适用 |
| policy/standard/guidance/case study | 区分规范与示例 | 案例做法不能生成成普遍义务 |
| section path、clause number | 精确条款定位与加权 | 编号宜支持原样匹配，不完全依赖英文词干化 |
| ACL、approval | 数据权限 | 所有检索、Parent expansion、缓存与工具路径都必须遵守 |
| topics/tags | 辅助发现与排序 | 不把自动标签当成真实适用范围 |

义务强度 `must/should/may`、否定、条件和例外应保留在原文与证据层。可以结构化辅助检索，但不应通过自动标签替代原条款。

## 5. Embedding、数据库和检索选型

### 5.1 Embedding

| 方案 | 适用性 | 优点 | 代价 | 本轮建议 |
|---|---|---|---|---|
| 当前 BGE-small-en-v1.5 | 英文政策、本地复现 | 已接入，384 维、512 输入限制清楚 | 小模型能力可能限制语义召回 | **保留为基线** |
| 同系列更大英文模型 | 已证实 dense 语义召回不足 | 便于独立对照 | 内存、延迟与全量重嵌入；维度可能不同 | 冻结 chunk 后测试 |
| 多语言模型 | 后续出现中文问题检索英文文档/多语言文档 | 可直接支持跨语言候选 | 未必在当前纯英文数据更优 | 出现真实需求再测 |
| 托管 embedding API | 接受数据出域、希望减少本地推理维护 | 运维简化 | 网络、限额、费用、模型版本与维度迁移 | 作为 provider 替代，不作为“英文必选” |

BGE 官方模型卡给出了 small-en-v1.5 的 384 维和 512 序列长度。现有英文方向合理，但模型卡成绩不能替代政策数据实测。[BGE 模型卡](https://huggingface.co/BAAI/bge-small-en-v1.5)

必须核对 query/passage 各自输入格式、归一化、tokenizer 和实际 provider 行为；同一字符串用不同模型 tokenizer 的 token 数不相同。切换 embedding 后不得混用旧向量，也不得沿用旧距离阈值而不校准。

### 5.2 数据库与词法检索

| 方案 | 检索能力 | 运维/改造 | 何时选 |
|---|---|---|---|
| PostgreSQL + pgvector + 原生 FTS | 向量 + 英文词法排序 + SQL metadata/权限 | 当前成本最低；FTS 不是 BM25 | **当前主方案**，先验证双路融合是否有收益 |
| PostgreSQL + pgvector + Elasticsearch | 向量保留；专业 BM25/全文能力独立提供 | 多一套服务，增删改同步、权限过滤与恢复复杂 | FTS 不满足要求且 BM25 对照有实质收益 |
| PostgreSQL + Milvus | 业务数据保留 Postgres；向量/稀疏检索放 Milvus | 数据双写、ID 映射、备份监控与迁移 | 实际规模、并发或检索能力需求证明值得迁移 |

PostgreSQL `ts_rank_cd` 是 cover-density 排序；Elasticsearch 默认 similarity 为 BM25；Milvus 也提供 BM25 全文能力。三者不能混称。[PostgreSQL 文档](https://www.postgresql.org/docs/current/textsearch-controls.html)；[Elasticsearch 文档](https://www.elastic.co/docs/reference/elasticsearch/index-settings/similarity)；[Milvus 文档](https://milvus.io/docs/bm25-function.md)

不要因为 Milvus 常见就迁移。先测当前数据库在目标数据量与过滤条件下的延迟、候选召回和资源占用，超过实际目标再决策，而不是用任意文档数量作迁移界线。

当前词法 SQL 在查询中对 Child 正文计算 `to_tsvector`。扩大数据后应评估持久化搜索字段与匹配的 GIN 索引，并用查询计划验证，而不是假定已经有高效倒排路径。标题/编号字段可分开处理，避免编号被词干化规则损坏。

### 5.3 检索到生成对比清单

| 环节 | 推荐起点 | 暂不默认采用 | 主要验收 |
|---|---|---|---|
| Query prepare | 保留原文、会话中明确实体和显式范围 | 自动引入问题外实体 | 不丢 actor、否定、条件、时间 |
| Query rewrite | 单轮问题默认不重写；指代问题做独立问题化，并保留原 query 通道 | 每题强制主改写、HyDE、多次同义扩展 | 原文保真、真实增益、无范围漂移 |
| Metadata filter | ACL 强制；用户明确范围过滤；不确定 metadata 软排序 | 把模型猜测的国家/年份硬过滤 | 错误排除率、空结果率 |
| Dense retrieval | 当前 pgvector Child ANN；另有 exact 对照 | 先调生成解决 ANN 漏召回 | ANN 相对 exact 的召回与延迟 |
| Lexical retrieval | FTS 独立候选通道，作为新实验 profile | 直接声明加入 BM25 就会提高效果 | 条款编号、缩写、专名题的新增证据 |
| 初始 fusion | 按 Child ID 去重，RRF 作为 rank-based 对照 | 直接相加不同量纲分数 | 候选 union 完整度、候选预算、来源贡献 |
| Rerank | 当前 cross-encoder；section path + Child | 完整 Parent 先展开再打分 | 重排前后完整证据损失、reranker 截断 |
| 复杂问题保留 | 先全局候选，再为独立需求保留补充证据 | 只选全局最相似的重复片段 | coverage 增量、证据冗余、子问题覆盖 |
| Evidence judge | 区分 supported/partial/background/missing；AND/OR 语义明确 | 主题相关或高分即完整支持 | false sufficient、漏放行、人工一致性 |
| Parent expansion | Child 通过检查后再展开；Parent 去重 | Parent 内容替代 Child 支持证明 | Child provenance 不丢、扩展文本有界 |
| Context packing | 先保留完整支持集合，再放必要 Parent 上下文 | 只按分数逐块填满；字符硬截断 | 打包前后 coverage 差、token、重复率 |
| Generation | 回答要求/主体/条件/例外/时间；区分案例和规范 | 用模型常识补政策事实 | claim correctness、modality、范围和完整性 |
| Citation | claim → supporting Child/span → 原 PDF 页/位置 | 只引 Parent 或文档首页 | 引用存在、真正支持该 claim、关键 claim 均有引用 |
| Answer validation | 确定性引用/预算检查 + 经人工校准的语义审查 | LLM judge 分数直接等于事实正确 | 不支持 claim、错义务强度、虚假完整性 |
| 无证据 | 明确“provided corpus 不足以建立该事实” | 把检索失败说成现实中不存在；一律追问 | 明确问题直接不足响应；歧义才澄清 |

pgvector 官方支持与全文检索组合，也提示 ANN 与过滤的相互作用。先核对安装版本和查询计划；不能假定项目数据库支持新版本的 iterative scan。[pgvector 官方说明](https://github.com/pgvector/pgvector)

必须单独实验一个风险：词法/定向补查找到了真实证据，但按原问题计算的统一距离门槛又将其删除。不能直接取消安全 gate；应记录 branch、触发 query、原问题/子需求分数，定位被删证据，再比较有语义验证支持的分支策略。

**6000 tokens 不等于应当填满 6000 tokens。** 必要证据先入包；其余 Parent 内容只有增加理解价值才加入。长上下文研究发现相关内容位置可影响回答表现，因此扩大窗口不能替代证据选择；该研究也不是当前模型必然出现同幅退化的证明。[Lost in the Middle](https://arxiv.org/abs/2307.03172)

## 6. Agentic 演进：换调度方式，不换知识库

建议共用以下小范围接口，尊重现有模块，不为接口大规模搬文件：

| 边界 | 输入 → 输出 | 可替换内容 |
|---|---|---|
| Extractor | 原件 → ParsedDocument/Blocks | 当前 PDF extractor / Docling |
| Chunker | Blocks/结构树 → Sections + Children | 结构策略与 Child 大小 |
| EmbeddingProvider | 受预算约束的 Child 输入 → vectors | 本地/API 模型 |
| Retriever | query + scope + index version → Candidates | ANN、FTS、未来 BM25 |
| EvidenceAssembler | 原问题 + Candidates → evidence bundles | 重排、检查、coverage-aware 选择 |
| ContextPacker | bundles + Parents + budget → Pack + provenance | 压缩/扩展/多样性策略 |
| Answerer | question + Pack → claims + citations + gaps | prompt/生成模型 |
| Orchestrator | question + state → 调用以上服务 | 单轮流程 / 受控 Agent |

推荐 Agent 的边界：只允许规划原问题内的需求、检查已有结果、定向检索缺口、在预算内停止。先沿用已配置轮数，不把加轮数作为主要优化；不赋予任意网页抓取、数据库写入或自由构造 quote 的能力。

Planner schema 应只保留对检索决策真正必要的信息。原问题/span 映射为事实基础，细分需求用于补查，不能让格式恢复凭空增加需求。宽泛 requirement 的合法 JSON，不等于完整语义分解。当前 Inspector/Builder 的确定性检查继续保留。

停止语义分为两类：

- 成功停止：所有必要证据充分支持，且打包后仍保留合法支持集合。
- 预算/无新增/错误停止：终止搜索，但不等于 evidence sufficient；按明确产品策略拒答或带缺口回答。

Selected-document、Full Corpus 与 Agent internal search 必须调用同一证据与打包服务。Live Web 维持独立来源模式；正式导入 Library 才走版本化 ingestion。MCP 只是未来对外暴露工具的一种接口，不改善召回本身，不是当前架构升级的前置条件。

## 7. 如何避免每轮都从 PDF 重跑

每阶段保存输入 hash、配置、代码/模型标识和输出产物。缓存不仅看问题字符串，还要包含 corpus/index version、检索范围与权限；权限变化必须失效。

| 变更 | 最早重跑阶段 | 不必重跑 | 成本级别 |
|---|---|---|---|
| Answer prompt/生成模型 | generation + citation/答案评测 | 提取、向量、检索（Pack 可用且预算相容时） | 低–中 |
| Packing/上下文预算 | packing + 后续 | 提取、embedding；已保存候选可复用 | 低–中 |
| Reranker/证据判断 | rerank/inspection + 后续 | PDF 与向量；需确保候选快照足够 | 中 |
| Query/fusion/candidate K | retrieval + 后续 | PDF、Child 向量 | 中 |
| FTS/BM25 backend | 词法索引 + retrieval + 后续 | 解析、Child、dense 向量 | 中 |
| Embedding 模型/prefix | Child embedding + 向量索引 + 后续 | 原件与结构输出；预算变化可能需重切 Child | 中–高 |
| Child/Parent 切分 | chunking + embedding + 后续 | 已冻结且合格的 ParsedDocument | 高 |
| PDF 解析/OCR/正文清洗 | extraction 及全部下游 | 原件 | 高 |
| Postgres → Milvus | 导出导入/索引/过滤兼容验证 + retrieval 回归 | 同模型兼容向量可复用，不必天然重新 embedding | 中–高 |
| 单轮 → Controlled | orchestrator + affected-stage/end-to-end 评测 | 合格知识库、向量与公共服务 | 中 |

上述成本是相对级别，不是工期承诺。模型、tokenizer、候选范围变化导致缓存不兼容时必须失效。

`reembed` 只更新现有 Child 表示；改变解析/结构/切分需要 full reprocess。旧文档可保留 flat fallback，不能因没有 section ID 崩溃。

## 8. 分阶段评测：定位损失，不只看最终分数

| 阶段 | 固定条件 | 指标/检查 | 能回答的问题 |
|---|---|---|---|
| Extraction | 同一原 PDF | 页覆盖、阅读顺序、表格/脚注/日期编号人工核对 | 证据是否在解析时丢失？ |
| Chunking | 同一解析输出 | 原文覆盖、Parent 边界、重复率、token 分布、关键条款完整 | 证据是否被切坏？ |
| Dense exact | 同一 Child、问题、模型 | Evidence Group Coverage@K、Complete@K | embedding 本身能否找到完整证据？ |
| ANN | 同一向量和过滤条件 | 相对 exact 的 ANN Recall@K、p50/p95 | 近似索引是否漏了本来能找到的证据？ |
| Hybrid candidate union | 同一 dense、词法配置 | 新增完整题/退化题、group coverage、候选数量 | 词法是否真正补缺？ |
| Rerank | 相同候选集 | MRR、nDCG（需相关性等级）、重排前后 EGC/Complete | 真证据是否被重排截掉？ |
| Builder/packing | 同一证据候选 | packed coverage、AND/OR 完整度、token、去重 | 完整证据是否在最终上下文丢失？ |
| Generation | 同一 context | 答案事实与义务强度、引用正确/完整、未支持 claim | 已有证据是否被错误表述？ |
| Controlled | 同一 corpus/model/基线 | 覆盖增量、false sufficient、错误回退、停止原因、延迟/费用 | 增加规划是否值得？ |

指标定义必须固定：Hit@K 只证明至少命中，不证明多证据问题回答完整；EGC 是 gold evidence groups 覆盖比例；Complete 要求全部必需组满足。ANN Recall 是与 exact 搜索的近似一致性，不是政策答案召回率。

Ragas 可辅助测 context recall、faithfulness 等，不应替代我们的 frozen evidence groups、义务强度和人工语义审核。[Ragas 指标](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/)

### 实验纪律

1. 保留既有 50 题与所有旧结果。长期参与调参的题视为开发诊断集，不宣传为完全未见测试。
2. 将来换 chunk 时，新建版本化证据映射；用原 PDF 版本/page/span 作为可迁移来源锚点。旧 ID 不覆盖，映射必须人工复核。
3. 新增独立文档与题目作为 held-out；同一文档变体/改写问题不要泄漏到训练与验收两侧。
4. 一次只改变一层；先离线阶段测试，再小规模端到端，最后全量对照。
5. LLM judge 先以人工样本校准；报告 disagreement。固定温度也不能消除全部响应波动，关键结论做重复运行。
6. 同时报 numerator/denominator。未完成全文复核的 unanswerable candidate 不进入正式拒答正确率分母。
7. 报告新增 complete 与 regressed case，而不只报均值；报告 false sufficient 的数量和其相对放行题的比例。
8. 不能靠扩大拒答量宣称“更安全更好”；同时看完整证据却被拒答、回答覆盖率与错误放行。
9. 不设置假冒行业标准的“必须 95%”。验收阈值由实际业务风险、标注质量和基线确定。

## 9. 建议执行顺序与验收门

| 顺序 | 工作包 | 交付与通过条件 | 不做什么 |
|---|---|---|---|
| P0 | 冻结现状、保存各阶段产物、为失败题定位最早证据损失 | 同一问题可查看 extraction→candidate→rerank→pack→answer；先明确损失位置 | 不再盲改 Planner prompt |
| P1 | 文档解析与 provenance 抽检；引入可替换 ParsedDocument 边界 | 表格、脚注、编号、跨页结构可追溯；新 parser 独立验收 | 不全量替换 parser 与模型 |
| P2 | 原 query dense/FTS 候选对照；exact/ANN 对照 | 候选覆盖新增/退化清楚；确认是否真需要 BM25 | 不与 chunk/embedding 一起改 |
| P3 | 固定候选测 rerank、证据 bundle 和 packing | 必需证据不会因重复或旧 first-round 顺序被挤掉；false sufficient 不恶化 | 不扩大 context 掩盖选择问题 |
| P4 | 固定 Pack 做 generation/citation 审核 | 条件、例外、义务强度准确，关键断言有真引用 | 不以模板完整代替事实完整 |
| P5 | 在稳定主链路上验证 Controlled 增量 | 同一数据下完整证据净增，错误/延迟/成本可接受 | 不把 schema parse 通过当最终验收 |
| P6 | 新文档规模与部署验证 | 新 held-out、重启恢复、权限、备份、目标并发测量 | 未证明需要前不迁移 Milvus/微服务 |

对当前 MC06、CS07 等历史难题，仅作为诊断样本：先看相关证据是否出现在候选 union，再决定改召回、重排还是打包。它们不能成为题目特判规则，也不能作为全部验收标准。

## 10. 运行与安全的最低完整性

- 保留现有前后端，优先 API + ingestion worker + PostgreSQL 的本地 Compose 部署；模型/解析器版本固定，提供健康检查、持久卷和备份恢复说明。
- 文件上传校验类型、大小、PDF 页数/处理超时；抓取限制协议、跳转和目的地址，防止 SSRF。
- 原文是数据，不是系统指令。文档中的提示注入不得修改工具权限、输出策略或执行流程。
- 普通日志不记录完整敏感原文/API key；debug 产物单独控制权限、保留期限。
- 原件、数据库、索引版本应可以一致恢复；删除文档同时处理 Child、向量、Parent 和缓存。
- LoRA 暂缓：它不能补回未召回证据或修复被切坏的文档。未来有足量、干净、独立划分的任务数据时，可评估规划/格式/领域表达微调，但不把易变政策事实主要写进模型参数。

## 11. 供后续开发 agent 使用的约束

每个工作包只改一个可观测边界；先读真实调用链。不得同时替换 PDF 解析器、chunk、embedding、reranker、数据库；不得修改既有 gold 以适应实现；不得把失败恢复改成静默放行；不得另写 Full Corpus 或 Agent 专属检索副本。先交付阶段测试与旧流程回归，再交付同变量 benchmark 和新增/退化 case 清单。

**我们要固定的是数据与证据契约，不是把某个框架锁死。先形成稳定可定位的 RAG，再让 Agent 以受控方式调用它。**
