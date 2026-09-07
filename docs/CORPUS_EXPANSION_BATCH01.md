# 首批扩容候选与历史来源核验

核验日期：2026-09-07。当前只做官方来源核验与候选暂存，没有导入数据库、生成向量或运行新检索。定向访问官方网页不是启用聊天 Web Search。

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
