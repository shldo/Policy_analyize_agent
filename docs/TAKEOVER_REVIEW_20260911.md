# 接管复核与执行记录

本轮未提交、推送或部署。没有改题库、gold、模型、检索策略或冻结数据。状态：工程验证推进，语义收尾尚未通过。

## 已复核并修复

1. `generation._build_citation_instruction` 原先无条件按列表顺序编号，与显式非连续编号合同矛盾。现保留显式编号，仅旧无编号列表使用顺序编号；新增两条回归。
2. 生成提示中允许把无 Child 支持的 Parent 事实标为 synthesis 的措辞不安全，已删除该豁免，并强调来源归属与问题范围。两轮诊断证明这仍不足以保证语义正确，不计为已修复的质量成果。
3. UI 验收脚本支持独立输出目录，避免覆盖旧截图与会话产物。

## 环境复核

此前报告的环境阻塞不是全部成立：本机存在 Playwright、Edge、PDF 源文件、可用后端镜像及运行时 DeepSeek 配置。未输出密钥。

启动旧验收 API 后实际失败原因是隔离库缺 migration 020。已确认连接数据库为 `policy_ui_acceptance_20260910`，只在该隔离库应用 020，未在 `testdb` 应用迁移。启动 PostgreSQL 容器不等于已校验冻结快照；本轮仍不宣称数据库 hash unchanged。

已恢复本地 API :8000 / 前端 :5300，成功执行真实浏览器注册、登录、Direct 生成及历史重开。历史保留引用与未确认覆盖提示，截图和页面记录在 `backend/data/evaluation/ui_acceptance_final_20260911/`。该目录中的 private 文件含测试会话，不得提交或公开。

追加：Document Analysis Agent、Open Discussion 全库搜索和网络中断路径均完成真实浏览器操作。Analysis 未获取 Singapore 时保留澳洲部分回答；Open Discussion 展示 wider-library 来源与 Singapore 内容（保留 SSE）。断网显示 `Connection interrupted. Please retry.`。PDF 实际打开/页码定位及非连续编号的浏览器端注入用例尚未完成，因此不是全部 UI 路径验收通过。隔离服务保持运行，供继续验证。

## 真实验证

- Docker 既有测试容器、显式隔离数据库：415 passed、6 skipped、1 warning。
- 新引用编号回归所在文件：8 passed。
- Ruff check：通过；本轮修改 Python 文件已格式化。
- 两轮各 8 道 generation-only：各 8/8 生成成功，没有检索调用；没有运行正式全量 50 题。
- 第一轮：`backend/data/evaluation/closeout_final_fix_20260911/diagnostic_20260911T035832104570Z/`。
- 第二轮：`backend/data/evaluation/closeout_final_fix_round2_20260911/diagnostic_20260911T040114841269Z/`。
- 产物保存输入、消息 hash；脚本的历史 prompt_version 标签仍为 closeout-b-v1，不应依赖该标签区分本轮提示，以实际 messages_sha256 区分。

## 未通过项：不能隐藏

第二轮 UN02 仍将治理和事件处置要求引用到仅包含培训等内容的 Child [6]；UN05 再次把 Criterion 79 引用到不包含该完整要求的 Child [6]；UN06 仍需检查 Criterion 21 与 Child [2] 的错配。合法引用号并不能阻止 Parent 事实渗入。

因此不能宣称两轮提示修订修复了 faithfulness。不要重跑相同问题直到偶然成功，也不要用 gold、题目 ID 或人工替换答案修运行时。下一步应独立验证“逐主张证据绑定与有限修订”机制：输入仅问题、回答及已保留 Child；检查源归属、义务强度与条件，保留 supported 部分，删除/限定缺证据部分；不得以字符串匹配替代蕴含判断。该机制尚未实施，不属于已交付能力。

## 简历成果核对边界

| 可以描述的工程能力 | 必须附带的限制 |
|---|---|
| 结构感知 Parent–Child、Child 检索和引用、token 预算打包 | 不能说父子分块在全部指标优于 Flat |
| BM25 + 向量检索 + RRF + cross-encoder | 分阶段召回指标不等于回答准确率 |
| LangGraph 工具调用与 selected/full-corpus 分工 | 不等于默认启用并通过验收的 Controlled Planner |
| 有依据部分回答、状态持久化、显式引用编号 | 不能说所有引用语义正确 |
| 415 条自动化测试通过 | 不等于 415 个真实用户场景或政策决策安全认证 |

历史 C 检索结果 Complete@20=40/43、EGC=95.03876%、Complete@5=36/43 属于显式 P2 配置，不是本轮新成绩，也不是默认 original 的结果。没有新的全量 faithfulness 或答案准确率。Memory、Wiki、GraphRAG、LoRA、自进化不能列为已完成成果。
