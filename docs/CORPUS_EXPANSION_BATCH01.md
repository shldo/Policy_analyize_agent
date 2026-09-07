# 首批扩容候选与历史来源核验

核验日期：2026-09-07。最新状态：首批新增 5 份官方英文 PDF 已在隔离库完成入库，共 10 文档、389 片段和向量；未运行新质量排名。下文原候选记录保留，最新执行结果见第 5 节。定向访问官方网页不是启用聊天 Web Search。

## 1. 两份历史来源已完成字节核验

| 原有文件 | 官方下载 SHA256 | 结果 |
| --- | --- | --- |
| Australia_Responsible_AI_Government_v2.pdf | 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11 | 与冻结副本完全一致，22 页，Version 2.0 |
| Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf | 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba | 与冻结副本完全一致，53 页；封面 v1.5，Published 20 May 2026，Updated 5 June 2026 |

来源：[DTA 官方政策页](https://www.digital.gov.au/ai/ai-in-government-policy)、[DTA PDF](https://www.digital.gov.au/sites/default/files/documents/2025-12/Policy%20for%20the%20responsible%20use%20of%20AI%20in%20Government%202.0_0.pdf)、[IMDA 官方 PDF](https://www.imda.gov.sg/-/media/imda/files/about/emerging-tech-and-research/artificial-intelligence/mgf-for-agentic-ai.pdf)。

官方下载副本存于 `backend/data/source_verification_20260907/`。保持旧 manifest 的历史状态不变，本记录是后补的来源证据，下一语料版本再更新 provenance。字节一致不代表全文人工审核已完成，TEST-18/19 仍不因此变成 confirmed。

## 2. 五项候选及业务用途

下列用途是项目选材判断，不是来源对系统效果的承诺。当前先补澳洲执行层面的同主题材料；跨国泛化仍需后续独立选材。

| 候选 | 格式/本轮状态 | 业务用途与风险 |
| --- | --- | --- |
| [Standard for accountability](https://www.digital.gov.au/ai/ai-in-government-policy/accountability) | 9 页 PDF 已下载，Version 2.0 | 区分负责人、use case owner 和登记册责任；会与旧题产生等价证据，须重审标签 |
| [Agentic AI addendum](https://www.digital.gov.au/policy/ai/agentic-ai-addendum) | 32 页 PDF 已下载 | 补充具体 Agent 生命周期治理；需区分主标准与附录条款，避免混为强制通用规则 |
| [Agency guidance on public generative AI](https://www.digital.gov.au/policy/ai/agency-guidance-public-generative-ai) | 官方网页已查看，尚未保存正文快照 | 机构如何管理访问权限与信息处理；要保留机构语境 |
| [Staff guidance on public generative AI](https://www.digital.gov.au/policy/ai/staff-guidance-public-generative-ai) | 官方网页已查看，不能用简短海报替代完整页面 | 员工使用场景、核验输出与信息保护；与机构级要求区分 |
| [AI impact assessment tool guidance](https://www.digital.gov.au/ai/impact-assessment-tool/guidance) | 多页网页入口已核验，完整章节尚未采集 | 支持评估流程与具体章节任务；入口页不是完整指南，需明确章节集合 |

Agentic AI 附录官网说明它与主技术标准配套使用，技术名称示例不等于官方背书。不要将它与新加坡框架不加区分地合并成统一规定。[官方说明](https://www.digital.gov.au/policy/ai/agentic-ai-addendum)

## 3. 已暂存 PDF

目录：`backend/data/expansion_batch01/`，不随 Git 发布。

| 文件 | SHA256 | 初检 |
| --- | --- | --- |
| Australia_Accountability_v2.pdf | 7012f097344bbb45f6502748698321a47addb33ec3087bcf891b58d9ec014986 | 9 页，无空文本页 |
| Australia_Agentic_AI_Addendum.pdf | 7580f3dd27677a746a991139ba7e4812a77021ab06e7920839b7dca53f968a35 | 32 页，无空文本页 |

官方下载：[Accountability PDF](https://www.digital.gov.au/sites/default/files/documents/2025-12/Standard%20for%20accountability%202.0.pdf)、[Agentic addendum PDF](https://www.digital.gov.au/sites/default/files/documents/2026-06/Addendum-Agentic-AI.pdf)。

没有空文本页不代表解析完整，仍需表格、条款和跨页阅读顺序检查。版权与复用条件应在发布原文或派生材料前逐份核对，本轮不向 GitHub 发布 PDF。

两份新 PDF 的封面已渲染查看，标题与预期一致；未据此宣称全部正文和表格已经视觉审核。

## 4. 下一执行批次

1. 先对两份 PDF 做关键页面解析抽检，确定新开发问题的业务方向与证据。
2. 在隔离扩容库中导入，保留旧库及恢复验证备份；入库可能调用现有上下文生成模型，需记录用量。
3. 发布新的 corpus manifest，不能将五文档清单直接用于七文档数据库。
4. 原有题目回归前，审核新增文档是否提供等价答案或改变有效答案；不将未补标签的结果称为真实退步。
5. 网页型材料先解决正文快照、章节范围与定位格式，不人为转成无来源页码的 PDF 凑数量。

暂不新增测试排名、暂不改变 v4 默认运行版本；评分规则独立使用已批准的 generation-rubric-v1。

## 5. 首批 PDF 扩容执行结果

用户确认继续扩容后，采用 PDF 优先路线：保留责任分工标准、Agentic 附录；从影响评估工具官方入口找到完整指南 PDF，另外加入 APS AI Plan 2025 和 OECD 2024 研究。此前机构/员工网页候选延期，不用海报替代完整文件。

| 新文档 | 物理页 | 新片段/向量 | 业务覆盖 |
| --- | ---: | ---: | --- |
| Australia_Accountability_v2.pdf | 9 | 8 | 责任、登记册、高风险通知 |
| Australia_Agentic_AI_Addendum.pdf | 32 | 31 | Agent 生命周期、工具控制、交互评估 |
| Australia_AI_Impact_Assessment_Guidance.pdf | 48 | 71 | 固有/剩余风险、评估流程与审批角色 |
| Australia_APS_AI_Plan_2025.pdf | 30 | 32 | 实施计划、培训、采购及阶段目标 |
| OECD_Governing_with_AI_2024.pdf | 32 | 45 | 公共部门研究、政策挑战及国际案例；不是澳洲强制规则 |
| 合计新增 | 151 | 187 | 英文原文，中文复盘 |

新增来源：[影响评估工具及指南下载入口](https://www.digital.gov.au/ai/impact-assessment-tool)、[APS 计划下载入口](https://www.digital.gov.au/media/606)、[OECD 2024 出版页面](https://www.oecd.org/en/publications/governing-with-artificial-intelligence_26324bc2-en.html)。全部下载 URL、文件 SHA256 和版本说明保存在 `backend/evaluation/corpora/expansion-batch01.json`；该文件引用旧 manifest 组成十文档清单，不是可直接计分的新题集。

### 隔离与验收

- 新数据库容器：`policy-expansion-db-batch01`；专用网络 `policy-expansion-batch01`，卷 `policy-expansion-batch01-pgdata`，没有映射主机端口。随机密码保存在本地容器配置中，不提交 Git。
- 数据目录：`backend/data/expansion_runtime_batch01/`；原始下载另存 `backend/data/expansion_batch01/`。模型缓存共用，文档/配置/数据库独立。当前网页仍连接五文档业务库。
- 旧五文档的 202 片段/向量快照完全一致；业务库 27 张表与扩容前备份指纹一致。
- 十文档全部 ready，389 向量均完整，384 维，模型为 BAAI/bge-small-en-v1.5；389 片段均有上下文头。
- 原有 43 个文件证据锚点校验、29 道可回答题映射通过。这不代表扩容后的等价证据标签已补齐。
- 重复运行导入，五个文件全部 already_ready，无重复调用或写入。
- 47 项相关测试、Ruff 检查和 198 文件格式检查通过；不代表全应用端到端验收。
- 导入真实调用了现有 DeepSeek 元数据/上下文生成流程，但该流程未持久化 token 用量，本轮 `api_usage=null`，不得估算成实测消耗。

本地报告：`backend/data/expansion_runtime_batch01/evaluation/expansion_audit_20260907T124546346899Z.json`。
新快照 SHA256：`b8bdb5e51b9818a2346ad940d532e2e59ef86f2d7453309c45067bf812a6e984`。

### 解析范围与未完成验收

已视觉抽检新增文档封面/正文，以及 Agentic 附录物理第 6 页、影响评估指南第 6/12 页、APS 第 27 页表格和第 30 页封底；APS 表格的入库文本抽检保留了列内容的对应次序。未完成每页逐项人工比对。

解析器会清空目录页：责任标准第 3 页、Agentic 附录第 2 页、影响评估指南第 3 页。APS 第 30 页经视觉确认仅为装饰性封底。

**OECD 第 26–32 页在清洗后为空**：当前解析器在后段遇到 References 后跳过其余页面，因此除参考书目外也排除了后续尾注。原始 PDF 完整保存，但不能据此宣称数据库覆盖 PDF 全文。下一步必须检查尾注中的业务证据，并决定按新解析版本保留尾注；在完成前，不给涉及这些内容的问题设定拒答 gold。不得直接改变旧基线的清洗结果。

影响评估指南引用单独 assessment tool 中的风险矩阵；该工具的 DOCX 未包含在当前 PDF 语料中。OECD 文件文本层带有旧分类字样，物理第 2 页明确记载 2024-06-11 获准解密发布；按官方公开下载保存，不将文件上传 GitHub。原文再发布前仍需核对复用条款。

### 下一步验收门槛

1. 先解决/明确尾注及外部工具表格的索引范围，再发布可计分语料版本。
2. 复核旧题新增等价证据，区分原 gold 缺标与真实检索退步。
3. 开发题由 13 道扩至约 30–40 道；另建约 20–30 道独立测试候选，按业务意图/证据主题隔离。
4. 人工审核后运行新基线；未复核的拒答候选继续 unresolved，不冻结为 confirmed。

本轮达到“首批新增 5–10 份”的数量下限，不代表所有简历项目验收标准完成，也不代表回答质量提升。
