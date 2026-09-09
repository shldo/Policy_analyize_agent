# Parent–Child Dev50 送审稿

## 来源文件索引

页码均为 PDF 物理页，从 1 开始；以下 SHA256 对应每题证据。

- [Australia_Responsible_AI_Government_v2.pdf](../backend/data/source_documents/Australia_Responsible_AI_Government_v2.pdf) — 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11
- [Australia_AI_Transparency_Standard_v2.pdf](../backend/data/source_documents/Australia_AI_Transparency_Standard_v2.pdf) — bcd3a3cac366fce0d5b0f003ebaee7d66e5062020e204ed500d21d7ad1d99af1
- [Australia_AI_Staff_Training_v2.pdf](../backend/data/source_documents/Australia_AI_Staff_Training_v2.pdf) — 7d81ab99a6d9239613ddee0370d034772335b75a3199c2316d5f568080d637c7
- [Australia_AI_Technical_Standard_2025.pdf](../backend/data/source_documents/Australia_AI_Technical_Standard_2025.pdf) — fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24
- [Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf](../backend/data/source_documents/Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf) — 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba


状态：13 道历史已审核题 + 37 道新增待评审题。英文业务问题，中文审核说明。不是正式 test set，不将新增题自动标记通过。

## 配额与口径

| 主类别 | 数量 | 占比 |
|---|---:|---:|
| 历史回归 | 13 | 26% |
| multi-child | 10 | 20% |
| cross-section | 8 | 16% |
| exception | 7 | 14% |
| modality | 6 | 12% |
| 无答案候选 | 6 | 12% |

这是本项目覆盖配额，不是行业统一比例。类别为主标签，实际能力可能重叠。跨章节不一定跨 Generation Parent；大 Parent 可以覆盖多个真实子章节。证据组之间 AND，组内来源替代项 OR。

审核：确认业务真实性、主体/action/condition-or-trigger/timeframe-or-exception、情态词强度、页码与证据充分性。6 道无答案候选必须全文复核五份 frozen PDF 后才能标记 confirmed；检索未命中不能证明无答案。旧 test 已被讨论过的主题仅作历史回归，后续扩容需要另建未见 holdout。

## DEV-AU01 — legacy_lookup

- 状态：reviewed / answerable
- Question: How often must agencies review their AI transparency statements?
- Reference: Agencies must review and update transparency statements at least annually, and earlier when their approach to AI changes significantly or a new factor materially affects the statement's accuracy.

**g1：At least annual review and update**

- 来源 SHA256 bcd3a3cac366fce0d5b0f003ebaee7d66e5062020e204ed500d21d7ad1d99af1; PDF 物理页 4–4。原文：at least once a year

**g2：Significant change trigger**

- 来源 SHA256 bcd3a3cac366fce0d5b0f003ebaee7d66e5062020e204ed500d21d7ad1d99af1; PDF 物理页 4–4。原文：when making a significant change to the agency’s approach to AI

**g3：Material accuracy trigger**

- 来源 SHA256 bcd3a3cac366fce0d5b0f003ebaee7d66e5062020e204ed500d21d7ad1d99af1; PDF 物理页 4–4。原文：when any new factor materially impacts the existing statement’s accuracy.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV-AU02 — legacy_lookup

- 状态：reviewed / answerable
- Question: Who must agencies notify when publishing or changing an AI transparency statement, and how?
- Reference: Agencies must send the DTA a link to the transparency statement by emailing ai@dta.gov.au when the statement is published or updated.

**g1：Recipient, channel and triggering event**

- 来源 SHA256 bcd3a3cac366fce0d5b0f003ebaee7d66e5062020e204ed500d21d7ad1d99af1; PDF 物理页 5–5。原文：Agencies must send the DTA a link to the statement when it is published or updated by emailing ai@dta.gov.au.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV-AU03 — legacy_lookup

- 状态：reviewed / answerable
- Question: Within what period must agencies develop a strategic position on AI adoption?
- Reference: Agencies must develop a strategic position on AI adoption within 6 months of the policy taking effect.

**g1：Deadline and starting event**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 10–10。原文：develop a strategic position on AI adoption within 6 months of this policy taking effect.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV-AU04 — legacy_lookup

