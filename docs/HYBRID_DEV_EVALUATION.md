# 开发集混合检索对照

## 实验约束（运行前固定）

- 仅使用 policy-v4 的 13 道 development 问题；不运行已观察的 test 排名，不改题目、gold 或语料。
- Dense top-20 与 BM25 top-20 等权 RRF 融合，截取 20 个候选后交给相同 BGE reranker；与 dense top-20 + reranker 比较。两个方案的重排候选上限相同，但混合方案多一次词法检索，不宣称成本相同。
- BM25 k1=1.2、b=0.75；RRF constant=60；不做网格搜索或逐题适配。
- 词法分析：NFKC、英文小写、ASCII 字母数字分词；不做 stemming/stopwords。Python 内存 BM25 仅是固定小语料参考实现，不等同 Elasticsearch/Lucene 的完整分析器或生产索引。
- 所有分支共用数据库中已批准公开文档的冻结快照；不加载未授权文档，也不写数据库。
- 报告分别保留 dense、rerank、bm25、hybrid、hybrid_rerank 五种结果及逐题排名。时间含冷启动且顺序执行，不作为性能对比。
- 优先看全部证据命中率@5 和证据组覆盖率@20，MRR@10 为辅助。开发集提升只能支持后续实验，不能直接作为新的独立测试结果。
- 如果混合方案没有改善或出现退步，保留生产检索配置并如实记录，不为技术栈完整而强行上线。

## 参数依据

[Elastic BM25 参数说明](https://www.elastic.co/guide/en/elasticsearch/reference/8.19/index-modules-similarity.html)给出 k1=1.2、b=0.75 默认值；[RRF 官方说明](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion)解释排名融合及默认常数 60。这些是本次实验起点，不代表本语料的最优参数。

## 复现

在 backend 环境运行 `python -m evaluation.run --run --split development --compare-hybrid --code-version <commit>`。执行器禁止在 test split 使用本实验开关。源文档位于 data/source_documents，需要已配置数据库和缓存的本地 embedding/reranker。

下一阶段：待本轮结果记录后，在固定检索配置下开展生成答案的完整性、引用支持性与证据不足行为评测；不把检索命中率称为回答准确率。
