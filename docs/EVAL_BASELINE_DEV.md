# 首轮开发评测：运行成功，标签尚不完整

日期：2026-09-06。英文检索，不调用生成模型或 Web Search；不是独立测试集，不用于简历质量提升声明。

## 方法与复现

程序：`backend/scripts/evaluate_seed_corpus.py`。8 道人工编写的开发草案题，对应 3 份文件中的已知证据；检索池为全部 5 份公开批准文件、202 个有向量片段。

同题先取一次 dense Top 20，再用 BAAI/bge-reranker-base 重排同一集合。重排失败直接终止；验证候选成员不变。模型为 BAAI/bge-small-en-v1.5，当前 chunk token budget 480；已入库片段包含 contextual headers。保存实际文本、页范围、元数据和向量的联合哈希，运行前后核对不变；不将运行时设置误当成所有历史片段分块参数的证明。

```powershell
docker compose --env-file .env.local cp backend/scripts/evaluate_seed_corpus.py backend:/app/scripts/evaluate_seed_corpus.py
docker compose --env-file .env.local exec -T backend python -m scripts.evaluate_seed_corpus
```

输出在本地 `backend/data/evaluation/seed_20260906T045337663839Z.json`，不含密钥；包含每题排序、计时、模型、标签与语料哈希。后续运行使用独立时间戳文件，不覆盖原结果。计时包含首次加载，不作为稳定延迟基准。

语料哈希：`14e7d4be3302b97d166020b77ec16c459705dfe2d01f274f5a590587218fc1cf`。
题集哈希：`0d4824dc7d548b835498f7ad9697a39833587ec1567b022b0932b5bbca1c86b4`。

## 原始结果（只针对已标注片段）

| 指标 | Dense | Dense + rerank |
|---|---:|---:|
| 已标注证据 Hit@5 | 8/8 | 8/8 |
| 已标注证据 Hit@20 | 8/8 | 8/8 |
| 已标注证据 MRR@10 | 0.625 | 0.875 |

Hit 是是否命中任一已标注片段，不是完整相关片段 Recall。MRR 是前 10 名中第一个已标注片段排名倒数的均值，未命中记 0。

| 题号 | Dense 标签排名 | Rerank 标签排名 |
|---|---:|---:|
| AU01 | 3 | 1 |
| AU02 | 3 | 1 |
| AU03 | 2 | 2 |
| AU04 | 1 | 2 |
| AU05 | 1 | 1 |
| TR01 | 1 | 1 |
| TS01 | 2 | 1 |
| TS02 | 3 | 1 |

## 重要发现：AU04 的“退步”是标注遗漏

AU04 问每隔多久向 DTA 分享登记册。原标签只覆盖第 11–12 页片段；重排第一名为第 10–11 页片段，同样明确包含“every 6 months”及起算条件。原文复查说明第一名也是正确证据，因此不能据标签排名下降认定实际检索变差。

本轮保留原始标签和结果，不根据已看到的结果悄悄修改标签再声称模型变好。下一版需独立复核所有等价证据，版本化标签并在同一标签版本下重新比较两个排序。AU01/AU02 等题也可能跨配套标准出现重复证据。

## 验证与下一步

- 3 项指标单元测试通过：Top K 边界、未命中/空结果、非法重复 ID/空标签。
- 整轮真实 embedding、数据库检索和 rerank 执行完成，语料哈希前后一致。
- 仅开发验证；没有完整相关性标注、拒答题、独立测试集或答案生成评分。8 题主题集中且容易，不能外推为系统准确率。
- 优先补齐等价证据标注与原 PDF 页码，再扩充条件、例外和跨文档题；冻结开发/测试划分后再调参。不因这次分数决定更换模型。