- 状态：reviewed / answerable
- Question: How frequently must agencies share their AI use case register with the DTA?
- Reference: Agencies must share the register with the DTA every 6 months, commencing from when they create the register to meet the requirement.

**g1：Frequency and commencement**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 11–11。原文：Agencies must share the register with the DTA every 6 months, commencing from when they create the register to meet the above requirement.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV-AU05 — legacy_lookup

- 状态：reviewed / answerable
- Question: When must mandatory responsible AI training be implemented, and which staff does it cover?
- Reference: Agencies must implement mandatory responsible AI training for all staff within 12 months of the policy taking effect.

**g1：All staff and implementation deadline**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 13–13。原文：Agencies must implement mandatory training for all staff on responsible AI use within 12 months of this policy taking effect.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV-TR01 — legacy_lookup

- 状态：reviewed / answerable
- Question: According to the staff training guidance, how long does the AI fundamentals module take?
- Reference: The AI fundamentals module takes approximately 20 to 30 minutes.

**g1：Known legacy answer anchor; completeness not adjudicated.**

- 来源 SHA256 7d81ab99a6d9239613ddee0370d034772335b75a3199c2316d5f568080d637c7; PDF 物理页 5–5。原文：20 to 30 minutes

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV-TS01 — legacy_lookup

- 状态：reviewed / answerable
- Question: Does the transparency standard require agencies to list individual AI use cases publicly?
- Reference: No. Agencies are not required to list individual AI use cases or provide use-case-level detail, but they may voluntarily provide detail beyond the standard's requirements.

**g1：Known legacy answer anchor; completeness not adjudicated.**

- 来源 SHA256 bcd3a3cac366fce0d5b0f003ebaee7d66e5062020e204ed500d21d7ad1d99af1; PDF 物理页 5–5。原文：not required to list individual use cases

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV-TS02 — legacy_lookup

- 状态：reviewed / answerable
- Question: What two classification dimensions must agencies list in their AI transparency statements?
- Reference: Agencies must list both usage patterns and domains when classifying their AI use.

**g1：Known legacy answer anchor; completeness not adjudicated.**

- 来源 SHA256 bcd3a3cac366fce0d5b0f003ebaee7d66e5062020e204ed500d21d7ad1d99af1; PDF 物理页 7–7。原文：both the usage patterns and domains

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV-TECH01 — legacy_lookup

- 状态：reviewed / answerable
- Question: When does Criterion 22 require watermarking, and what must it provide?
- Reference: Criterion 22 requires visual watermarks and metadata on AI-generated media content that may directly impact a user, to provide transparency and provenance, including authorship. The standard gives a team logo generated with AI as an example that does not need watermarking.

**g1：Watermarks, metadata and required purpose**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 43–43。原文：Apply visual watermarks and metadata to generated media content to provide transparency and provenance, including authorship.

**g2：Direct-user-impact applicability and example**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 43–43。原文：This will only apply where AI generated content may directly impact a user. For instance, using AI to generate a team logo would not need to be watermarked.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV-TECH02 — legacy_lookup

- 状态：reviewed / answerable
- Question: Which version management practice is required under Statement 7?
- Reference: Statement 7 requires version management across the AI system's end-to-end development lifecycle.

**g1：Known legacy answer anchor; completeness not adjudicated.**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 15–15。原文：end-to-end development lifecycle
- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 41–41。原文：end-to-end development lifecycle

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV-SG01 — legacy_lookup

- 状态：reviewed / answerable
- Question: Which protocols does the framework name for agent-to-tool and agent-to-agent communication?
- Reference: The framework names Model Context Protocol (MCP) for agent-to-tool communication and Agent2Agent Protocol (A2A) for communication between agents.

**g1：Agent-to-tool MCP**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 7–7。原文：the Model Context Protocol (MCP) has been developed for agents to communicate with tools

**g2：Agent-to-agent A2A**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 7–7。原文：the Agent2Agent Protocol (A2A) defines a standard for agents to communicate with each other.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV-SG02 — legacy_lookup

- 状态：reviewed / answerable
- Question: Why should organisations prefer deterministic limits over prompt-only limits for agents?
- Reference: Deterministic limits bound behavior by design: access controls can prevent a prohibited tool call altogether instead of relying on the agent to obey a prompt. Where limits are non-deterministic or less reliable, the framework recommends additional monitoring or human-in-the-loop review to catch failures.

