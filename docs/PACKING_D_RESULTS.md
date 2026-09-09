# D 打包配置实验结果

## 第二轮复测与默认配置切换（最新）

第二轮真实模型生成37/37完成：`backend/data/evaluation/packing_d/D_20260908T121955580773Z`。
复用同一批检索中间产物，语料快照未变；30道可映射草稿的最终完整证据仍为25/30（83.33%），
平均证据组覆盖仍为91%，相较旧配置12/30与53.94%的改善已复现。
生成累计250.53秒（约4.18分钟）。这是证据打包改善，不是回答正确率或检索提升。

按用户“提升后删去byte参数”的授权，代码默认改为6000 tokens / 8 parents / 每文档5 parents。
已移除生成token计数的UTF-8 byte回退及未使用的max_context_characters配置；历史报告和备份保留。
默认tokenizer路径为`data/tokenizers/deepseek-v4/tokenizer.json`，首次运行须执行
`python -m app.core.tokenizer_assets`，也支持`--archive`离线安装；校验固定SHA256，仅加载JSON。
缺失tokenizer明确报错，不静默回退bytes；更换生成模型时必须配置匹配的tokenizer。
完整工程回归277 passed / 5 skipped。未发布业务容器、未推送GitHub。
下一步仍为全量答案语义审核，特别是义务强度、额外建议及引用支持。

下文为首轮历史记录；其中“默认未切换”与byte回退说明已由本节替代。

## Docker恢复后补验

已恢复原隔离数据库与测试容器。完整工程回归276 passed / 5 skipped（既有跳过），
另以D环境变量运行token计量、Parent context及pipeline相关测试7 passed。
Ruff lint/format通过。未重新调用模型、未改业务默认、未发布或推送。
下方Docker关闭时的待办记录现已由本次验证补齐；剩余工作为答案语义审核与后续策略对照。

同一批新增37题，复用 Parent–Child 原运行已保存的30候选与重排结果，不重新检索、不重新入库。
来源：`backend/data/evaluation/exploratory/draft_20260908T045925676069Z`。
结果：`backend/data/evaluation/packing_d/D_20260908T053907916840Z`。

## 实际配置

独立进程环境设置：RAG_MAX_CONTEXT_TOKENS=6000、PARENT_CONTEXT_K=8、
MAX_PARENTS_PER_DOCUMENT=5、RAG_TOKENIZER_PATH 指向官方 V4 tokenizer.json。
业务默认仍为旧8192字节/4/3，没有自动发布D。

使用[DeepSeek官方token计量页面](https://api-docs.deepseek.com/quick_start/token_usage/)链接的
https://cdn.deepseek.com/api-docs/deepseek_v4_tokenizer.zip，仅加载tokenizer.json数据，不运行远端代码。
tokenizer.json SHA256：89085f12ef79460ac5f66d1119325ddfc694b4ab209d80bbd81d35f081dc9614。
按正文token数而非bytes打包；完整prompt另检查窗口和输出余量，API usage作为实际用量记录。
6000限制的是RAG上下文，不是含系统提示/问题的整个API输入。

未改变：Child gate、rerank、Parent排序、正文重复呈现、researcher提示词、DeepSeek模型和输出2048预留。
因此D是多个打包参数的组合实验，不能单独归因于max_blocks或tokenizer。

## 结果

37/37实际生成成功，37个finish_reason=stop，未发现越界引用编号；运行结束快照未变。
这不等于引用语义正确率100%。MC05仍严格映射失败，6个无答案候选仍不计正式分数。
以下共同分母30道answerable草稿：

| 指标 | 原PC：8192 bytes/4/3 | D：6000 tokens/8/5 |
|---|---:|---:|
| 最终全部证据保留 | 40%（12/30） | 83.33%（25/30） |
| 最终平均证据组覆盖 | 53.94% | 91% |
| 检索/重排 | 原结果 | 完全复用，不宣称提升 |

D最终全引用集按@20计算，不能只看前5引用：D @5全证据为80%，@10/@20为83.33%。
最终覆盖已达到本轮gate后可用证据的91%及25/30全证据，但剩余5题检索证据仍不齐。
不要用扩大上下文代替后续多方面检索优化。

## 实际回答抽查

- CS01补回所有员工12个月内培训，同时保留公开透明度与内部战略差异。
- CS02补回design阶段screening/documentation和material change后重新评估的要求。
- EX02补回内部流程整合全部provisions、等价或更高风险结果、随工具更新可修订等条件。
- CS02仍推断“immediate action”“before continuing deployment”等，不能视为完成语义验收。

未进行全量人工评分；仍需审核义务强度、扩展建议及引用支持，不报告回答正确率。

## 时间与用量

本轮生成累计261.77秒（约4.36分钟），原PC生成216.62秒（约3.61分钟），单次观测增加约21%。
本轮复用检索，未花原来的约271秒检索时间；非生产P95，无统计显著性结论。
RAG上下文平均4627.84、最大5952个离线token，全部低于6000。
API实际输入190061 tokens、输出30053 tokens。旧运行未保留API usage，不能给精确成本增长倍数。

## 交付与后续

新增可选rag_tokenizer_path（默认None保留byte基线）、replay_packing入口和token计量测试。
原默认配置与业务数据不改，未推送。Ruff通过；测试期间Docker随后关闭，
本轮新增测试的完整suite最终输出未能取回，不把此前273项通过当成本轮新增测试全部通过。
实际37题运行完整结果及快照已独立落盘，可在Docker恢复后补跑工程回归。
建议保留D为候选配置，下一步做全量答案语义审核与证据优先/去重打包对照，再决定发布。
