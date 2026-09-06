# 本地 RAG 首批评测题（开发集草案）

日期：2026-09-06。范围：仅本地 RAG，不调用 Web Search。

来源：Australia_Responsible_AI_Government_v2.pdf，SHA256：94BEDA4E6E9F61E0DD5D5F17B45B18CF6015B20FD9AABE41D20318F725273C11。
当前文档 ID：2a37798a-ba31-474c-867a-daf75e90e8bd。当前库只有该文档、17 个片段。

以下答案依据数据库已解析原文核对；页码是片段覆盖的 PDF 物理页范围，尚未逐页视觉确认，不等同于精确证据所在页。属于开发草案，待人工复核，不能作为独立测试集或简历指标依据。

| ID | Question | 参考答案要点 | 当前相关片段 ID / 页范围 |
|---|---|---|---|
| AU01 | How often must agencies review and update their AI transparency statements, and what triggers an earlier review? | 每年；AI 方法发生重大变化时提前更新。 | 20b225ff-f607-4607-9f95-593e2d430d12 / 9–10 |
| AU02 | Who must agencies notify when publishing or changing an AI transparency statement, and how? | 通知 DTA；通过 ai@dta.gov.au。 | 20b225ff-f607-4607-9f95-593e2d430d12 / 9–10 |
| AU03 | Within what period must agencies develop a strategic position on AI adoption? | 政策生效后 6 个月内；向员工传达战略立场。 | 20b225ff-f607-4607-9f95-593e2d430d12 / 9–10 |
| AU04 | How frequently must agencies share their AI use case register with the DTA? | 每 6 个月；从为满足要求而建立登记册时开始。 | 2658730a-006d-46ee-946c-fdc0a5ac6fc2 / 11–12 |
| AU05 | When must mandatory responsible AI training be implemented, and which staff does it cover? | 政策生效后 12 个月内；所有员工。 | 072b16bc-e451-4627-944e-82eefc48dd28 / 12–13 |

## 拒答候选题

“What exact monetary fine does this policy prescribe for failing to update a transparency statement?”

当前已检查片段没有罚款金额，但不能仅凭检索未命中标注为全文不可回答。需全文核验后再纳入拒答集。暂不计入检索指标分母。

## 标注和评测约束

1. 人工复核原 PDF 的原句、页码及所有等价相关片段；当前单个片段标签可能不穷尽相关集合。
2. 冻结语料清单、文件哈希、分块参数、embedding 模型和 contextual header 状态；重新分块后必须重新映射片段 ID。
3. 同一问题只取一次 dense 候选，分别比较原始排序与该候选集重排结果；直接调用重排器，失败须单独记录，不能将静默回退算作重排成功。
4. 记录候选 Recall@20、最终 Recall@5、MRR@10，明确截断和无命中规则；没有完整相关标签时先称作已标注证据 Hit@K，不冒充完整 Recall。
5. 当前只有 17 个片段，候选上限 20 会覆盖全库，Recall@20 在这里几乎没有筛选意义。扩大至多文档语料后再正式比较召回。
6. 这 5 题用于验证评测程序与发现问题；不能证明泛化能力。独立测试集应在调参前划分并冻结，避免同源近重复问题跨集合泄漏。
7. 后续扩充条件/例外、多证据、跨文档、拒答及中文问题。英文 bge-small-en 的单文档结果不能外推到中文。

## 本轮接口验证

- 经 Web 反向代理调用 POST /api/v1/chat/stream，Direct + analysis 模式；HTTP 200，text/event-stream。
- 问题为带 [smoke] 标记的 AU01 简化版；246 个 token 事件，收到 citations、answer_done、suggestions、done；没有 error 事件。
- 会话 ID：0b0049a9-fdc9-45ae-94dc-2a97abcb9489。GET /api/v1/chat/sessions/{id} 返回 200，两条消息均 complete，助手消息保留 5 条引用与 3 个建议。
- 未登录访问 GET /api/v1/chat/sessions 返回 401。测试令牌仅在内存生成，未记录或写入文件；本轮未测试密码登录或跨用户隔离。
- 5 条引用的 chunk_id 均存在，quote 均为相应片段的子串，page 均落在片段页范围内。这只是引用结构一致性，不代表所有回答主张得到证明。
- 核验核心答案“每年或重大变化时提前更新”与相关片段一致；未对全部建议进行逐项质量评分。
- 测试脚本最初误用 /sessions，返回 404；改为代码定义的 /chat/sessions 后验证通过。这是测试路径错误，不是应用缺陷。
- 未操作浏览器页面，本轮不能声称浏览器交互、引用点击跳转或刷新恢复已通过。

## 已发现的改进点

引用预览目前只截取片段开头 500 字符。AU01 的引用 [1] 预览主要是章节介绍，不包含年度更新要求，虽然该要求确实存在于完整片段中。后续应展示命中的证据句并准确定位页码，另加跨页片段的引用测试；本轮仅记录，不扩大到前端重构。