**g1：Why enforced limits differ from instructions**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 19–19。原文：rather than relying on prompts to instruct the agent against accessing certain tools, impose access controls that prevent the tool from being called by the agent at all.

**g2：Additional safeguards for less reliable limits**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 19–19。原文：or less reliable, layer on more monitoring measures or incorporate human-in-the-loop review to catch any failures.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV-SG03 — legacy_lookup

- 状态：reviewed / answerable
- Question: What three design patterns does the framework list for multi-agent systems?
- Reference: The three patterns are Sequential (agents run in a structured workflow, passing outputs to the next agent), Supervisor (a supervising agent coordinates specialised agents and calls them as tools), and Swarm (agents work concurrently and hand off when needed). The framework does not prescribe one universally correct architecture; tasks may need hybrid patterns.

**g1：Sequential**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 8–8。原文：Sequential: Agents work one after another in a linear or otherwise structured workflow

**g2：Supervisor**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 8–8。原文：Supervisor: One supervising agent coordinates specialised agents under it

**g3：Swarm**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 8–8。原文：Swarm: Agents work at the same time, handing off to another agent when needed.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-MC01 — multi_child

- 状态：draft / answerable
- Question: What assessment and monitoring steps should an agency plan from designing a new in-scope AI use case through deployment and later material changes?
- Reference: Document the in-scope screening during design while developing requirements; commence the impact assessment at design, finalise it and apply agreed treatments before deployment; regularly monitor and evaluate the deployed use case and revalidate the assessment after a material change.

**g1：Document design-phase screening**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 14–14。原文：The assessment must be documented and take place during the design phase while developing requirements.

**g2：Finalise assessment and apply treatments before deployment**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 14–14。原文：Before the solution is deployed, agencies must finalise the assessment and apply any agreed risk treatments.

**g3：Revalidate for material changes**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 15–15。原文：when there is a material change in the use case scope, usage or operation.

**g4：Ongoing monitoring and evaluation**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 15–15。原文：regularly monitor and evaluate their use case

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-MC02 — multi_child

- 状态：draft / answerable
- Question: Which strategic-position, ownership/register, operational-practice and training deliverables are expected within six or twelve months under Australia's policy?
- Reference: The strategic position on AI adoption is due within six months. Within twelve months agencies must designate owners for in-scope use cases, create the internal register, establish an approach embedding responsible AI practices, and implement mandatory responsible-AI training for all staff.

**g1：Strategic position within six months**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 10–10。原文：develop a strategic position on AI adoption within 6 months

**g2：Accountable owners within twelve months**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 11–11。原文：designate an accountable use case owner for each in-scope AI use case within 12 months

**g3：Create register**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 11–11。原文：create a register of in-scope AI use cases

**g4：Operational approach within twelve months**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 12–12。原文：establish an approach to embed responsible AI practices within 12 months

**g5：Training all staff within twelve months**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 13–13。原文：mandatory training for all staff on responsible AI use within 12 months

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-MC03 — multi_child

- 状态：draft / answerable
- Question: What reporting pathways and follow-up processes must an agency provide for AI safety concerns and changes affecting a deployed in-scope use case?
- Reference: Provide staff and appropriate public pathways for AI safety concerns, including staff incident reporting; incident remediation must be overseen by an appropriate governance body or senior executive. Regularly monitor deployed in-scope cases and revalidate their impact assessment when scope, usage or operation changes materially.

**g1：Staff reporting pathway**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 12–12。原文：a pathway for staff to report AI safety concerns, including AI incidents.

**g2：Public reporting pathways**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 12–12。原文：pathways for the public to report AI safety concerns

**g3：Incident remediation oversight**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 12–12。原文：incident remediation must be overseen by an appropriate governance body or senior executive

**g4：Revalidate assessment**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 15–15。原文：re-validate the AI use case impact assessment

**g5：Material-change trigger**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 15–15。原文：when there is a material change in the use case scope, usage or operation.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-MC04 — multi_child

