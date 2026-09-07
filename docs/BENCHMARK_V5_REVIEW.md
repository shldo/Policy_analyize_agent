# v5 四题措辞修订

依据用户反馈，只修改四题；v4 数据及历史评测报告不变。v5 是待复核修订稿，默认评测仍固定 v4，避免旧生成报告的数据哈希失配。不重新运行测试或模型调用。

## TEST-07 参考答案

For existing AI use cases that have not yet been assessed, agencies must determine whether they are in scope of the policy and apply all relevant policy actions by 30 April 2027.

补齐主体、未评估的前提、确定是否在政策范围内、落实全部相关行动以及截止日期。原文锚点扩展为完整原句，不将所有 use cases 无条件表述为必须完成同一套 impact assessment。

## TEST-13 参考答案

Criterion 95 requires human verification of AI test design and implementation for correctness, consistency, and completeness.

同步补齐 action 与 required_answer_points；保留原有三项核验要求。

## TEST-18 题干

Does the Bank of Singapore Source of Wealth case report a measured percentage reduction in processing time? If so, what percentage does it report?

## TEST-19 题干

Does the MSD agentic AI governance case disclose which LLM model and version were used? If so, what does it disclose?

后两题不预设已报告量化收益，也不预设使用了特定 commercial LLM。两题仍为 unresolved_candidate、reference_answer=null；没有证据不能自动回答 No，仍应限定 provided corpus / available material。

## 审核与历史边界

TEST-07/13 的新答案为待复核措辞，原 v4 审核信息保存在 previous_review。其他题不变。v5 由已观察过的 v4 测试主题修订而来，不是新的未见测试集。

源文件哈希与 43 处原文锚点检查通过。代码测试覆盖仅四题变更、未决状态保留及修订稿不能直接作为正式测试运行。
