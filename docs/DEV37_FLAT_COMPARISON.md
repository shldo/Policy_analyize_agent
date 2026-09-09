# 新增 37 题：Flat 索引与 Parent–Child 对照

## 最终结果（2026-09-08）

Flat 37/37 实际生成完成，无 API 错误；两侧均确认各自语料/Parent 快照未变。
选题、数据集hash、模型和K的配对检查通过。共同计分分母为30题，排除两侧均映射失败的MC05，
以及6道 unresolved_candidate。没有把这些排除项伪装成成功，也没有自动批准草稿答案。

| 指标 | Flat | Parent–Child |
|---|---:|---:|
| ANN Hit@5 | 86.67% | 80.00% |
| ANN Evidence Group Coverage@5 | 71.56% | 67.39% |
| 重排 Hit@5 | 96.67% | 100.00% |
| 重排 MRR@10 | 0.8944 | 0.8928 |
| 重排 Evidence Group Coverage@5 | 90.61% | 91.00% |
| 重排 All Evidence@5 | 83.33%（25/30） | 83.33%（25/30） |
| 重排 All Evidence@20 | 93.33%（28/30） | 83.33%（25/30） |
| packed 至少一个证据组命中 | 86.67%（26/30） | 70.00%（21/30） |
| packed Evidence Group Coverage | 58.11% | 53.94% |
| packed 全证据保留 | 33.33%（10/30） | 40.00%（12/30） |

packed 指标按最终 Child 引用集计算，本轮@5/@10/@20相同；不等价于答案完整正确。
Parent–Child多2题全证据保留，但有更多题一个标注证据组也未保留，因此平均覆盖率更低，
两项指标并不矛盾。重排MRR差约0.0017不能解读为显著差异。

| 类别 | 题数 | Flat完整证据保留 | Parent–Child完整证据保留 |
|---|---:|---:|---:|
| multi-child | 9 | 1 | 1 |
| cross-section | 8 | 0 | 1 |
| exception | 7 | 6 | 5 |
| modality | 6 | 3 | 5 |

配对差异：Parent–Child在CS05、MO05、MO06多保留完整证据；Flat在EX03多保留完整证据。
以上都是证据指标，不是四题实际语义胜负计分。

结论：没有证明当前Parent–Child全面优于Flat，也没有理由只因这轮结果就推翻结构化架构。
优先修复两侧共有的上下文打包损失，再进行同题配对复测。当前不能宣称chunk升级带来回答正确率提升。
本轮未实现策略修复、未扩文档、未部署或推送GitHub。工程验证273项通过、5项既有跳过，Ruff通过。

## 对照定义

本次恢复历史 Flat 索引，不重新切块或 embedding。新建隔离数据库 `flat_dev37`，
与 `testdb`（Parent–Child）并存，不覆盖业务数据库或先前报告。
只应用 additive migration 019 以兼容查询，document_sections 为空，所有旧 chunk section_id 为 NULL。
NULL section 使用自身正文作为上下文，不展开额外 Parent。

Flat：5 文档、202 chunks，快照 `b7e675ee0c8846172070f1448e7d71046f0888b6c82f33affe1477ad62b57993`。
Parent–Child：相同五文档、332 Child，快照 `52aca085e534f74883e2f4ef3acd2cf2e5a65001205de05e07f093477aba1895`。

两组使用同一个 Dev50 文件中的新增37题、DeepSeek/deepseek-v4-flash、
BAAI/bge-small-en-v1.5 embedding、BAAI/bge-reranker-base、ANN 30、rerank 8、
distance floor/ceiling 设置不变（最大 cosine distance=0.7，reranker 最低=-7）。
打包预算8192保守字节上界、最多4个上下文块、每文档最多3个，生成预留2048。
同 researcher prompt、temperature=0，无历史对话、无 Web Search，模型不接收 gold。

重要限制：这是旧 Flat 索引在当前公共 gate/packer/generation 中的兼容对照，
不是旧应用的字符截断流程回放。Flat fallback 同样受 Parent/Child 重复呈现与预算限制。
因此不能把差异归因于单一 chunk 大小，也不能据此声称所有 Flat 实现优于所有 Parent–Child。
单次真实 API 生成即使 temperature=0 也不保证完全确定；未计算显著性或生产 P95。

## 评分方法

只在两侧都能映射的 answerable 题目上计算配对指标；某侧映射失败，不用不同分母比较。
无答案候选观察回答，但不计算未经全文确认的正式拒答分数。
Hit / Evidence Group Coverage / All Evidence 是原文锚点与 chunk ID 指标，非答案正确率。
packed 指标衡量保留为引用证据的 chunk 集，不等价于模型生成文本的语义完整性。
应同时查实际回答与引用，不单靠检索表格下结论。

## 原始产物

- Flat：`backend/data/evaluation/exploratory_flat/draft_20260908T051128153805Z/`。
- Parent–Child：`backend/data/evaluation/exploratory/draft_20260908T045925676069Z/`。
- 每题 JSON 保存候选、距离、重排、gate、上下文、实际回答、引用与锚点映射状态。
- `answers_review.md` 为各组实际答案/引用审阅稿。
- 配对程序 `evaluation.compare_exploratory` 校验选题、数据集hash、模型、K以及运行完整性。

本轮只运行对照、补充评测报告，不改检索或生成策略，不把 draft 自动改为 approved。

## 个案对照（定性审阅，不计为整体正确率）

- MC09：两侧都回答了水印，但都遗漏输出 explainability testing。不能由任一侧 Hit@5 高就判为答对。
- CS01：Parent–Child 主要回答公开透明度和内部战略，漏培训；Flat 主要回答培训，反而声称摘录不包含公开透明度义务。两侧均不完整。
- CS02：Flat 回答了 material change 后重新判断 scope 的明确触发；Parent–Child 把这部分说成仅推论。
  但 Flat 仍未完整覆盖初始设计阶段 screening/documentation，因此也不是完整正确答案。
- CS03：Flat 覆盖部分内部流程等价性条件，仍遗漏 high-risk 强制治理；Parent–Child 更偏向一般 scope 讨论。
- MC10：Flat 覆盖 logging tests，遗漏 commit hash 等细节；Parent–Child 覆盖 commit hash，但遗漏 logging tests。
  两侧还出现 recommended / required 在不同段落混杂的风险。

这些案例表明，同一配置下改变证据块边界会改变遗漏的内容；不能把任一侧的长答案当作完整答案。