- 状态：draft / answerable
- Question: How should an organisation assess an agent that accesses sensitive customer data, has high autonomy, and is supplied by an external vendor?
- Reference: Assess impact from sensitive-data access, with increased risk where persistent memory stores it across sessions; assess likelihood from greater autonomy and unpredictability; consider how using an external provider limits visibility and control. These are risk factors, not an automatic prohibition.

**g1：Sensitive data and persistent memory**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 15–15。原文：the risk increases if the agent has persistent memory and can store sensitive data across sessions.

**g2：Autonomy increases unpredictability**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 16–16。原文：A higher level of autonomy can result in higher unpredictability

**g3：Vendor visibility and control limits**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 17–17。原文：to what extent their visibility and control over the agent is limited.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-MC05 — multi_child

- 状态：draft / answerable
- Question: What identity and authorisation controls does the Singapore framework suggest for an agent acting on behalf of an employee?
- Reference: Give the agent a unique cryptographically verifiable identity linked to an accountable supervisor, user or department; centrally issue and track identities and permissions; use scoped, time- or session-bound, non-transferable least-privilege permissions and explicit escalation. As a rule of thumb, the employee should not delegate permissions greater than their own; record delegations.

**g1：Unique verifiable identity**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 23–23。原文：cryptographically verifiable identity

**g2：Accountability linkage**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 23–23。原文：tied to a supervising agent, a human user, or an organisational department

**g3：Central identity management**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 23–23。原文：issued from and tracked by a centralised system.

**g4：Bounded authorisations**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 24–24。原文：time- or session-bound, non-transferable

**g5：Human permission ceiling**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 24–24。原文：the human user should not be able to set permissions for the agent greater than what the human user is himself authorised to do

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-MC06 — multi_child

- 状态：draft / answerable
- Question: How do the Dayos IT-support and Bank of Singapore wealth-analysis cases differ in the autonomy they allow, and what human checks remain?
- Reference: Dayos Tier 1 tickets are automated without a human engineer in the loop but receive biweekly audits; Tier 2 actions need engineer approval and Tier 3 actions are not performed by the agent. The bank's system provides decision support only, with final validation and approval by designated human reviewers, not autonomous credit, onboarding or risk decisions.

**g1：Dayos Tier 1 automation**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 18–18。原文：No human engineer is in the loop.

**g2：Dayos Tier 1 audits**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 18–18。原文：But with biweekly audits

**g3：Dayos Tier 2 approval**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 18–18。原文：Agent diagnoses but can only act with a human engineer’s approval.

**g4：Dayos Tier 3 exclusion**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 18–18。原文：Agent does not touch these.

**g5：Bank human validation and approval**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 20–20。原文：final validation and approval remain with designated human reviewers.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-MC07 — multi_child

- 状态：draft / answerable
- Question: How does MSD combine controls for high levels of agent autonomy with containment of third-party SaaS agents?
- Reference: MSD is implementing a programmatic runtime policy-enforcement layer at its AI gateway before enabling higher autonomy. Vendor-embedded SaaS agentic features are restricted by default to their own ecosystems to contain cross-platform residual risks while preserving approved-use-case benefits.

**g1：Runtime enforcement before higher autonomy**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 21–21。原文：A programmatic runtime policy enforcement layer is being implemented at the AI gateway before higher levels of autonomy are enabled.

**g2：Default third-party containment**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 22–22。原文：agentic features in SaaS tools are by default restricted to within their own ecosystems.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-MC08 — multi_child

- 状态：draft / answerable
- Question: What should an agency's test plan include to reduce testing bias and verify both test design and human control?
- Reference: Differentiate formal test data from development data and maintain tester/developer independence. Undertake human verification of test design and implementation for correctness, consistency and completeness, and perform controllability testing for human oversight and control and system-control requirements.

**g1：Separate formal and development data**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 83–83。原文：differentiating test data for formal testing from the data used during model development

**g2：Tester/developer independence**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 83–83。原文：providing testers and developers a degree of independence from each other

**g3：Human verification dimensions**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 85–85。原文：human verification of test design and implementation for correctness, consistency, and completeness.

**g4：Controllability testing**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 85–85。原文：Perform controllability testing to verify human oversight and control, and system control requirements.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-MC09 — multi_child

