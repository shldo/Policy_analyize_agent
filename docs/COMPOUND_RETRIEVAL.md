# 复合问题证据覆盖：候选实现，未完成实测验收

## Docker恢复后全量实测：未通过（最新）

运行：`backend/data/evaluation/compound_regression/draft_20260908T143043911166Z`。
50/50真实生成成功；题库、语料和Parent快照与此前一致，结束语料未变。工程测试281 passed / 5 skipped。
25题保存非空子问题计划；其余25题包含单方面空计划或失败回退，当前日志不能精确区分其数量，不能称为25次失败。

共同30道新增可映射题：完整证据25/30，与旧D持平；平均组覆盖91%→88.78%。
CS07由1/3→0；MC04由2/3→1/3；其余28题此指标持平。旧13题全证据13/13。
全43道可映射题全证据38/43、组覆盖92.17%，不可与30题分母混比。
检索累计945.32秒、生成累计449.14秒；未检测到越界引用编号，不代表语义引用正确。

CS07确实找回Child `a95e23ad-4119-4562-b8c7-1867540dab4a`（Criterion24–26部分正文），
但仍遗漏alternatives assessment对应证据组。其回答还用引用[4]支持该Child未包含的Criterion22/23，
说明Parent上下文信息仍可能被错误归到Child引用；并将水印质量验证建议加强为must。
不能根据答案出现watermark就宣称修复通过，也不改gold来提升成绩。

结论：COMPOUND_RETRIEVAL_ENABLED继续默认false，不发布。下一步需要子问题非重复性验证、
方面内证据完整性与原始top结果保留策略，以及事实到Child的引用核验；固定两名额并不保证证据完整。
完整回答在运行目录answers_review.md。下文“Docker未启动”为此前历史记录，已由本节补验。

新增COMPOUND_RETRIEVAL_ENABLED，默认false。保持题库、gold、gate阈值及Child上限8不变。

启用后：

1. 配置中的生成模型只看用户问题，输出0或2–3个独立检索子问题，不读取答案或题号。严格校验JSON；错误回退原召回。
2. 每个方面召回Child，沿用原文档权限和范围。新增Child重新计算原问题向量距离，不使用子问题距离冒充原问题距离。
3. 原问题和子问题分别重排同一候选集合。每方面最多预留两条，剩余名额用原问题排序填充；按Child ID去重。
4. 原问题距离、原问题reranker score以及对应方面score均须通过既有阈值。保留原score供后续gate使用。
5. 共用已有Child gate、Parent resolver、证据优先packing与Child citation。

此时返回顺序是coverage-selected顺序，不再是单一score单调排序；分阶段报告中的reranked指标应解释为重排后选择顺序。不能把多query分数变化说成原模型本身提升。

新增query_aspects、retrieval_sources保存在候选中供debug。模型规划增加调用成本，子问题重排增加延迟；仍须全量测试验证子问题是否保留了实体、条件和范围，不能保证CS07一定改善。

## 本轮验证

2项本地单元测试通过：低全局排名的方面证据进入固定8条窗口；子问题不能绕过原query gate且重复Child不重复计数。Ruff通过。
Docker引擎未启动，数据库/模型/全量工程测试未执行。旧279项通过不视为本轮新增实现的回归成绩。

## 恢复后执行

在原隔离policy-parent-child-tests/testdb运行，以环境变量COMPOUND_RETRIEVAL_ENABLED=true开启，
CHILD_LEXICAL_CANDIDATE_K=0保持关键词候选关闭。使用evaluation.exploratory_parent_child的
--all-development --run，对原policy-parent-child-dev50-v1执行50题并保存新的独立output目录。
必须先跑完整pytest。比较同一30题分母与旧D、另报告历史13题；检查CS07/MC04以及所有退步题。
未验收前不发布，不修改原始模型结果，不新增题目特例。
