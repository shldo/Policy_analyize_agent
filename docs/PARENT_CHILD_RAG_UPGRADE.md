# Structure-aware Parent–Child RAG 升级记录

后续 structure-v2 修订、Dev50 与最新回归结果见 [Chunk V2](CHUNK_STRUCTURE_V2.md)。
下方 A/B 数字保留为历史实验，不应当作最新版本结果。

更新：2026-09-08。状态：核心增量实现与测试通过，A/B 开发集和 B 的13道真实生成已完成；
语义审核与发布验收未完成，尚未发布到业务服务或推送 GitHub。

## 真实链路

入库：现有 extraction → layout/text heading detection → section tree → logical generation
parents → parent 内独立 token split → structure prefix + optional contextual header → child embedding。

检索：现有 pgvector ANN → structure path + child rerank → child distance/score gate →
section resolver（max score、保留 supporting child IDs）→ parent 去重 → whole-block token packing。
Classic 与 Agent internal/full-corpus 共用 post-retrieval service；Agent final writer 汇总并重新打包。
Citation 的 chunk_id、quote、page range 保持来自 Child，section_id/title 是附加信息。

## 数据库与兼容

迁移 `019_parent_child_sections.sql` 为 additive，新增 document_sections、document_chunks
的 nullable section_id/child_index、索引、同文档复合外键及自引用树外键。
新 volume 由 compose 挂载自动执行；已有 volume 必须手动运行该 migration，不能重跑 init.sql。
迁移本身不改变已有 202 chunks/vectors。旧 NULL section_id 使用 child 自身作为 flat context。

reembed 仅重算现有 child 与存储 prefix/header 的向量，不产生 section。
现有单文档 rescan 执行完整 extraction、structure、parent/child、embedding。
完整 rescan 会替换该文档旧 chunks 和所有模型向量，旧 chunk UUID 不再可解析；
历史消息保存的 quote/page 仍在，但升级前必须保留可恢复备份。默认不自动迁移业务文档。

管理员可用 `GET /api/v1/admin/documents/{id}/structure-status` 查询 schema/structured children
与 requires_full_reprocess；`POST /api/v1/admin/documents/{id}/reprocess` 是完整重处理的明确别名。
原 rescan 路由保留。新入库前检查 migration 019，缺失时明确报错而不是先改 pages。

## 配置默认值

| 设置 | 默认 |
| --- | --- |
| STRUCTURE_AWARE_CHUNKING | true |
| CHILD_TARGET_TOKENS / CHILD_MAX_TOKENS / CHILD_OVERLAP_TOKENS | 320 / 380 / 50 |
| PARENT_TARGET_MIN_TOKENS / PARENT_TARGET_MAX_TOKENS | 600 / 1500（不强制补齐短结构） |
| USE_LLM_CONTEXTUAL_HEADER | false |
| EMBEDDING_MAX_INPUT_TOKENS | 512（切换模型须核实） |
| EMBEDDING_SPECIAL_TOKENS / EMBEDDING_SAFETY_MARGIN | 4 / 16 |
| CONTEXTUAL_HEADER_RESERVE_TOKENS / STRUCTURE_PREFIX_MAX_TOKENS | 64 / 96 |
| CHILD_CANDIDATE_K / CHILD_RERANK_K / PARENT_CONTEXT_K | 30 / 8 / 4 |
| MAX_PARENTS_PER_DOCUMENT | 3 |
| RAG_CONTEXT_WINDOW_TOKENS / RAG_MAX_CONTEXT_TOKENS | 32768 / 8192 |
| RAG_RESERVED_OUTPUT_TOKENS / RAG_PROMPT_SAFETY_TOKENS | 2048 / 512 |

未知 generation tokenizer 使用 UTF-8 byte 上界，明显偏保守，不冒充 DeepSeek 精确 token 数。
普通日志不输出全文。embedding 超预算明确报错，而非依赖 provider 静默截断。

## 验证记录与剩余工作