- 状态：draft / answerable
- Question: For user-impacting generated media, what transparency controls and output-testing checks should be addressed under the technical standard?
- Reference: Apply visual watermarks and metadata providing transparency, provenance and authorship where generated media may directly impact a user, with WCAG compatibility where relevant. Perform explainability/transparency testing so outputs are understandable for the target audience and the right information is available for the right user.

**g1：Watermarks and metadata**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 43–43。原文：Apply visual watermarks and metadata to generated media content

**g2：User-impact condition**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 43–43。原文：This will only apply where AI generated content may directly impact a user.

**g3：Accessibility condition**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 43–43。原文：WCAG compatible where relevant

**g4：Understandable outputs**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 85–85。原文：testing that AI outputs are understandable for the target audience

**g5：Appropriate information access**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 85–85。原文：testing that the right information is available for the right user.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-MC10 — multi_child

- 状态：draft / answerable
- Question: Which audit-log information should be recorded and what logging behaviour should be tested for an AI system?
- Reference: Record version-control information in audit logs, including a commit hash to identify control state and AI predictions and actions. Logging tests should verify warnings and errors and relevant system changes, including who made the change, timestamp and system version.

**g1：Commit-hash control state**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 43–43。原文：use of a commit hash to identify the control state of all elements

**g2：Predictions and actions**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 43–43。原文：recording AI predictions and actions taken

**g3：Warning/error logging tests**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 85–85。原文：system warnings and errors

**g4：Change attribution, time and version**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 85–85。原文：who made the change, timestamp, and system version.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-CS01 — cross_section

- 状态：draft / answerable
- Question: How should an agency distinguish public AI transparency obligations from staff-facing strategy and training deliverables?
- Reference: Publish an AI transparency statement and review/update it annually or earlier for significant AI-approach changes; communicate the strategic position to staff, with that position due within six months; implement mandatory responsible-AI training for all staff within twelve months.

**g1：Public statement**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 10–10。原文：make a publicly available statement outlining their approach to AI adoption and use

**g2：Staff strategy communication**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 10–10。原文：communicate their strategic position on AI to give staff clear direction

**g3：Six-month strategic position**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 10–10。原文：within 6 months of this policy taking effect

**g4：Twelve-month training**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 13–13。原文：mandatory training for all staff on responsible AI use within 12 months

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-CS02 — cross_section

- 状态：draft / answerable
- Question: What changes in the policy workflow between initially screening a new AI use case and revisiting a previously out-of-scope use case after a material change?
- Reference: Initially assess all new use cases against Appendix C, document screening during design while developing requirements. An adopted out-of-scope use case must be reassessed for becoming in-scope when scope, usage or operation changes materially; if in scope, applicable policy actions follow.

**g1：Initial scope screening**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 14–14。原文：assess all new AI use cases against the in-scope criteria (Appendix C)

**g2：Document screening**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 14–14。原文：The assessment must be documented

**g3：Reassess adopted out-of-scope case**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 16–16。原文：they must assess whether the use case becomes in-scope

**g4：Apply in-scope actions**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 16–16。原文：If a use case is in scope, agencies must follow any applicable actions

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-CS03 — cross_section

- 状态：draft / answerable
- Question: If an agency uses its own impact-assessment process and identifies a high inherent risk, what constraints and governance actions apply?
- Reference: The internal process must integrate all government-tool provisions, be consistent and deliver the same or higher inherent and residual risk outcome, and be revisable for tool updates. High inherent risk must be reported to the accountable official with reasons, mitigations and residual risks and governed by an appropriate designated board or senior executive.

**g1：Integrate all provisions**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 14–14。原文：an internal process that integrates all provisions of the impact assessment tool.

**g2：Same or higher risk outcomes**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 15–15。原文：the same (or a higher) risk outcome for inherent and residual risk.

**g3：Report high risk**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 16–16。原文：report the use case to the agency accountable official with the reasons

**g4：Governance oversight**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 16–16。原文：govern the use case through a designated board or a senior executive

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-CS04 — cross_section

- 状态：draft / answerable
- Question: How do least-privilege agent design and centrally managed agent identities complement each other in the Singapore framework?
- Reference: Least-privilege design limits tools and data to what an agent needs. Centrally issuing and tracking agent identities and permissions enables tracking deployed agents, identifying anomalies and removing unused identities; scoped permissions should include explicit escalation paths.

