# Chunk structure-v2 与 Dev50 执行记录

后续更新：新增37题真实生成现已完成；以下“尚未生成”为上一轮历史状态。
见 [Dev37实测](DEV37_EXPLORATORY_RESULTS.md)，已暴露上下文打包损失，不满足稳定扩容条件。

日期：2026-09-08。本轮只改本地工作树和专用恢复测试库；业务库、历史备份和旧数据集保持不变，未推送 GitHub。

## 已实现的规则修订

- 全文按字符权重确定主字体，联合字号、粗体比例、文本块、行号及页边位置判断标题。
- `1.` / `1)` 默认视为列表，只有独立排版证据才允许成为标题；含义务/完整陈述特征的编号行不当成标题。
- 小字号页底脚注不成为 Section；脚注文本保留。布局键统一空白，避免双空格导致脚注提示丢失。
- 同一 PDF block 内连续、同字号的标题行合并；新 Article/编号、正文陈述会阻断合并。
- 多页重复的页边文字不再产生 Parent，但不在该模块删除正文。
- 无编号子标题保持在最近的编号章节之下；Child 落在具体子节内时保留最具体 section path，Generation Parent 仍可为上层完整章节。
- Child overlap 仍局限同一个 Parent；不通过跨独立章节合并来降低 Parent 数。
- structure_version=2；旧文档需要 full reprocess，单纯 reembed 不会更新边界。

## 离线结构审计

五份 frozen PDF，`audit_20260908T044729.json`：

| PDF | Generation parents | Children |
|---|---:|---:|
| AU Responsible AI | 14 | 28 |
| AU Transparency | 2 | 7 |
| AU Staff Training | 8 | 8 |
| AU Technical Standard | 72 | 155 |
| SG Agentic Framework | 82 | 134 |
| 总计 | 178 | 332 |

上一轮 411 parents / 529 children。此处减少主要来自纠正错误边界，不等于检索质量必然提升。
Staff Training 的短章节仍各自成为 Parent；SG 仍有约 31.7% Parent 小于 100 tokens，需区分真实短段与表格/装饰标题。

## Dev50

独立新增 `backend/evaluation/datasets/policy-parent-child-dev50-v1`，旧 v4/v5 不变。
13 历史回归 + 10 multi-child + 8 cross-section + 7 exception + 6 modality + 6 无答案候选。
配额用于本项目风险覆盖，不是行业统一比例，也不是用户请求频率估计。

44 answerable / 6 unresolved_candidate。125 处原 PDF 锚点已验证；不等于参考答案语义审核通过。
新增 37 题仍 draft，6 道无答案题 reference=null，禁止进入正式拒答准确率计算。
`DEV50_REVIEW.md` 提供英文题、参考答案、证据组及 PDF 物理页码。

`evaluation.evidence_geometry` 用精确集合覆盖检查实际需要几个 Child/Parent，不拿标签冒充 multi-child 能力。
目前 43/44 可回答题映射到离线 Child；DEV2-MC05 的授权证据包含提取器造成的连字符空格差异，
原 PDF 锚点可验证，但严格 Child 映射失败。保留失败，不模糊匹配或删除难题来提高通过率。
9 道已映射 MC 题实际需要 2–4 个 Child；第 10 道待解决上述提取差异。
cross-section 是逻辑章节维度，不要求一定跨 Generation Parent。

## 验收与后续顺序

1. 270 项测试通过，5 项既有 embedding shim 测试跳过；Ruff lint/format 通过。新增列表、脚注、布局空白、多行标题、层级、路径、集合覆盖和 Dev50 状态保护回归。
2. 完成 13 题旧 Dev 新结构回归；不把旧题高分等同于 50 题已通过。
3. 解决 MC05 严格映射差异；抽检表格标题、跨 block 标题和扫描/OCR 文档。目前规则不是通用 PDF 语义解析器。
4. 审核 37 道新题，检查主体、动作、条件、期限/例外，以及 must/should/may/not required；6 道缺失题全文复核。
5. 运行审核后的扩大 Dev，逐阶段保存候选、重排、gate、Parent、token packing、答案/引用；重新观察分数分布，不先改阈值。
6. 语义审核确认没有新增例外遗漏、义务强化与引用错配后，再增加 5–10 份新政策 PDF。
7. 新语料单独冻结版本并建立新题；旧 Dev 衡量干扰退化，新题衡量覆盖增量，另建未见 holdout。

这轮没有新增政策 PDF，没有新一轮生成语义成绩，不能称整个 Parent–Child 已稳定验收。

## 本轮真实检索回归

同五文档、旧 13 道已审核 development 问题、candidate_k=30；阈值未调整。

| 实验 | Child/flat chunks | Parents | Hit@5 | All Evidence@5 | MRR@10 |
|---|---:|---:|---:|---:|---:|
| 历史 flat A | 202 | — | 1.0000 | 1.0000 | 0.9231 |
| 上一轮 B | 529 | 411 | 1.0000 | 1.0000 | 0.8205 |
| 本轮 structure-v2 B | 332 | 178 | 1.0000 | 1.0000 | 0.8974 |

本轮 Hit@20、Evidence Group Coverage@5 也为 1.0000；13 题 Child gate 全通过。
DEV-AU01/02 首个相关 Child 在第 3 位，其余 11 题在第 1 位。后续优先分析透明度题的近似候选竞争，
不要为 13 题单独写关键词特判。MRR 恢复但尚未超过 flat；这些数据也不能外推到 Dev50 或更多 PDF。

报告：`backend/data/evaluation/parent_child/B_20260908T045146.json`。
语料快照：`52aca085e534f74883e2f4ef3acd2cf2e5a65001205de05e07f093477aba1895`。
数据库为 443 sections / 178 generation parents / 332 children；embedding 输入共 72,990 tokens，
未调用 LLM contextual header。单次 ingestion 约 130.6 秒，包含启动等环境因素，不作生产性能提升结论。
历史 A 是旧 flat 索引上的相同评测 runner，不等于旧应用完整 generation 基线；本轮没有执行 generation。

## 复现入口

在 backend 目录和专用隔离环境运行：

```text
python -m evaluation.structure_audit
python -m evaluation.run --dataset evaluation/datasets/policy-parent-child-dev50-v1
python -m evaluation.evidence_geometry --dataset evaluation/datasets/policy-parent-child-dev50-v1 --audit <audit.json> --output <new-output.json>
python -m evaluation.parent_child --variant B --code-version <source-version>
python -m pytest -q
```

重建仅限隔离恢复库；额外使用 --rebuild 与 --expected-snapshot，并先保留原始备份。
报告存放 backend/data/evaluation；新输出不覆盖旧报告。

测试环境必须设置 DATABASE_URL 指向专用恢复库，并设置 PARENT_CHILD_DB_TEST=1。
一次遗漏数据库环境变量的运行出现 12 failed / 257 passed / 6 skipped；复核代表用例为默认 localhost:5432
连接拒绝。使用正确隔离数据库配置的完整运行结果为上列 270 passed / 5 skipped，不能把无数据库运行描述为通过。
