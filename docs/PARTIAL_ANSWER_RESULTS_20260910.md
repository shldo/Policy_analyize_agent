# 混合检索 + 部分回答策略：50 题结果

日期：2026-09-10。结论：工程行为已修改并通过回归；混合候选检索有效，但放宽 Gate 本身没有提高这批题的证据覆盖。当前主要损失发生在召回缺口、重排 Top-8 与 Parent 数量限制。

## 1. 实验口径

- 原 `policy-parent-child-dev50-v1` development 50 题；43 题有可评分 evidence groups。
- `DEV2-MC05` 无有效映射；`DEV2-UN01～06` 未完成正式无答案确认，7 题不进入检索指标分母。
- 原 5 份 PDF、332 个 Child、Parent 和向量快照未变，`corpus_unchanged=true`。
- Embedding：`BAAI/bge-small-en-v1.5`；reranker：`BAAI/bge-reranker-base`；生成：`deepseek/deepseek-v4-flash`。
- 每路候选 30；RRF 常数 60；reranker 后实际取 8 个 Child；context 6000 tokens；最多 8 Parents、每文档 5 Parents。
- 本轮是默认混合 Classic RAG，共享服务的评测，不是旧 V3/V5 Controlled Planner/Inspector 的全链路复跑。不能直接把它与旧版 38/43 归因对比。
- 每题只检索/重排一次，再将同一结果分别经旧严格 Gate 和新部分回答策略打包。旧策略只记录生成许可，不重复调用生成；新策略实际生成 50 题。

## 2. 分阶段检索指标

| 阶段 | Hit@5 | MRR@10 | Hit@20 | Evidence Group Coverage@5 | Evidence Group Coverage@20 | 完整证据@5 | 完整证据@20 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 纯向量通道 | 83.72% | 0.6398 | 100% | 74.92% | 91.05% | 28/43 | 37/43 |
| BM25 通道 | 95.35% | 0.8987 | 100% | 82.33% | 94.46% | 29/43 | 39/43 |
| RRF 融合 | 97.67% | 0.8043 | 100% | 88.26% | 97.36% | 35/43 | 41/43 |
| Reranker 排序 | 97.67% | 0.8864 | 100% | 89.50% | 98.14% | 36/43 | 42/43 |

定义：Hit 是至少命中一个必需证据组；EGC 是每题必需证据组覆盖比例后取宏平均；完整证据要求全部必需组命中。它们不是所有相关片段的 exhaustive Recall，也不是答案正确率。没有完整相关性标注，不补造 Precision/nDCG 数字。

这些是当前候选池中各通道的排名分数，并非分别启动三个不同配置的完整 RAG。RRF 相比单通道增加了候选并进行排名融合；reranker 在该联合候选池上排序。

## 3. Gate 与最终上下文对照

| 指标 | 旧严格 Gate | 新部分回答策略 |
|---|---:|---:|
| 允许进入生成 | 50/50 | 50/50 |
| 程序级整题拒答 | 0 | 0 |
| 最终上下文完整证据 | 40/43（93.02%） | 40/43（93.02%） |
| 最终上下文 Macro EGC | 94.26% | 94.26% |
| 平均上下文 tokens（43 题） | 4932.65 | 4989.14 |
| 实际生成 API 调用 | 未运行 | 50 次成功，0 错误 |

最终上下文只使用重排前 8 个 Child，因此不能把表中的 reranker Complete@20=42/43 当成模型实际拥有 42 题完整证据。最终 citation 顺序也不等同于 reranker 顺序。

这批默认 Classic RAG 中，旧相关性 Gate 本就没有阻断整题，所以新策略没有体现减少拒答的数量收益。行为差异由新增的部分覆盖/打包丢失/Inspector 错误等测试验证；不应把旧 Controlled 运行的拒答数量拿来填本表。

新模式下 50 题均为 `coverage_status=not_assessed`，因为没有运行完整性 Inspector。`generation_allowed=true` 不等于完整支持。没有错误的完整性认证，但也没有任何完整性认证，因此不能将这一点当作 false-sufficient 准确率改善。

## 4. 三个未完整覆盖的案例与定位

| 题目 | 最终 EGC | 本轮查到的实际损失位置 |
|---|---:|---|
| MC04 | 1/3 | 三个证据组分别在重排第 8、13、2 位；第 13 位在 Top-8 外；第 8 位虽然进入打包输入，却被每文档最多 5 Parents 限额排除。最终仅 3102 tokens，不能简单归因于 6000-token 窗口不足 |
| MC06 | 1/5 | Dayos 的四个分级证据组不在联合候选池中；Bank 证据组位于第一。属于初始召回缺口，放宽 Gate 或换后续打包不能补出未召回 Child |
| CS07 | 0/3 | BM25 和 RRF 前 10 已完整召回；reranker 把必需 Child 排到第 13、16 位，Top-8 将它们全部排除。不能归因于没有爬取水印原文 |

因此下一步的工程优先级应是：修复有用证据被重排/Top-8 丢弃，以及单文档 Parent 硬限额；MC06 单独检查实体/结构范围召回。不要再把主要精力放到更复杂的 Gate。

## 5. 答案检查的范围与限制

- 50 次生成均返回文本，50 题存在编号引用，编号越界为 0；这里只证明语法，不证明每条引用支持对应断言。
- MC06 的回答明确说明缺少 Dayos 具体分级，回答了已有证据支持的差异，没有由程序标记为完整。
- CS07 回答了部分一般设计/透明度内容并说明材料缺口，但缺少题目要求的确切条款证据；不能因为答案很长就判成功。
- 抽查还发现研究者固定报告模板使部分答案冗长，并主动列出用户没有询问的“证据缺口”。这是生成表达问题，后续可固定本轮上下文单独改 prompt，不必重建知识库。
- 未进行全部答案逐断言的人工语义验收，不报告“答案正确率 100%”或“无幻觉”。6 道 UN 题仍不是正式拒答 gold。

## 6. 工程验证与复现

- 全套测试：358 passed、6 skipped、1 条既有依赖弃用 warning。
- 原严格 Gate 测试在显式关闭部分回答策略的配置下保留；新增测试验证新的默认行为。
- 完成评测后仅对评测器闭包显式绑定 factory、统一少量文件换行格式，未改变评分函数、模型参数或被运行的业务逻辑；运行报告保留开始时的 source hash。
- 配置：`RAG_ALLOW_PARTIAL_ANSWERS=true`，旧进程重启后生效；设为 false 可回到旧严格路径。
- 本轮评测中的检索/重排/双路打包总耗时中位数约 10.88 秒，生成约 4.00 秒；不是部署并发环境的 p95。

结果目录：`backend/data/evaluation/hybrid_partial_answers/draft_20260910T021612893235Z/`。

- `report.json`：配置、dataset/corpus/Parent/source hash、全量完成状态。
- `paired_summary.json`：本报告指标的机器可读汇总。
- 每题 JSON：两路候选、RRF、重排、旧/新打包分数、新答案及引用语法。

复现：

```sh
# 配置正确数据库与已存在的生成 API；不上传新的文件。
python -m evaluation.exploratory_parent_child \
  --dataset evaluation/datasets/policy-parent-child-dev50-v1 \
  --output data/evaluation/hybrid_partial_answers \
  --all-development --compare-strict --run --api-timeout 90
python scripts/summarize_partial_answers.py <new-run-directory>
```

输出使用新时间目录，不覆盖旧运行。原数据集是开发集，长期参与过调优，本轮不能冒充独立 held-out 成绩。