**g1：Minimum tools/data**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 19–19。原文：only the minimum tools and data access needed for it to complete its task.

**g2：Central management**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 23–23。原文：issued from and tracked by a centralised system.

**g3：Anomaly and lifecycle management**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 23–23。原文：identify any anomalies, and remove identities that are no longer required.

**g4：Explicit escalation**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 24–24。原文：with explicit escalation paths for elevated permissions.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-CS05 — cross_section

- 状态：draft / answerable
- Question: Why should a team assess external-system exposure before allowing vendor agents to act across enterprise platforms?
- Reference: External exposure can make agents more vulnerable to prompt injections and cyberattacks. The MSD case notes that cross-platform actions may not have been exhaustively tested despite each vendor's ecosystem testing; MSD therefore restricts SaaS agentic features to their own ecosystems by default. This is a case-specific containment strategy, not a universal ban.

**g1：External exposure threat**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 16–16。原文：more vulnerable to prompt injections and cyberattacks.

**g2：Cross-platform testing gap**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 22–22。原文：cross platform actions which may not have been exhaustively tested.

**g3：Case-specific containment**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 22–22。原文：by default restricted to within their own ecosystems.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-CS06 — cross_section

- 状态：draft / answerable
- Question: After deciding an agent use case has acceptable benefits and risks, what accountability arrangements should the deployer still establish?
- Reference: Assess risk against benefits rather than assuming every use case suits agents. Deploying organisations and overseeing humans remain accountable; establish clear responsibility chains across the value chain and lifecycle, meaningful approval checkpoints and audits of approval effectiveness, complemented by monitoring.

**g1：Risk-benefit assessment**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 15–15。原文：first identify and assess the risk against the benefits.

**g2：Continuing accountability**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 25–25。原文：remain accountable for the agents’ actions.

**g3：Responsibility chains**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 25–25。原文：establishing chains of accountability across the agent value chain and lifecycle

**g4：Audit human oversight**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 25–25。原文：auditing the effectiveness of human approvals

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-CS07 — cross_section

- 状态：draft / answerable
- Question: Before building an AI-generated-media service, what design-stage alternatives assessment and user-transparency provisions should an agency consider?
- Reference: The technical standard lists assessing AI and non-AI alternatives as required pre-work. For generated media that may directly affect a user, visual watermarks and metadata must provide transparency, provenance and authorship; this watermark condition should not be generalised to every internal artefact.

**g1：Assess alternatives**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 16–16。原文：Criterion 28: Assess AI and non-AI alternatives.

**g2：Watermark purpose**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 43–43。原文：provide transparency and provenance, including authorship.

**g3：Direct-impact condition**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 43–43。原文：This will only apply where AI generated content may directly impact a user.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-CS08 — cross_section

- 状态：draft / answerable
- Question: How do continuous-improvement model version control and logging tests work together in the technical standard?
- Reference: Perform model version control under the continuous-improvement requirements, and test logging of relevant system changes with who made the change, timestamp and system version. Version control and verifying audit-record completeness are related but distinct activities.

**g1：Model version control**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 21–21。原文：Criterion 90: Perform model version control.

**g2：Verify change logs**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 85–85。原文：relevant system changes with corresponding details of who made the change, timestamp, and system version.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-EX01 — exception

- 状态：draft / answerable
- Question: Must an agency build a brand-new AI use-case register, or can an existing register meet the policy requirement?
- Reference: An existing register may be reused. It must still meet the requirement to record in-scope use cases and accountable owners and capture the standard's minimum fields; additional fields may meet organisational needs. Reuse is permission, not an exemption from the register obligations.

**g1：Reuse allowed**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 11–11。原文：An existing register may be reused

**g2：Minimum fields still apply**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 11–11。原文：minimum fields agencies must capture in the use case register.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-EX02 — exception

- 状态：draft / answerable
- Question: Can an agency replace the government impact-assessment tool with an internal process without losing any required provisions?
- Reference: Yes, if the internal process integrates all tool provisions, is consistent, delivers the same or a higher inherent and residual risk outcome, and can be revised in response to tool updates.

**g1：All provisions**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 14–14。原文：an internal process that integrates all provisions of the impact assessment tool.

**g2：Consistency**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 15–15。原文：the internal process is consistent

