# 13 道开发题生成基线 · 逐题送审

状态：助手初审完成，等待用户复核；不是用户已审核的正式准确率。

## 批次与边界

保留首批 3 道，新增后续 10 道，没有重复 API 调用。两个报告的模型配置、数据哈希、语料快照和检索报告哈希一致；执行代码仅增加分批选择，未改业务提示词、模型参数、gold 或检索结果。模型服务本身仍可能随时间变化，不能保证逐字可复现。

- backend/data/evaluation/generation_20260907T074355539627Z.json：3 道。
- backend/data/evaluation/generation_20260907T081211713093Z.json：10 道。

13 次均正常结束（finish_reason=stop），引用编号均存在且未越界；这不是语义正确率或引用支持率。总用量 35541 tokens。固定检索上下文生成，不覆盖 Agent 路由、工具调用、多轮状态或拒答能力。

## 优先审核

- DEV-AU02：明确遗漏操作内容。
- DEV-SG02：新增缺乏支持的 only 限制。
- DEV-TECH01：具体实施要求遗漏，同时需澄清评分范围。
- DEV-TECH02：扩展解释省略适用范围例外，先记录风险，不强行计错。

其余题初审未发现明显核心遗漏。所有结论仍是助手逐项核对，不将其包装成人工标注的正式指标。

## DEV-AU01

问题：How often must agencies review their AI transparency statements?

实际答案：

Agencies must review and update their AI transparency statements at the following junctures: at least once a year, when making a significant change to the agency’s approach to AI, and when any new factor materially impacts the existing statement’s accuracy [2][4].

参考答案：Agencies must review and update transparency statements at least annually, and earlier when their approach to AI changes significantly or a new factor materially affects the statement's accuracy.

初审：已覆盖年度复核和两项提前更新条件；上轮已核对引用 [2]/[4]。

审核人复核：待填写（通过 / 需修改 / 评分口径待明确）。

## DEV-AU02

问题：Who must agencies notify when publishing or changing an AI transparency statement, and how?

实际答案：

Agencies must notify the Digital Transformation Agency (DTA) when they publish or make any changes to their AI transparency statement by emailing ai@dta.gov.au [1][2]. This notification requirement applies both when the statement is first published and whenever it is subsequently updated [2].

参考答案：Agencies must send the DTA a link to the transparency statement by emailing ai@dta.gov.au when the statement is published or updated.

初审：完整性问题：遗漏发送声明链接。所引 [2] 已有该要求，属于生成遗漏。

审核人复核：待填写（通过 / 需修改 / 评分口径待明确）。

## DEV-AU03

问题：Within what period must agencies develop a strategic position on AI adoption?

实际答案：

Agencies must develop a strategic position on AI adoption within 6 months of the policy taking effect [1][2].

参考答案：Agencies must develop a strategic position on AI adoption within 6 months of the policy taking effect.

初审：已覆盖政策生效后 6 个月的期限；上轮已核对引用 [1]/[2]。

审核人复核：待填写（通过 / 需修改 / 评分口径待明确）。

## DEV-AU04

问题：How frequently must agencies share their AI use case register with the DTA?

实际答案：

Based on the selected documents, agencies must share their AI use case register with the DTA every 6 months, commencing from when they create the register [1][2].

参考答案：Agencies must share the register with the DTA every 6 months, commencing from when they create the register to meet the requirement.

初审：已覆盖每 6 个月分享，以及从登记册建立时开始的起算条件；[1]/[2] 支持。

审核人复核：待填写（通过 / 需修改 / 评分口径待明确）。

## DEV-AU05

问题：When must mandatory responsible AI training be implemented, and which staff does it cover?

实际答案：

Based on the selected documents, mandatory responsible AI training must be implemented within 12 months of the policy taking effect [1]. This training is required for **all staff**, regardless of their role [1][2]. The policy explicitly states that agencies must implement mandatory training for all staff on responsible AI use within this timeframe [1]. The training guidance further confirms that the requirement applies to all staff at all levels, as they will interact with AI and its outputs directly or indirectly [2].