- 隔离容器 policy-parent-child-db 从已有 baseline 备份恢复，业务库未变。
- Migration 019 连续运行两次通过；同文档 FK 阻止跨文档关联测试通过。
- 最终核心测试 261 passed / 5 skipped（数据库测试显式启用）；Ruff check 与 213 文件格式检查通过。
  5 个 skip 为已有 embedding shim 测试。修复新增 provider 安全契约对应的测试替身。
- A 组：冻结五文档 202 chunks，13 development，候选 30；Hit@5=1，
  Evidence Group Coverage@5=1，All Evidence@5=1，MRR@10=0.9230769。
  这是旧 flat 索引在新公共 runner 下的检索对照，不是旧应用生成链路的精确复现。
- B 第一轮：597 children，13/13 anchors 映射成功，Hit@5/Coverage@5/All Evidence@5=1，
  MRR@10=0.8205128。抽查发现加粗正文被误识别为标题，保留该结果作为诊断，不能作为推荐版本。
- B 第二轮：增加 short-block 标题约束；新加坡 section 从 366 降至 238、children 从224降至164。
  13/13 anchors 映射成功，上述检索指标不变，仍未优于 A。
- B 页码修正版：长 fallback parent 保留源 paragraph/page items，避免所有 child 被赋予宽泛父页范围；
  13道真实生成已采集，所有题 evidence gate 通过、所有引用编号有效。语义正确性仍需按已批准 rubric
  审核，不用引用编号有效性冒充 citation correctness。
- C 组、生成语义正确性、citation completeness 尚未完成；不可声称 B 优于 A。
- 原始本地报告：backend/data/evaluation/parent_child/，不提交敏感内容或配置。

下一验收重点：真实 PDF heading 误检、跨页 fallback provenance、全部 gold anchor 映射，
Agent 最终引用与被 pack 的 Child 一致性、web snippet token safety、运行统计与独立测试。
anchor 无法映射必须明确报告，不改 gold、不缩小分母后声称提升。

## 文件职责与 Phase 对应

| Phase | 文件（相对 backend，除 compose/docs） | 职责/验证 |
| --- | --- | --- |
| 1 | database/migrations/019_parent_child_sections.sql；documents/models.py；compose.yaml | nullable 迁移、树外键、同文档关联、重复迁移与隔离 FK 测试 |
| 2 | app/modules/documents/structure.py；pdf_extractor.py | 文本/字体/短文本块联合识别、层级树、无结构 fallback；真实 PDF 误检回归 |
| 3 | documents/parent_child.py；chunker.py | logical parent 选择、局部 child overlap、长结构拆分与物理页传递 |
| 4–5 | documents/service.py；repositories/embeddings.py；embedding/service.py | 新 ingestion、prefix/header、安全预算、只 embed child、旧数据检索兼容 |
| 6 | chat/rag/parent_resolution.py | supporting child 到 section，max score、去重、旧 child fallback |
| 7–8 | chat/rag/context_packing.py；generation.py；chat/schemas.py | 完整块打包、总 prompt 校验、输出预留、Child citation |
| 9 | chat/rag/graph/nodes.py；state.py | 在 child gate 后组装 generation context，保留原 graph 拓扑 |
| 10 | chat/rag/agent/tools.py；context.py；graph.py | internal/full-corpus 公共逻辑、最终跨工具去重打包、原引用编号、web 保持 flat |
| 11 | documents/admin_router.py；service.py | 结构状态、reprocess/rescan 与 reembed 区分、迁移前置检查 |
| 12 | tests/test_structure.py；test_parent_child.py；test_parent_context.py；test_parent_pipeline.py；test_parent_search_paths.py；test_parent_child_database.py；test_agent_parent_context.py；test_embedding_input_safety.py | 新单元/集成测试；旧 reranker 与 suggestions 测试契约更新 |
| 13 | evaluation/parent_child.py | 复用 v4、A/B/C 配置、逐题候选/距离/分数/parents/context/生成审核材料；不改 gold |