**g3：Risk equivalence**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 15–15。原文：the same (or a higher) risk outcome for inherent and residual risk.

**g4：Update capability**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 15–15。原文：revise their internal process in response to any impact assessment tool updates.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-EX03 — exception

- 状态：draft / answerable
- Question: Does an out-of-scope AI assessment exempt an agency from privacy/security obligations and all future scope checks?
- Reference: No. Adoption of an out-of-scope case must still comply with relevant existing obligations such as privacy and security. An adopted case must be reassessed if its scope, usage or operation changes materially.

**g1：Existing obligations remain**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 16–16。原文：while ensuring they comply with relevant existing obligations, such as privacy and security.

**g2：Future reassessment trigger**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 16–16。原文：if there is a material change in the scope, usage or operation of the solution.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-EX04 — exception

- 状态：draft / answerable
- Question: For a general-purpose AI solution with several uses, does the Australian policy require treating every use separately?
- Reference: No. Agencies may treat the solution as one complex use case and apply actions for the highest risk, or treat uses separately with actions proportionate to each risk, including separate owners and registration of each in-scope case.

**g1：Single complex-use option**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 19–19。原文：treat the AI solution as a single complex use case

**g2：Highest-risk rule**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 19–19。原文：appropriate for the highest level of risk

**g3：Separate-use option**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 19–19。原文：treat each use case separately

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-EX05 — exception

- 状态：draft / answerable
- Question: If an internal team logo does not directly impact users, does Criterion 22 prohibit adding a watermark?
- Reference: No prohibition is stated in the cited provision. It says user-impacting AI-generated content is covered and gives a team logo as an example that would not need watermarking. Not required must not be rewritten as forbidden.

**g1：Scope condition**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 43–43。原文：This will only apply where AI generated content may directly impact a user.

**g2：Not required, not forbidden**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 43–43。原文：using AI to generate a team logo would not need to be watermarked.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-EX06 — exception

- 状态：draft / answerable
- Question: Does the technical standard's discussion of C2PA amount to instructions that agencies must implement that standard?
- Reference: No. It describes C2PA's work on content provenance but expressly places advice on using C2PA outside the scope of this standard; it does not establish that implementation requirement.

**g1：C2PA advice out of scope**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 43–43。原文：Advice on the use of C2PA is out of scope for the standard.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-EX07 — exception

- 状态：draft / answerable
- Question: In the Dayos case, does having no human engineer in the Tier 1 execution loop mean there is no human oversight at all?
- Reference: No. Tier 1 is automated without a human engineer in the loop, but a designated reviewer audits a cross-section of actions biweekly; the case describes these actions as reversible.

**g1：No engineer in execution loop**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 18–18。原文：No human engineer is in the loop.

**g2：Reviewer audits**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 18–18。原文：A designated reviewer audits a cross- section of these biweekly.

**g3：Reversibility condition**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 18–18。原文：every Tier 1 action is reversible

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-MO01 — modality

- 状态：draft / answerable
- Question: Are mandatory staff training and applying the AI technical standard expressed with the same obligation strength in the responsible-AI policy?
- Reference: No. The policy says agencies must implement mandatory responsible-AI training for all staff within twelve months. Applying the AI technical standard is strongly recommended; the policy does not express the two with identical force.

**g1：Mandatory staff training**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 13–13。原文：Agencies must implement mandatory training for all staff

**g2：Strong recommendation for standard**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 13–13。原文：It is strongly recommended that agencies apply the AI technical standard

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-MO02 — modality

- 状态：draft / answerable
- Question: Does the policy impose the same board-or-senior-executive governance obligation on medium- and high-inherent-risk use cases?
- Reference: No. For medium inherent risk agencies should consider whether additional board or senior-executive governance would help. For high inherent risk they must govern through a designated board or senior executive appropriate to agency size and scope.

**g1：Medium-risk consideration**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 15–15。原文：they should consider if the use case would benefit

**g2：High-risk requirement**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 16–16。原文：govern the use case through a designated board or a senior executive

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-MO03 — modality

- 状态：draft / answerable
- Question: Do the policy's implementation deadlines mean agencies must wait until those deadlines to act?
- Reference: No. Agencies should implement requirements sooner if practicable and may consider interim processes while building their approach toward the deadline. This guidance is not a new mandatory earlier date.

