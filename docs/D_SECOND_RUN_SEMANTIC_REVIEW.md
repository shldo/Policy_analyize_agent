# D 第二轮：人工语义审核入口

## 用户审核回传

用户已回传[11题修订答案包](D_SECOND_RUN_USER_REVISIONS.md)，并确认审核与答案修订完成。
原始模型回答保持不变；以下“待审核”为此前送审状态，不表示用户尚未提交审核。
人工修订完成不等于链路自动修复：CS07仍待重新检索/打包Statement 8证据并生成独立引用产物。
尚未从本次修订计算全量答案正确率。

## 材料与范围

审核对象为本轮新增37题的真实模型回答，不包含旧13题。参考答案仍为草稿，所有题均待人工审核。
运行：D_20260908T121955580773Z；配置6000 tokens / 8 Parents / 每文档5 Parents。
本次只交付审核材料，不代表已经审核通过。

- [37题全文：英文题目、参考答案、实际回答、Child证据及页码](../backend/data/evaluation/packing_d/D_20260908T121955580773Z/answers_review.md)
- [本轮结果汇总](../backend/data/evaluation/packing_d/D_20260908T121955580773Z/summary.json)
- [原始50题送审说明](DEV50_REVIEW.md)
- [配置对照结果及限制](PACKING_D_RESULTS.md)

完整逐题JSON位于上述全文所在目录，文件名为题号.json；packed.context记录实际模型上下文，packed.citations记录Child证据。审核不能仅依赖参考答案，也不能把上下文中的其他Parent文字当成对应Child已经支持了引用。

## 原始PDF

本轮冻结语料对应以下五份PDF。目录内其他PDF不自动属于本轮评测范围。

- [澳洲政府负责任AI政策](../backend/data/source_documents/Australia_Responsible_AI_Government_v2.pdf)
- [澳洲AI透明度标准](../backend/data/source_documents/Australia_AI_Transparency_Standard_v2.pdf)
- [澳洲AI员工培训要求](../backend/data/source_documents/Australia_AI_Staff_Training_v2.pdf)
- [澳洲AI技术标准](../backend/data/source_documents/Australia_AI_Technical_Standard_2025.pdf)
- [新加坡Agentic AI治理框架](../backend/data/source_documents/Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf)

引用中的页码用于定位，核验时注意PDF物理页序与印刷页码可能不同。

## 怎么审核

每题先核对原文及参考答案，再逐条检查回答中的事实陈述。建议先看CS01、CS02、EX02、MC09，再完成全部题；这不是只抽查四题。

1. 事实：主体、动作、日期、适用范围是否正确。
2. 完整性：是否漏掉问题所问的条件、例外、期限。
3. 情态：must / should / may是否被错误加强或削弱。
4. 引用支持：对应编号的Child是否真正支持这句话。
5. 引用完整：重要政策结论是否都有支持证据。
6. 无依据扩展：是否把建议、推断或其他司法辖区做法说成政策要求。
7. 证据不足：清楚的问题缺少证据时，应限定为provided corpus不足，不应凭空补充或断言全世界不存在。

对发现的问题，回查逐题JSON的packed.context：原文有但未召回属于检索；召回但未装入属于打包；已经装入但答错属于生成；参考答案本身错误属于评测集问题。无法确定时标记待定位，不强行归因。

## 暂不正式计分的题

- DEV2-MC05：严格证据映射失败；仍审核答案，但须修复映射后才加入对应自动指标。
- DEV2-UN01～UN06：无答案候选。需完整冻结语料复核，不能把未检索到视为确认不存在。
- 其余30题也只是可映射草稿，不是已经人工批准的gold。

## 可复制的逐题批注模板

题号：

结论：待审核 / 通过 / 需修改 / 无法判定

参考答案是否需要修订：

| 回答原句或遗漏点 | 问题类型 | 原文依据（PDF、页码、短引文） | 建议修改 | 根因或待定位 |
|---|---|---|---|---|
| | | | | |

条件检查：主体 / action / condition-or-trigger / timeframe-or-exception。

你可以直接把题号与上述批注发回对话。不必改写整段答案；指出原句、错误和原文依据即可。没有问题的题可写“该题通过”，但不要将尚未检查的题批量标记通过。
