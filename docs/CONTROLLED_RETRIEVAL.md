# 受控Agentic Retrieval：首版工程接入

CONTROLLED_RETRIEVAL_ENABLED默认false。题库、PDF、向量库及证据阈值未改。
选定文档与全库检索共享controlled_retrieval.py，不复用此前一次性compound拆分策略。

## 已实现

- evidence planning：1–5项证据需求，只输入用户问题。
- 首轮原问题召回、原问题重排及既有Child阈值过滤。
- inspection逐项输出supported/partial/missing/conflicting、Child ID和逐字摘录、缺口查询。
- ID和摘录必须存在于提交的Child；格式错误回退首轮检索，不伪装成功。
- 最多一次补查轮、两条不同缺口查询；总计最多三次规划/检查模型调用。
- 新候选重算原问题distance并按原问题reranker gate筛选，不借子问题降门槛。
- coverage-aware fusion以证据组合而非固定每方面两条选择：优先首轮已支持证据，再补检查结果所需Child组合，最后填充原排名。
- 停止原因包括coverage_sufficient、selection_budget、round_limit、no_new_evidence、time_budget、inspection_or_retrieval_error。
- 90秒在调用之间检查，模型请求30秒超时、禁用重试；不是整个流程严格硬超时，数据库与本地模型调用仍可能超出。
- 模型输入最多14000离线tokens、单次输出1800 tokens，超过输入预算明确失败回退，不从正文中间切断。
- trace保留查询、各轮Child、检查结果、最终选择、模型usage，以及packing后未覆盖事项。

## 验证与尚未完成

本次完整工程测试285通过、5既有跳过；四项新测试覆盖缺口补查、首轮证据保留、伪造摘录拒绝、无新增停止及无效计划回退。
Ruff通过。未运行新策略50题模型回归，不报告质量提升，默认保持关闭。

当前inspection的逐字摘录校验不证明语义正确；coverage标记仍是模型判断。pack后缺口已记录，但尚未新增事实逐句引用验证器。
全量评测runner目前仍走旧的显式retrieve/rerank路径，必须先接入控制器并保存独立trace，不能只设置环境开关就声称已测试新策略。
需要补齐接口联调、trace空证据传播、deadline/原检索失败观测及复杂证据组合单测，然后运行冻结50题。
该版本是工程基础，不是最终验收完成，未部署业务容器、未推送GitHub。