参考答案：Agencies must implement mandatory responsible AI training for all staff within 12 months of the policy taking effect.

初审：已覆盖全体员工和政策生效后 12 个月；[1]/[2] 支持，答案存在重复表达但不是事实错误。

审核人复核：待填写（通过 / 需修改 / 评分口径待明确）。

## DEV-SG01

问题：Which protocols does the framework name for agent-to-tool and agent-to-agent communication?

实际答案：

The framework names the Model Context Protocol (MCP) for agent-to-tool communication and the Agent2Agent Protocol (A2A) for agent-to-agent communication [1][2]. It notes that this is a fast-developing space, with more protocols being developed to standardise agent interactions, especially in agentic commerce [1][2].

参考答案：The framework names Model Context Protocol (MCP) for agent-to-tool communication and Agent2Agent Protocol (A2A) for communication between agents.

初审：已正确区分 MCP（agent-to-tool）和 A2A（agent-to-agent）；补充的协议发展背景也见 [1]/[2]。

审核人复核：待填写（通过 / 需修改 / 评分口径待明确）。

## DEV-SG02

问题：Why should organisations prefer deterministic limits over prompt-only limits for agents?

实际答案：

Based on the selected framework, organisations should prefer deterministic, system-level limits over prompt-only (non-deterministic) limits for several key reasons:

- **Reliability and enforceability**: Deterministic limits are imposed through access controls that prevent the agent from calling certain tools at all, rather than relying on prompts to instruct the agent against accessing them [1]. This is more robust because prompt-layer safeguards can be bypassed or "forgotten" by the agent [2].

- **Consistency**: Prompt-layer safeguards tend to be inconsistently defined across users, whereas system-level safeguards can be consistently defined and enforced [4].

- **Preference for structural controls**: The framework explicitly advises implementing deterministic safeguards that operate at a system level through predefined logic, especially for higher-risk actions [4]. For example, if an agent needs to follow a set procedure, building that sequence into the workflow is more robust than prompting the agent to adhere to it through instructions alone [4].

- **Layering for residual risk**: Where limits are non-deterministic or less reliable, organisations should layer on more monitoring measures or incorporate human-in-the-loop review to catch any failures [1][3].

In summary, the framework recommends bounding risks "by design" through deterministic limits, with prompt-based measures used only as a supplementary layer where deterministic controls are less feasible [1][3].

参考答案：Deterministic limits bound behavior by design: access controls can prevent a prohibited tool call altogether instead of relying on the agent to obey a prompt. Where limits are non-deterministic or less reliable, the framework recommends additional monitoring or human-in-the-loop review to catch failures.

初审：核心要求已覆盖，但末句新增“prompt-based measures used only as a supplementary layer where deterministic controls are less feasible”，所引 [1]/[3] 没有确立这个 only 限制。应删去该强化结论或明确标为受限推断，不能冒充原文要求。其余关于一致性、结构性控制的解释可见 [2]/[4]。

审核人复核：待填写（通过 / 需修改 / 评分口径待明确）。

## DEV-SG03

问题：What three design patterns does the framework list for multi-agent systems?

实际答案：

Based on the framework, the three design patterns for multi-agent systems are [1]:

- **Sequential**: Agents work one after another in a linear or otherwise structured workflow (e.g., a graph), where each agent’s output becomes the next agent’s input.
- **Supervisor**: One supervising agent coordinates specialised agents under it, calling specific agents as tools when required.
- **Swarm**: Agents work at the same time, handing off to another agent when needed.

The framework notes that there is no universally correct architecture, and tasks may require different or hybrid patterns [1].

参考答案：The three patterns are Sequential (agents run in a structured workflow, passing outputs to the next agent), Supervisor (a supervising agent coordinates specialised agents and calls them as tools), and Swarm (agents work concurrently and hand off when needed). The framework does not prescribe one universally correct architecture; tasks may need hybrid patterns.

初审：三种模式、协作方式及不存在通用最优架构的例外均已覆盖，[1] 支持。列表共用前置引用，不宣称逐句引用格式完美。

审核人复核：待填写（通过 / 需修改 / 评分口径待明确）。

