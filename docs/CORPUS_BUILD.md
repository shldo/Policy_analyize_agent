# 英文政策语料入库与数据库复现

## 更新：首批隔离扩容（2026-09-07）

独立 `policy-expansion-db-batch01` 数据库已完成新增 5 PDF，总计 10 文档、389 片段/向量；业务库仍为 5/202，网页未切换。见 [扩容结果及解析限制](CORPUS_EXPANSION_BATCH01.md) 和 [下一步指导](PROJECT_EXPANSION_AND_EVALUATION_GUIDE.md)。新增 OECD 尾注存在清洗排除范围，结构验收不代表全文语义验收或评测冻结。

## 更新：来源与扩容准备（2026-09-07）

两份历史 PDF 已从官方重新下载并确认字节哈希完全一致，见 [核验与候选清单](CORPUS_EXPANSION_BATCH01.md)。两份新 PDF 仅暂存，没有改变五文档/202 片段基线。数据库隔离恢复验收已完成，见 [恢复记录](BASELINE_BACKUP_RESTORE.md)；下文的“待溯源/待备份验收”为历史状态。

## 本轮验收结果（2026-09-06）

5 份文件全部 ready，共 202 个片段、202 条向量，缺失向量数 0：原澳洲政策 17、透明度标准 5、员工培训指南 3、技术标准 109、新加坡 Agentic AI 框架 68。

新增脚本通过语法编译和实际入库验证；再次执行四份清单全部返回 already_ready，无重复处理。SQL 核对记录数与向量关联完整性。未运行完整后端测试集。

全库 smoke query `What information must an agency include in its AI transparency statement?` 返回五个带重排分数的结果：主政策第 9 页、透明度标准第 4/6/2 页、技术标准第 35 页。检索在新加坡导入过程中执行；不是冻结语料上的正式评测，也不代表答案质量或 Recall 达标。

下一步：复核 PDF 页码和表格提取、补齐旧项目文件的官方版本溯源、扩充多文档标注题，再冻结语料与配置执行基线对比。技术标准贡献 109/202 片段，后续应注意语料主题与长度分布偏斜。

## 范围

本轮使用定向官方 PDF 下载，不启用聊天 Web Search，不执行 OECD 全站爬取。语料包含政策、标准与实施指南，不能把所有文件都称作独立政策。

新项目路径：`D:\AIWorkspace\Projects\policy-research-agent`。
2026-09-06 首次独立根提交 `3473dc5` 已推送至 `https://github.com/shldo/Policy_analyize_agent`；未保留旧提交历史。密钥、运行时数据、模型缓存和课程 proposal.pdf 不随代码发布。

## 文件来源

原始文件放在 `backend/data/source_documents/`，Git 忽略。新增三个澳洲文件来自 DTA 官方下载链接；固定链接、文件名、SHA256 记录在 `backend/scripts/ingest_seed_corpus.py`，下载后须通过哈希校验再入库。

| 文件 | PDF 页数 | 来源/版本状态 |
|---|---:|---|
| Australia_Responsible_AI_Government_v2.pdf | 22 | 旧项目副本，已入库；官方字节匹配待补 |
| Australia_AI_Transparency_Standard_v2.pdf | 8 | DTA 官方 PDF，Version 2.0 |
| Australia_AI_Staff_Training_v2.pdf | 6 | DTA 官方 PDF，Version 2.0 |
| Australia_AI_Technical_Standard_2025.pdf | 102 | DTA 官方 PDF，封面 Version 1 |
| Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf | 53 | 旧项目副本，版本与官方下载字节匹配待补；不伪填来源 URL |

官方落地页：

- https://www.digital.gov.au/ai/ai-in-government-policy/standard-ai-transparency-statements
- https://www.digital.gov.au/ai/ai-in-government-policy/staff-training
- https://www.digital.gov.au/policy/ai/AI-technical-standard

下载来源不等同于法律适用性审核；PDF 提取成功也不等同于逐页表格、脚注与阅读顺序完整性审核。

## 现有数据库，不清空重建

沿用 Compose 的 PostgreSQL + pgvector，持久化卷为该 Compose 项目的 `pg_data`；主机仅绑定 `127.0.0.1:55432`。PDF 和模型缓存由 `backend/data` 本地挂载保存。

- `documents`：文件标识、SHA256、来源 URL、处理状态。
- 页面/元数据表：解析结果与模型生成的文档描述。
- `document_chunks`：分块文本与页范围。
- `chunk_embeddings`：当前 384 维模型的向量；其他模型可能有独立向量表。
- 聊天会话与消息表：历史记录、引用与建议。

当前 embedding 为 `BAAI/bge-small-en-v1.5`，rerank 为 `BAAI/bge-reranker-base`，生成模型为用户配置的 DeepSeek。入库使用既有上下文标题增强，需调用真实模型并产生费用，不是纯离线处理。尚未升级 pgvector；不启用不兼容的高维 halfvec 路径。

## 重跑与恢复

按 LOCAL_SETUP.md 启动服务并在本地配置密钥。准备清单中全部四份待导入文件（原始澳洲政策已经单独导入），确保哈希一致。新加坡旧项目文件不会从 GitHub 自动恢复，需保留本地备份。

```powershell
docker compose --env-file .env.local cp backend/scripts/ingest_seed_corpus.py backend:/app/scripts/ingest_seed_corpus.py
docker compose --env-file .env.local exec -T backend python -m scripts.ingest_seed_corpus
```

脚本先校验整批文件，再逐份调用应用上传与处理服务。已存在且 ready 的哈希跳过；存在但未完成的记录会停止并要求检查，避免自动重复调用或覆盖。脚本不会清空表、删除文件或覆盖已有 PDF。

不要执行 `docker compose down -v`；该操作会删除持久化数据。GitHub 代码备份不能替代 PostgreSQL 数据备份、PDF 备份及本地设置备份。数据库备份流程尚待单独验收。
