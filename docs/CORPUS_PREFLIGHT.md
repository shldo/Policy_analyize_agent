# 首批语料与环境验收记录

## 2026-09-06：真实模型与单文档链路验收

本节覆盖下方历史状态。配置已保存，仅检查密钥存在性，不记录密钥。Docker 数据库与后端健康。

- DeepSeek / deepseek-v4-flash 真实最小调用成功，回复 OK.，该调用用量 10 tokens（输入 8、输出 2）；不代表整个入库/问答总用量。
- 本地 BAAI/bge-small-en-v1.5 模型通过 Clash 代理下载后，实际生成 384 维向量。
- 使用应用 save_upload/process_document 服务导入 Australia_Responsible_AI_Government_v2.pdf，ID 为 2a37798a-ba31-474c-867a-daf75e90e8bd；SQL 核验状态 ready，共 17 个片段。未批量导入另外三份文件。
- 用英文问题询问 AI transparency statements 要求，应用检索返回 5 个片段，真实生成回答包含 [1] 引用，并指出具体字段需查阅另一个 Standard。仅验证服务层连通性，尚未人工逐条核验引用、浏览器上传/SSE 或聊天历史恢复。
- 首次检索时 rerank 开关开启，但 BAAI/bge-reranker-base 下载遇到 DNS 错误，实际回退到 dense 检索；这次问答不能作为 rerank 生效证据。随后通过代理补齐缓存，在未额外设置代理的新进程中重跑应用检索：5 个结果均有 reranker_score，页码依次 9、12、2、13、11，确认实际重排生效。此分数不是准确率，也不能证明质量提升。
- 本轮不是正式评测，无 Recall/MRR 或质量提升数据。英文单文档 smoke test 不代表中文适用性。搜索 API 仍未配置，Web Search 未验收。


日期：2026-09-05。当前状态为文件级初检，不是解析质量、问答效果或全文完整性的最终验收。

## 最新进展：Docker 恢复后

以下结果覆盖后文历史环境阻塞状态：db/backend healthy、web running。SQL 实查 documents=0、document_chunks=0、app_users=0；pgvector=0.5.1。运行时主模型、模型密钥和搜索密钥均未配置；Embedding 为 local/384 维。当前低维路径可先验证，halfvec 高维路径在版本升级前不启用。

### 现有测试

在现有后端容器临时安装 pytest 8.4.2 / pytest-asyncio 0.26.0，并复制现有 tests、scripts 与 pyproject.toml 执行：

```text
python -m pytest tests/test_chunker.py tests/test_pdf_extractor.py tests/test_document_service_reranking.py tests/test_agent_tools.py tests/test_chat_resume_router.py tests/test_web_search_provider.py -q --disable-warnings --tb=short
```

首次 45 passed / 2 failed，原因是 cl100k_base 分词器首次下载 DNS 失败。通过本机 Clash 代理下载分词器缓存后，同一命令重跑结果：47 passed in 2.75s。第二次 pytest 命令未新增代理变量，但依赖已下载缓存。该测试集合不是完整后端测试，也不是使用真实模型/搜索服务的端到端评测。测试依赖、复制文件及默认分词器缓存位于容器可写层，重建容器后需重新准备，尚未固化到镜像/CI。

### 应用实际 PDF 解析器检查

使用容器内 PdfExtractor.extract（包含清洗及 OCR），输出结果如下；与下方原始 pypdf 字符数不同是处理阶段不同，不能直接解释为内容丢失率。

| 文件简称 | 页数 | 清洗/OCR 后字符数 | 空文本页数 |
|---|---:|---:|---:|
| Australia | 22 | 26273 | 1 |
| China | 20 | 10773 | 1 |
| Singapore | 53 | 121751 | 1 |
| South Africa | 1 | 757 | 0 |

扫描样例已跑通 OCR，但南非文件仍只有一页，全文来源与完整性仍待核验。其他文件的空页需要与原文逐页核对；本结果不等于视觉质量验收。未执行应用上传、向量入库或调用付费模型。

下一步：用户在 localhost:8080/login 创建本地管理员并登录，在 /manage 配置 DeepSeek 和实际模型。搜索 API 暂缺；不将模拟 Provider 测试当作真实联网成功。

## 文件准备

四份 PDF 已从旧项目 Sprint3_PDFs 复制到新项目 backend/data/source_documents/，逐文件 SHA256 一致。该目录被 Git 忽略，尚未通过应用上传或入库。

| 文件 | 页数 | pypdf 提取字符数 | 少于20字符的页数 | 处理意见 |
|---|---:|---:|---:|---|
| Australia_Responsible_AI_Government_v2.pdf | 22 | 33419 | 0 | 英文链路候选，需逐页/引用抽查 |
| China_AI_Safety_Governance_Framework_2024.pdf | 20 | 11082 | 1 | 中文专项候选，需检查文本顺序及低文本页 |
| Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf | 53 | 128317 | 0 | 英文链路候选，首页标注 Version 1.5，需核验来源版本 |
| South_Africa_National_AI_Policy_OCR.pdf | 1 | 0 | 1 | 暂不作为完整政策全文；须视觉核验及 OCR，确认是否只是扫描样例 |

字符数仅表示文本可提取性，不表示内容正确。页数不能换算成问答指标。

## 环境阻塞

Docker Desktop 启动失败，日志指向 Inference manager 无法移除/监听本机通信文件：
`C:/Users/Lucifer/AppData/Local/Docker/run/dockerInference`。

本轮通过普通启动入口与 CLI 重试，Docker Linux API 仍不可用，WSL docker-desktop 显示 Stopped。因此未执行数据库升级、文档入库或容器测试。未重置 Docker、删除数据卷或修改系统配置。

## 模型信息

- 用户确认已有 DeepSeek API；未接收密钥，待在本地管理页面配置。
- 暂无 Tavily/Firecrawl API；真实 Web Search 验收待配置。
- 本地 settings.json 尚不存在；不可据此认定已有模型设置。
- 主机附带 Python 可运行 pypdf，但未安装 pytest，未向共享运行时安装项目依赖。

## 后续顺序

1. 处理 Docker Desktop 的本机启动错误，验证容器恢复。
2. 核对数据库与 pgvector 兼容版本，再决定升级方案。
3. 本地配置 DeepSeek，记录实际选用模型；密钥不写进文档或 Git。
4. 先用澳大利亚/新加坡文件验证英文文档处理，再处理中文/OCR 专项。
5. 完成应用入库、带引用问答与历史恢复后，再扩充评测集。
6. 搜索服务配置后单独验收联网工具，当前不记作通过。
