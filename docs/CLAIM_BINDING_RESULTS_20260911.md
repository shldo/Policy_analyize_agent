# Child 主张绑定、有限修订与全量验证

## 结论

工程接入完成，**不通过默认启用验收**。不能把本轮称为全量答案正确率或 faithfulness 已达标。默认保留 `RAG_CLAIM_BINDING_ENABLED=false`，检索仍为 `reranker_top_k + original`。隔离 UI 曾显式启用绑定及 P2；不代表默认配置发生改变。

## 实际实现

- `rag/claim_binding.py`：初稿按非空行生成稳定单元 ID；一个单元的所有子主张都须支持，才能保留。检查器只接收问题、初稿单元、实际 Child 标题/页码/正文，不接收 Parent、gold 或题目 ID。
- 一次模型检查，程序验证单元全集、引用号和 Child 原文片段。支持/部分支持/不支持/矛盾/有界证据缺口/非事实分别处理。准确匹配只能证明来源映射，不证明语义蕴含。
- 有限修订只删除不支持的单元或修改引用号，不让模型编写新的事实。不反复重试，不以检索覆盖完整作为答案质量证明。
- 单条绑定失败只删除该条，不吞掉其他已验证内容；全集缺失或最终没有正文仍须复核。
- Direct 同步、Direct SSE、Agent Document Analysis 共用实现。启用后缓冲初稿，审核完成才展示；Agent 流中过滤初稿和审核器内容，按 final_generation 更新发送最终答案。
- 不触碰 Open Discussion 的通用知识和 Web 分支；不声称此模式也有 Child-only 质量保证。
- 修订模式保守保留 `not_assessed`，不把删除后答案标记完整。代价包括额外一次模型调用、首字延迟、可能误删和审核失败。

## 运行与变量控制

使用 C 保存的同一批 50 题 question/context/citations，模型为 `deepseek/deepseek-v4-flash`；本轮没有重新检索、写冻结数据库、改题库或调整 evidence group。数据库 hash 没有重查，明确为 `not_checked`。

1. 8 题 smoke：8/8 有检查输出。
2. 全量：50/50 初稿生成，50 次绑定检查均保存原始响应（其中有解析/绑定失败）。生成与绑定共 100 次成功返回，无外层重试。
3. 修复单条失败导致整题失败的渲染逻辑后，离线重放同一批响应：**48/50 有修订答案**，不重新调用 API。EX01 原检查 JSON 截断；EX05 所有正文被过严判 partial，因此无可验证最终正文。
4. 对 48 份修订答案另行调用审核器，不将审核意见反馈给生成。48 次审核尝试、50 份逐题状态记录；不存在答案的两题单独登记。

### 第二次审核的真实结果

| 项目 | 数量 |
|---|---:|
| 结构校验通过的审核 | 43 |
| 主张 span 非原文，待复核 | 4 |
| 审核 JSON 错误 | 1 |
| 无修订答案可审核 | 2 |

43 份格式有效的模型意见为：36 pass_complete、5 pass_partial、2 needs_revision；267 条模型主张标签为 254 supported、6 not_verifiable、6 partial、1 contradicted。**这是模型候选统计，不是认证准确率；不能把 254/267 写成项目 faithfulness 成果。** 也不能把这里的 43 与历史 frozen evidence 分母 43 混为一谈，两者筛选原因不同。

审核脚本曾因无答案记录缺 verdict 在终端汇总时退出；并行任务已保存全部 50 份逐题记录。已修复该显示错误，公开汇总由逐题文件重建，没有重跑模型、覆盖旧目录或伪造完整索引。

## 指挥侧复核与已知误判

- UN02/UN05/UN06：先前具体错引内容在本轮最终答案中已删除；这是局部有效修复，不证明这三题所有语义都完美。
- EX05：原答案正确区分“不要求水印”与“禁止水印”。模型因末句措辞过严否定整个单元，属于误删；不能计为成功拒答。
- CS02：最终只剩表格中的输出项，筛查阶段、Appendix C、重大变化触发等被删，实用性退化。
- MC06：仍缺 Tier 1/2/3 完整规则。第二审核器把缺失 gold 要点当作引用 Child 中存在，进而把有界缺口判 contradicted；这不是可靠的事实矛盾标签。保留原记录并注明不同意该判断，不更改 gold。
- MO05：问题只比较 bias mitigation 与 test coverage，答案已回答 Required / Recommended。审核器要求额外 Criterion 92/94 属于参考答案范围过度扩张，不能直接计为回答错误。
- MC09：删除标题会丢失 Required/Recommended 语境，不能因逐条句子“有出处”就当作整体义务强度正确。
- MC10：Criterion 21 的 Child 未带完整推荐/强制层级，仅因出现条款就写 requires 有强化风险。两个模型一致通过不等于正确。
- CS07：仍没有补齐替代方案评估及 Statement 8 完整条件证据。生成修订不是召回修复，核心缺口仍在。
- 自动审核误判和未校准样本已如实保留。不存在全量人工签核，也不能宣称无人审核政策决策可用。

## PDF 与浏览器

最终工程验证：423 passed、6 skipped、1 warning；Ruff check、format check、compileall、git diff --check 通过；前端 build 通过，保留既有 bundle 大小提示。秘密模式扫描未发现命中，运行时 data 与 private 会话未纳入推送。

真实浏览器点击来源：文件端点 HTTP 200、`%PDF-` 文件签名、打开 URL 的 `#page=12` 均校验通过。文件 SHA256：`94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11`。

渲染并核对物理第 12、13 页：第 12 页是 Preparedness and operations，培训条款在第 13 页；引用本身为 12–13 页范围，跳到范围起点正确，但不代表已经实现逐主张精确页内高亮。

启用绑定的隔离 API 下，真实注册、登录、Direct、Agent 均执行；两个回答页面无 pageerror，未确认覆盖提示保留。截图、SSE、PDF 导航记录保存在本地 evaluation 目录；含 private 会话的目录不公开。

## 公开产物与复现

[逐题真实产物与汇总](results/claim_binding_20260911/summary.json)：50 份 JSON 包括问题、初稿、修订答案、Child 引用、绑定响应、第二次审核、输入和结果 hash。未包含设置、API 密钥、登录会话、PDF 原文件或数据库备份。

相关命令入口：

```text
python -m evaluation.claim_binding_run --source <C run> --output <new dir> --all --run
python -m evaluation.replay_claim_binding --source <C run> --run <binding run> --output <new dir>
python -m evaluation.review_saved_answers --source <C run> --recovery <replay dir> --output <new dir> --prefer-recovery --run
```

## 下一步边界

这轮不再追加模型试跑直到偶然成功。保持开关关闭作为实验能力交付。下一次先解决句内事实与缺口混合导致的误删、表格/标题依赖和义务强度绑定，再用保存响应离线验证；不要增加 Planner、改 benchmark 或放宽语义标准。

简历可以写：实现 Child 引用绑定校验、有限修订、SSE 审核前缓冲与 50 题可追溯评测。不能写“全量 faithfulness 达标”“修订后 50/50 正确”“召回提升”。历史 C 的 Complete@20=40/43、EGC=95.03876% 并非本轮新成绩。
