# 可扩展政策评测 v1

## 本轮实际交付

- 版本化 JSONL 33 题：14 development / 19 test 候选；其中 29 题可回答、4 题不可回答候选。
- 原来的 13 题全部留在 development，已观察过的排序不能重新充当独立测试。
- 新测试候选覆盖适用范围、定义、事件处置、影响评估、Agent 权限、风险和案例、技术测试要求；含 2 题跨文档比较、3 题不可回答候选。
- 全部为助手编写或迁移，draft。无客户问题日志、独立人工审核或生产分布证明。
- 5 份语料哈希、38 个证据锚点及物理页已程序验证；29 道可回答题均解析到当前 202 个片段。
- 抽查原 PDF 页面：澳洲主政策 p6/p14，技术标准 p22，新加坡框架 p20。其余为文本核对，不能表述为全部页面视觉审核。
- 两份继承 PDF 尚未与官方字节核对；本次不改变其来源状态。
- 33 题是覆盖优先的第一批，不是先前讨论的 60 题承诺已完成。
- 本轮建立数据、标签和检索评测入口；生成质量、拒答率、Agent 任务成功率尚未执行。

## 文件与扩展契约

实跑记录（2026-09-06）：源码提交 5adde10；报告
backend/data/evaluation/benchmark_20260906T132336373288Z.json。
13 道历史可回答开发题完成 Dense/本地 rerank 对照，Hit@5 均 13/13，
MRR@10 分别为 0.8333/1.0000；开发拒答候选 DEV-NEG01 明确未评分。
语料快照前后相同；全部 19 道 test 候选未执行检索。
这次仅验收新入口和开发回归，没有产生独立测试集成绩。新旧题集的标签结构不同，
不能仅凭同分认定两套指标在所有情况下等价。12 项相关契约/指标测试通过，Ruff 通过。

源数据：backend/evaluation/datasets/policy-v1/manifest.json 和 questions.jsonl。
代码：backend/evaluation/dataset.py、run.py。
人工阅读版：docs/BENCHMARK_QUESTIONS_REVIEW.md。

每题有 question_id、split、category、language、corpus_version、answerable、reference_answer、
rationale、leakage_group、review_status、author、evidence_groups。
标记 reviewed 时必须补 reviewed_by；程序不自动给题目盖人工审核章。

每组证据代表一个必要答案要点；组内多个 alternatives 为等价证据。锚点使用文件 SHA256、
物理起止页和原文 quote。页码从 1 开始，与印刷页号可能不同。规范化仅处理 Unicode NFKC 与空白。
匹配不依赖 chunk UUID。哈希相同但片段 UUID 改变可以重映射；锚点被新切分断开时明确失败，
需要复核并用更短但仍具辨识力的原文锚点或多个必要证据组重新标注，不能模糊匹配后静默通过。

现有接口约定默认检索全部公开批准语料，因此运行前检查该集合与 manifest 精确一致。
新增文件会令旧版本在线运行失败，提示建立新版本；不自动把旧不可回答标签带入扩充语料。
本地文件夹中多余未入库 PDF 不自动进入评测池。

精确重复问题、重复 ID、同 leakage_group 跨集合、相同原文锚点跨集合会被程序拒绝。
语义改写和不同长度的重叠锚点仍需人工审核；自动检查不证明零泄漏。

## 评分口径

检索先调用现有 pgvector 全库入口得到 Dense Top 20，再用固定本地 BAAI/bge-reranker-base
重排同一候选集合。这是可控消融入口，不代表管理界面所选的任意 rerank provider。
调用失败直接失败；不回退或丢掉题目后生成看似完整的汇总。

- Hit@K：前 K 是否包含任一已标注必要证据组。
- evidence_group_coverage@K：已覆盖的必要证据组数 / 全部必要组数。
- all_evidence@K：是否覆盖全部必要证据组。
- MRR@10：第一个已标注证据排名倒数，未命中为 0。多证据是否找齐看前两项覆盖指标。
- 不把上述覆盖率称作穷尽相关片段 Recall；尚未穷尽标注所有相关片段。
- 不可回答候选不参与检索命中率分母，报告明确列出未评分 ID；不能从检索分数推出拒答率。
- 已看到新测试集结果后，不应再用它调参；若用于改进，后续需补新的保留测试集。
- 原开发题的 reference_answer 是迁移草稿，须扩写复核后才可用于生成质量评分。

报告保留题集哈希、包括实际文本与向量的语料快照哈希、模型/维度、候选数量、
代码提交号、逐题排序与时间。运行前后语料核对，检测变化则舍弃结果。
计时含冷启动，不能作为稳定 P95 延迟。失败运行以非零退出码报错；当前未提供失败历史数据库。

## 复现

从项目目录执行。不会调用 DeepSeek 或 Web Search；真实检索会使用已配置 embedding，
若未来切为收费 embedding，运行前需自行确认其配置。

~~~powershell
docker compose --env-file .env.local cp backend/evaluation backend:/app/evaluation
docker compose --env-file .env.local exec -T backend python -m evaluation.run --database
~~~

上面只做文件/数据库/标签核验，不查看测试排序。生成报告在 backend/data/evaluation，
不覆盖历史文件，Git 忽略原始语料与运行数据。

开发集探索性评测（先提交本轮代码，避免提交号与执行代码不一致）：

~~~powershell
$benchmarkCommit = git rev-parse HEAD
docker compose --env-file .env.local exec -T backend python -m evaluation.run --run --split development --allow-draft --code-version $benchmarkCommit
~~~

正式 test 执行需要选定 split 的标签全部 reviewed，命令使用 --run --split test，
不加 --allow-draft。显式允许草稿时报告会标记 exploratory，不能作为独立人工标注的最终性能结果。
本轮 test 仅核验锚点，保留首测机会。

纯契约 CI 只安装 pytest/pytest-asyncio 并执行 tests/test_benchmark_dataset.py；
无需数据库、PDF、模型或任何密钥。它验证评测实现，不能替代真实检索或回答质量测试。

## 后续语料扩充

1. 复制版本目录到新版本，更新 dataset_version/corpus_version 与文件清单；保留旧版本。
2. 重审受影响题目：新文档可能改变不可回答标签、适用时间和等价证据。
3. 重审开发/测试主题重叠；客户用于调试的问题进入开发集。
4. 对旧题+新语料和新题+新语料分别报告，按来源、主题与题型分组分析。
5. 要重跑旧题+旧语料，需要恢复独立数据库快照及文件副本；本工具不会自动保留数据库。
   数据备份尚未验收，不能声称已有完整一键历史恢复能力。

## 方法来源

- Ragas 场景化单跳/多跳生成：https://docs.ragas.io/en/stable/concepts/test_data_generation/rag/
- BEIR 语料、查询、相关性标签分离：https://github.com/beir-cellar/beir
- Microsoft 检索与生成分别评估：https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators
- SQuAD 2.0 相关但不可回答的问题：https://arxiv.org/abs/1806.03822

这些来源提供原则，不规定本项目题量和比例。本数据集是项目定制格式，不声称直接兼容 BEIR/Ragas 导入接口。
