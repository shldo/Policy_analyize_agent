# 受控检索首轮结果：未通过验收

原轮次46题：`backend/data/evaluation/controlled_regression/draft_20260908T162313786987Z`。
Docker中断后仅补跑UN03–UN06：`backend/data/evaluation/controlled_regression_resume/draft_20260909T022756773282Z`。
合计50/50生成完成，保留两份运行，不覆盖原结果。补跑前校验题库、corpus、Parent及模型一致，结束快照检查见补跑report。
两轮代码hash不完全相同：中间增加校验失败观测和断点入口、修复进度分母；未调整阈值、题库或检索策略。

共同30道新增可映射题：完整证据25/30、平均覆盖91%，与旧D持平，无质量提升证据。
停止原因：18 coverage_sufficient、23 inspection_or_retrieval_error、1 no_new_evidence、8 round_limit。
11题实际发起定向补查。23题检查/检索错误不等于23题生成失败，它们回退到首轮结果。
MC06被检查器标记coverage_sufficient，但最终冻结证据组不完整；不能把模型自评作为准确率。

CS07仍未修复：补查被引导到司法判例/行政裁决，偏离原技术标准问题；最后检查失败回退，证据覆盖仍1/3。
独立诊断还确认检查器会改写quote，导致精确摘录校验拒绝。保持严格校验，不用模糊匹配制造通过。

工程测试287通过、5既有跳过；Ruff通过。CONTROLLED_RETRIEVAL_ENABLED继续默认false。
下一步应采用可验证的证据片段选择、缺口查询范围约束，并核验packing前后覆盖；本轮不宣称方向已工程验收。
评测runner新增--remaining-from，仅在新目录执行未完成题，原始已完成模型回答不覆盖。