**g1：Earlier where practicable**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 7–7。原文：agencies should implement them sooner if practicable.

**g2：Interim-process option**

- 来源 SHA256 94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11; PDF 物理页 7–7。原文：putting in place interim processes

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-MO04 — modality

- 状态：draft / answerable
- Question: Does Statement 8 give hidden-watermark tooling and watermark-risk assessment the same required status as visual watermarks and metadata?
- Reference: No. Its required criteria include visual watermarks and metadata, with scope qualifications in the detailed text. Hidden-watermark tooling based on use case/content risk and assessment of watermarking risks/limitations are listed as recommended.

**g1：Required visual watermark/metadata criterion**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 16–16。原文：Criterion 22: Apply visual watermarks and metadata

**g2：Recommended tier**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 16–16。原文：Recommended

**g3：Recommended hidden-watermark tooling**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 16–16。原文：Criterion 25: For hidden watermarks, use watermarking tools based on the use case and content risk.

**g4：Recommended risk/limitation assessment**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 16–16。原文：Criterion 26: Assess watermarking risks and limitations.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-MO05 — modality

- 状态：draft / answerable
- Question: In Statement 26, are defining test coverage and mitigating testing bias both labelled required?
- Reference: No. Mitigating bias and defining test-criteria approaches are required; defining how coverage will be measured and a test-adequacy strategy are recommended.

**g1：Required bias mitigation**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 21–21。原文：Criterion 91: Mitigate bias in the testing process.

**g2：Required test criteria**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 21–21。原文：Criterion 92: Define test criteria approaches.

**g3：Recommended coverage**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 21–21。原文：Criterion 93: Define how test coverage will be measured.

**g4：Recommended adequacy**

- 来源 SHA256 fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24; PDF 物理页 21–21。原文：Criterion 94: Define a strategy to ensure test adequacy.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-MO06 — modality

- 状态：draft / answerable
- Question: Does preferring deterministic agent limits mean the Singapore framework guarantees that all residual risk can be eliminated?
- Reference: No. It prefers deterministic limits and bounding risk by design; it also says some residual risk always remains and organisations should decide whether that risk is tolerable and acceptable. It does not establish a zero-risk guarantee.

**g1：Preference for deterministic limits**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 19–19。原文：prefer deterministic rather than non-deterministic limits

**g2：Residual risk remains**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 24–24。原文：there will always be a level of risk remaining

**g3：Evaluate risk tolerance**

- 来源 SHA256 2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba; PDF 物理页 24–24。原文：is of a tolerable level and can be accepted.

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-UN01 — unanswerable_candidate

- 状态：draft / unresolved_candidate
- Question: Does the provided policy corpus disclose the average monetary training cost per Australian Government employee?
- Reference: 未设定：待全文缺失性审核，不能评分为 gold refusal。

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-UN02 — unanswerable_candidate

- 状态：draft / unresolved_candidate
- Question: Does the provided corpus disclose a dated agency-specific AI governance board meeting calendar?
- Reference: 未设定：待全文缺失性审核，不能评分为 gold refusal。

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-UN03 — unanswerable_candidate

- 状态：draft / unresolved_candidate
- Question: Does the Singapore framework disclose the deployment budget for the Bank of Singapore Source of Wealth agentic system?
- Reference: 未设定：待全文缺失性审核，不能评分为 gold refusal。

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-UN04 — unanswerable_candidate

- 状态：draft / unresolved_candidate
- Question: Does the Dayos case disclose a measured post-deployment error rate for automated Tier 1 tickets?
- Reference: 未设定：待全文缺失性审核，不能评分为 gold refusal。

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-UN05 — unanswerable_candidate

- 状态：draft / unresolved_candidate
- Question: Does the provided technical standard prescribe a single minimum RAG Recall@5 score for every agency deployment?
- Reference: 未设定：待全文缺失性审核，不能评分为 gold refusal。

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

## DEV2-UN06 — unanswerable_candidate

- 状态：draft / unresolved_candidate
- Question: Does the provided corpus specify a universal number of years for retaining AI prediction logs across all agencies?
- Reference: 未设定：待全文缺失性审核，不能评分为 gold refusal。

审核意见：待填写（保留历史审核状态；新增题不得自动通过）。

