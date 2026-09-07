# 生成评测首轮检查与待审核材料

更新：已补齐全部 13 道开发题，原有 3 道未重跑。当前完整审核材料见 [13 道逐题送审](GENERATION_DEV_REVIEW.md)，下文保留首批历史记录。

## 范围

2026-09-07，使用 v4 开发集检索报告的 dense + reranker 前 5 个片段，固定题号顺序取 DEV-AU01～03。调用项目现有消息构建与模型客户端，policymaker / analysis，无历史对话、无 Web Search。不是全 Agent 端到端测试，也不是代表性抽样准确率。

原始报告：`backend/data/evaluation/generation_20260907T074355539627Z.json`。代码提交：`b117ef8c299ad374b7b9346b6e1aced7640be300`。

实际配置：deepseek/deepseek-v4-flash，temperature=0，max_tokens=1200，单请求超时 90 秒，不自动重试。3 次调用成功，finish_reason 均为 stop。供应商返回用量合计输入 7656 tokens、输出 140 tokens、总计 7796 tokens；不按未经确认的价格估算费用。

报告保存每题实际发出的消息、检索片段、答案与 token 用量。Gold answer 和审核要点保存在独立 review_only 字段，未发送给生成模型。语料快照在运行前后保持一致。

## 逐题初审（助手核对，待用户复核；不是自动语义评分）

| 题目 | 观察 | 依据 |
| --- | --- | --- |
| DEV-AU01 | 答案覆盖年度复核、AI approach 显著变化、新因素影响准确性三个条件 | 实际引用 [2]/[4] 的片段均包含这些条件 |
| DEV-AU02 | 答案部分完整：覆盖 DTA、邮箱、发布或更新，但遗漏“发送声明链接” | 实际上下文 [2] 明确要求发送链接，属于生成遗漏，不是检索缺失 |
| DEV-AU03 | 覆盖政策生效后 6 个月内制定 strategic position | 实际引用 [1]/[2] 均包含该要求 |

三个答案都有编号引用且编号未越界。这只是机械校验通过，不能叫“引用准确率 100%”。片段可能跨页，现有应用消息仅标注片段起始页；原始报告保留起止页，严格的精确页码引用仍需单独验证。

### DEV-AU02 实际输出

> Agencies must notify the Digital Transformation Agency (DTA) when they publish or make any changes to their AI transparency statement by emailing ai@dta.gov.au [1][2]. This notification requirement applies both when the statement is first published and whenever it is subsequently updated [2].

审核重点：通知邮箱和触发条件正确，但没有告诉用户邮件中需要发送声明链接。即使答案所有已表达的事实都有支持，任务要求仍可能没有回答完整。

## 人工审核规则

1. 完整性：按 reference_answer_checks 的主体、行动、条件/触发、期限/例外逐项检查；未被问题要求的维度不强行计入分母。
2. 证据支持：逐项核对答案中实质性事实是否得到提供片段支持；把“没有支持”与“与原文矛盾”区分开。
3. 引用支持：编号存在只是第一步，需确认该编号对应片段确实支持相邻陈述。跨页定位单独记录。
4. 证据不足：仅在语料或提供片段范围内表达不确定，不补数字；只有问题歧义影响检索目标才追问。
5. 审核状态：当前 semantic_scores=null，初审不能替代用户签核。TEST-18/19 不纳入拒答计分。

## 下一步

- 保留当前生成提示词，先补齐全部 13 道开发题的基线采集与同一规则审核；首轮 3 题不是独立测试分数。
- 完成基线后再比较通用的答案完整性约束，不能向模型提供 gold，也不能为 DEV-AU02 写专用规则。
- 独立测试题已经用于检索观察，后续生成结果应标注这一暴露历史；需要全新未见问题才能提出新的完整端到端独立测试结论。
- 混合检索仍保留为实验选项，本轮无收益，因此不替换应用主流程。

复现入口：`python -m evaluation.generation --retrieval-report <development-report> --run --limit 3 --code-version <commit>`。省略 --run 仅准备审核数据，不调用模型；原始资料默认保存在被 Git 忽略的 data/evaluation。