## A/B/C 对照与解释边界

A 使用恢复的旧 flat 480/120 + 已存 LLM header 索引；B 使用 320/50、structure prefix、header OFF；
C 开关与 runner 已提供，使用同样结构及 header ON，但尚未运行，不能判断额外 API 成本是否值得。
所有组固定同一 embedding/cross-encoder 与 30 ANN candidates；重排前20用于 Hit@20，前8进入证据和生成。
真实报告记录每题 distance/reranker score，可在评审后校准阈值；本轮未改阈值。

不能因为 Hit@5 饱和就宣称架构升级有效：当前小开发集更适合发现回归，MRR 下滑提示需要比较
相邻 Child 排名、结构误检与精确证据的位置。下一步先做结构与生成评审，再决定 C/Top-K 消融；
不要继续针对 test gold 调规则。生产部署、业务库重处理和简历最终指标发布均尚未执行。

## 最终隔离实跑结果

原始报告（本地）：

- A：`backend/data/evaluation/parent_child/A_20260908T032154.json`
- B 第一轮诊断：`B_20260908T033207.json`
- B short-block 修正：`B_20260908T033739.json`
- B 页码修正及生成：`B_20260908T034414.json`

| 指标 | A flat 索引 | B Parent–Child |
| --- | ---: | ---: |
| 文档数 | 5 | 5 |
| Child/向量数 | 202 | 529 |
| Section / generation parent | 不适用 | 565 / 411 |
| 已映射开发题 | 13/13 | 13/13 |
| Hit@5 / Hit@20 | 1.000 / 1.000 | 1.000 / 1.000 |
| Evidence Group Coverage@5 / All Evidence@5 | 1.000 / 1.000 | 1.000 / 1.000 |
| MRR@10 | 0.923077 | 0.820513 |
| 候选 cosine distance 均值（非质量评分） | 0.271454 | 0.261734 |
| 候选 reranker score 均值（非质量评分） | -3.881511 | -4.611689 |
| context 保守预算单位均值 / 最大值 | 6190.6 / 7996 | 6651.2 / 8105 |

B 最大 parent 1394 embedding-token、最大 child 314；入库总计约199.4秒（含冷启动，非性能基准），
embedding 输入总计78344 tokens；header API请求为0，但 metadata enrichment 在生产 ingestion 中仍保留。
该实验复用已有 title/summary，仅重做原文 extraction、结构、child、embedding，不重复计元数据 LLM 成本。
A 旧 ingestion 耗时与费用没有同轮测量，不补造数据。context 数值是 UTF-8 byte 保守上界，不是服务商计费 token。

最终 child/vector snapshot：`4536114c917a2b46191bb02e3410805d0f420ca732886040e17e83ad7470909e`。
旧基线 snapshot 仍为 `b7e675ee0c8846172070f1448e7d71046f0888b6c82f33affe1477ad62b57993`。
后续 runner 增加 parent 独立快照及源代码摘要验证；本轮旧报告生成时尚未包含这两个新增字段，
不得补称本轮已经验证了 parent 快照稳定性。

### 生成审核发现（不是正式评分）

- DEV-AU02 这次答案包含通知邮箱与发送链接，较历史遗漏样本有改善，但单次样本不能证明稳定提升。
- DEV-TECH01 将“不要求水印”的例子写成“Do not watermark”，存在把豁免强化成禁止的风险。
- DEV-SG02 使用“access controls ... cannot be bypassed”这样的绝对化保证，不能由可靠性建议直接推出。
- 13题引用编号全部有效仅证明语法/范围检查通过，不证明每项说法被 Child 支持，也不代表 citation completeness。

发布前仍需完成：结构抽样人工验收、按既定 rubric 对13题逐项打分、必要的生成提示对照、
C成本收益实验（尚未执行）、更广问题覆盖和业务服务 smoke test。未调 evidence thresholds。