## DEV-TECH01

问题：When does Criterion 22 require watermarking, and what must it provide?

实际答案：

Based on the selected document excerpts, Criterion 22 requires watermarking only where AI-generated content may directly impact a user [1][3]. For example, generating a team logo with AI would not need to be watermarked [1][3].

The watermark must provide transparency and provenance, including authorship information [1][3].

参考答案：Criterion 22 requires visual watermarks and metadata on AI-generated media content that may directly impact a user, to provide transparency and provenance, including authorship. The standard gives a team logo generated with AI as an example that does not need watermarking.

初审：完整性待复核：触发条件、透明性/来源/作者和 logo 例外正确，但遗漏 visual watermarks and metadata 的具体实施要求，且将 media content 简化为 content。严格按当前 gold 不完整；问题文字偏向 when/purpose，应由审核人确认实施方式是否属于必答项，不为提高分数临时改口径。

审核人复核：待填写（通过 / 需修改 / 评分口径待明确）。

## DEV-TECH02

问题：Which version management practice is required under Statement 7?

实际答案：

Under Statement 7, the required version management practice is **Criterion 18: Apply version management practices to the end-to-end development lifecycle** [2][3]. This criterion mandates that agencies apply version control to the model, training and operation datasets, data in the AI system, training algorithm, and hyperparameters, while also maintaining design documentation and capturing approvals from accountable officials [4][5].

参考答案：Statement 7 requires version management across the AI system's end-to-end development lifecycle.

初审：核心回答正确。额外列举的版本管理对象见 [4]/[5]，但 [4] 同时包含 third-party software products 的排除条款，答案未带出。由于问题只问 practice，记录为扩展陈述的范围风险，暂不直接判为核心答案失败。

审核人复核：待填写（通过 / 需修改 / 评分口径待明确）。

## DEV-TR01

问题：According to the staff training guidance, how long does the AI fundamentals module take?

实际答案：

According to the staff training guidance, the AI fundamentals training module takes approximately 20 to 30 minutes to complete [1].

参考答案：The AI fundamentals module takes approximately 20 to 30 minutes.

初审：约 20–30 分钟，保留 approximately，[1] 支持。

审核人复核：待填写（通过 / 需修改 / 评分口径待明确）。

## DEV-TS01

问题：Does the transparency standard require agencies to list individual AI use cases publicly?

实际答案：

Based on the selected documents, the transparency standard does **not** require agencies to list individual AI use cases publicly [1]. The standard explicitly states that "Agencies are not required to list individual use cases or provide use case level detail" [1]. However, agencies "may choose to provide detail beyond the requirements to publicly explain their approach to AI" [1].

Instead, agencies must publish a transparency statement that provides a high-level overview of their AI use and management, including how AI is used and managed, a commitment to safe and responsible use, and compliance with the policy [1]. Additionally, agencies must list the applicable usage patterns and domains (e.g., decision making, analytics, workplace productivity, image processing) in their statements, but this is a classification of AI types, not individual use cases [2].

参考答案：No. Agencies are not required to list individual AI use cases or provide use-case-level detail, but they may voluntarily provide detail beyond the standard's requirements.

初审：已覆盖不强制公开个案、可自愿增加细节；附加的分类与概览说明也得到 [1]/[2] 支持。

审核人复核：待填写（通过 / 需修改 / 评分口径待明确）。

## DEV-TS02

问题：What two classification dimensions must agencies list in their AI transparency statements?

实际答案：

Based on the selected documents, agencies must list both the **usage patterns** and **domains** which apply to their use of AI in their transparency statements [1].

参考答案：Agencies must list both usage patterns and domains when classifying their AI use.

初审：usage patterns 与 domains 两项均正确，[1] 支持。

审核人复核：待填写（通过 / 需修改 / 评分口径待明确）。

## 下一步实验条件

完成本基线审核后，比较通用的“保留条件、例外与操作细节；不强化规范用语”约束。不得向生成模型传 gold，不写题号专用提示，不改基线答案。先固定评分口径与原始基线，再做开发集前后对照；独立测试指标另行设计。

