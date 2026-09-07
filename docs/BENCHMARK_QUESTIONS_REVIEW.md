# 题目审核清单 · v3 草稿

版本：policy-benchmark-v3-draft；语料仍为 policy-five-v1。共 31 题：13 道开发题、18 道测试候选；29 道可回答、2 道 unresolved_candidate、0 道 unanswerable_confirmed。新测试排序未运行。

用户已提出业务真实性、参考答案完整性和缺失证据处理意见；本版为据此修订的待复核稿，不将部分评审自动视为全题通过。

## 原文与来源完整性

- [Australia_Responsible_AI_Government_v2.pdf](D:/AIWorkspace/Projects/policy-research-agent/backend/data/source_documents/Australia_Responsible_AI_Government_v2.pdf)；SHA256：`94beda4e6e9f61e0dd5d5f17b45b18cf6015b20fd9aabe41d20318f725273c11`。
- [Australia_AI_Transparency_Standard_v2.pdf](D:/AIWorkspace/Projects/policy-research-agent/backend/data/source_documents/Australia_AI_Transparency_Standard_v2.pdf)；SHA256：`bcd3a3cac366fce0d5b0f003ebaee7d66e5062020e204ed500d21d7ad1d99af1`。
- [Australia_AI_Staff_Training_v2.pdf](D:/AIWorkspace/Projects/policy-research-agent/backend/data/source_documents/Australia_AI_Staff_Training_v2.pdf)；SHA256：`7d81ab99a6d9239613ddee0370d034772335b75a3199c2316d5f568080d637c7`。
- [Australia_AI_Technical_Standard_2025.pdf](D:/AIWorkspace/Projects/policy-research-agent/backend/data/source_documents/Australia_AI_Technical_Standard_2025.pdf)；SHA256：`fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24`。
- [Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf](D:/AIWorkspace/Projects/policy-research-agent/backend/data/source_documents/Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf)；SHA256：`2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba`。

2026-09-07 本地新加坡 PDF 已定位，SHA256 与冻结清单一致。附件未送达审阅者不等于知识库缺失；官方字节匹配仍待补。PDF 仅保存在本地，上述链接适用于本机。

## 评审规则

四个字段逐题列出：主体 / action / condition-or-trigger / timeframe-or-exception。null 显示为“不适用或题目未要求”，须人工判断是否真的不适用；程序只能检查字段结构，不能证明答案语义完整。required_answer_points 与必要证据组共同支持将来的生成评分。

- answerable：有明确源证据，参考答案仍可处于待复核状态。
- unanswerable_confirmed：必须记录人工全文复核者、日期及全部冻结文档哈希，才可作为无答案金标。
- unresolved_candidate：未完成全文核验；reference_answer 为 null，禁止当金标拒答评分。

对于清楚的问题，证据不足时说明 provided corpus / available material 的局限，不编造数字或要求无意义补充。不将证据不足解释成现实世界不存在该事实。只有主体、司法辖区、版本等歧义改变检索目标时才追问。此处是 benchmark 预期，未修改应用运行时提示词。

## 编号去向

TEST-17 在 v1 因开发主题重叠移为 DEV-NEG01，后者在 v3 因罚款前提刻意而退休。TEST-20 在 v2 退休。本版不填补编号、不复用 ID；历史题目保留于 policy-v1/v2。

## DEV-AU01 · development · legacy_lookup

How often must agencies review their AI transparency statements?

选题目的：Preserve previously observed v3 retrieval examples in development only.

状态：answerable；审核：draft。

参考答案：Agencies must review and update transparency statements at least annually, and earlier when their approach to AI changes significantly or a new factor materially affects the statement's accuracy.

- 主体：Agencies and their AI transparency statements
- action：Review and update the statement
- condition-or-trigger：Significant change in AI approach or a new factor materially affecting statement accuracy
- timeframe-or-exception：At least once a year; earlier when a trigger occurs

主题组：legacy-AU01。

修订说明：v3: expanded from legacy retrieval anchors into a complete source-backed reference draft; pending semantic sign-off.

必要证据 g1：At least annual review and update

- Australia_AI_Transparency_Standard_v2.pdf，物理页 4：`at least once a year`

必要证据 g2：Significant change trigger

- Australia_AI_Transparency_Standard_v2.pdf，物理页 4：`when making a significant change to the agency’s approach to AI`

必要证据 g3：Material accuracy trigger

- Australia_AI_Transparency_Standard_v2.pdf，物理页 4：`when any new factor materially impacts the existing statement’s accuracy.`

## DEV-AU02 · development · legacy_lookup

Who must agencies notify when publishing or changing an AI transparency statement, and how?

选题目的：Preserve previously observed v3 retrieval examples in development only.

状态：answerable；审核：draft。

参考答案：Agencies must send the DTA a link to the transparency statement by emailing ai@dta.gov.au when the statement is published or updated.

- 主体：Agencies; recipient DTA
- action：Send a link by email to ai@dta.gov.au
- condition-or-trigger：Statement is published or updated
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：legacy-AU02。

修订说明：v3: expanded from legacy retrieval anchors into a complete source-backed reference draft; pending semantic sign-off.

必要证据 g1：Recipient, channel and triggering event

- Australia_AI_Transparency_Standard_v2.pdf，物理页 5：`Agencies must send the DTA a link to the statement when it is published or updated by emailing ai@dta.gov.au.`

## DEV-AU03 · development · legacy_lookup

Within what period must agencies develop a strategic position on AI adoption?

选题目的：Preserve previously observed v3 retrieval examples in development only.

状态：answerable；审核：draft。

参考答案：Agencies must develop a strategic position on AI adoption within 6 months of the policy taking effect.

- 主体：Agencies
- action：Develop a strategic position on AI adoption
- condition-or-trigger：Policy takes effect
- timeframe-or-exception：Within 6 months

主题组：legacy-AU03。

修订说明：v3: expanded from legacy retrieval anchors into a complete source-backed reference draft; pending semantic sign-off.

必要证据 g1：Deadline and starting event

- Australia_Responsible_AI_Government_v2.pdf，物理页 10：`develop a strategic position on AI adoption within 6 months of this policy taking effect.`

## DEV-AU04 · development · legacy_lookup

How frequently must agencies share their AI use case register with the DTA?

选题目的：Preserve previously observed v3 retrieval examples in development only.

状态：answerable；审核：draft。

参考答案：Agencies must share the register with the DTA every 6 months, commencing from when they create the register to meet the requirement.

- 主体：Agencies; DTA
- action：Share the AI use case register
- condition-or-trigger：Creation of the register to meet the requirement
- timeframe-or-exception：Every 6 months, commencing from register creation

主题组：legacy-AU04。

修订说明：v3: expanded from legacy retrieval anchors into a complete source-backed reference draft; pending semantic sign-off.

必要证据 g1：Frequency and commencement

- Australia_Responsible_AI_Government_v2.pdf，物理页 11：`Agencies must share the register with the DTA every 6 months, commencing from when they create the register to meet the above requirement.`

## DEV-AU05 · development · legacy_lookup

When must mandatory responsible AI training be implemented, and which staff does it cover?

选题目的：Preserve previously observed v3 retrieval examples in development only.

状态：answerable；审核：draft。

参考答案：Agencies must implement mandatory responsible AI training for all staff within 12 months of the policy taking effect.

- 主体：Agencies; all staff
- action：Implement mandatory training on responsible AI use
- condition-or-trigger：Policy takes effect
- timeframe-or-exception：Within 12 months

主题组：legacy-AU05。

修订说明：v3: expanded from legacy retrieval anchors into a complete source-backed reference draft; pending semantic sign-off.

必要证据 g1：All staff and implementation deadline

- Australia_Responsible_AI_Government_v2.pdf，物理页 13：`Agencies must implement mandatory training for all staff on responsible AI use within 12 months of this policy taking effect.`

## DEV-TR01 · development · legacy_lookup

According to the staff training guidance, how long does the AI fundamentals module take?

选题目的：Preserve previously observed v3 retrieval examples in development only.

状态：answerable；审核：draft。

参考答案：The AI fundamentals module takes approximately 20 to 30 minutes.

- 主体：Staff taking the AI fundamentals module
- action：Complete the module
- condition-or-trigger：不适用或题目未要求（待审核）
- timeframe-or-exception：Approximately 20 to 30 minutes

主题组：legacy-TR01。

修订说明：v3: expanded from legacy retrieval anchors into a complete source-backed reference draft; pending semantic sign-off.

必要证据 g1：Known legacy answer anchor; completeness not adjudicated.

- Australia_AI_Staff_Training_v2.pdf，物理页 5：`20 to 30 minutes`

## DEV-TS01 · development · legacy_lookup

Does the transparency standard require agencies to list individual AI use cases publicly?

选题目的：Preserve previously observed v3 retrieval examples in development only.

状态：answerable；审核：draft。

参考答案：No. Agencies are not required to list individual AI use cases or provide use-case-level detail, but they may voluntarily provide detail beyond the standard's requirements.

- 主体：Agencies publishing AI transparency statements
- action：Provide a high-level overview without mandatory individual use-case detail
- condition-or-trigger：不适用或题目未要求（待审核）
- timeframe-or-exception：Additional detail may be provided voluntarily

主题组：legacy-TS01。

修订说明：v3: expanded from legacy retrieval anchors into a complete source-backed reference draft; pending semantic sign-off.

必要证据 g1：Known legacy answer anchor; completeness not adjudicated.

- Australia_AI_Transparency_Standard_v2.pdf，物理页 5：`not required to list individual use cases`

## DEV-TS02 · development · legacy_lookup

What two classification dimensions must agencies list in their AI transparency statements?

选题目的：Preserve previously observed v3 retrieval examples in development only.

状态：answerable；审核：draft。

参考答案：Agencies must list both usage patterns and domains when classifying their AI use.

- 主体：Agencies
- action：Classify AI use by usage patterns and domains
- condition-or-trigger：In their AI transparency statements
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：legacy-TS02。

修订说明：v3: expanded from legacy retrieval anchors into a complete source-backed reference draft; pending semantic sign-off.

必要证据 g1：Known legacy answer anchor; completeness not adjudicated.

- Australia_AI_Transparency_Standard_v2.pdf，物理页 7：`both the usage patterns and domains`

## DEV-TECH01 · development · legacy_lookup

When does Criterion 22 require watermarking, and what must it provide?

选题目的：Preserve previously observed v3 retrieval examples in development only.

状态：answerable；审核：draft。

参考答案：Criterion 22 requires visual watermarks and metadata on AI-generated media content that may directly impact a user, to provide transparency and provenance, including authorship. The standard gives a team logo generated with AI as an example that does not need watermarking.

- 主体：Agencies; AI-generated media content
- action：Apply visual watermarks and metadata to provide transparency and provenance, including authorship
- condition-or-trigger：Content may directly impact a user
- timeframe-or-exception：AI-generated team logo given as an example not needing watermarking

主题组：legacy-TECH01。

修订说明：v3: expanded from legacy retrieval anchors into a complete source-backed reference draft; pending semantic sign-off.

必要证据 g1：Watermarks, metadata and required purpose

- Australia_AI_Technical_Standard_2025.pdf，物理页 43：`Apply visual watermarks and metadata to generated media content to provide transparency and provenance, including authorship.`

必要证据 g2：Direct-user-impact applicability and example

- Australia_AI_Technical_Standard_2025.pdf，物理页 43：`This will only apply where AI generated content may directly impact a user. For instance, using AI to generate a team logo would not need to be watermarked.`

## DEV-TECH02 · development · legacy_lookup

Which version management practice is required under Statement 7?

选题目的：Preserve previously observed v3 retrieval examples in development only.

状态：answerable；审核：draft。

参考答案：Statement 7 requires version management across the AI system's end-to-end development lifecycle.

- 主体：Agencies managing AI systems
- action：Manage versions across the end-to-end development lifecycle
- condition-or-trigger：Under Statement 7
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：legacy-TECH02。

修订说明：v3: expanded from legacy retrieval anchors into a complete source-backed reference draft; pending semantic sign-off.

必要证据 g1：Known legacy answer anchor; completeness not adjudicated.

- Australia_AI_Technical_Standard_2025.pdf，物理页 15：`end-to-end development lifecycle`
- Australia_AI_Technical_Standard_2025.pdf，物理页 41：`end-to-end development lifecycle`

## DEV-SG01 · development · legacy_lookup

Which protocols does the framework name for agent-to-tool and agent-to-agent communication?

选题目的：Preserve previously observed v3 retrieval examples in development only.

状态：answerable；审核：draft。

参考答案：The framework names Model Context Protocol (MCP) for agent-to-tool communication and Agent2Agent Protocol (A2A) for communication between agents.

- 主体：Agents, tools and other agents
- action：Use the framework's named communication standards
- condition-or-trigger：MCP: agent-to-tool; A2A: agent-to-agent
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：legacy-SG01。

修订说明：v3: expanded from legacy retrieval anchors into a complete source-backed reference draft; pending semantic sign-off.

必要证据 g1：Agent-to-tool MCP

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 7：`the Model Context Protocol (MCP) has been developed for agents to communicate with tools`

必要证据 g2：Agent-to-agent A2A

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 7：`the Agent2Agent Protocol (A2A) defines a standard for agents to communicate with each other.`

## DEV-SG02 · development · legacy_lookup

Why should organisations prefer deterministic limits over prompt-only limits for agents?

选题目的：Preserve previously observed v3 retrieval examples in development only.

状态：answerable；审核：draft。

参考答案：Deterministic limits bound behavior by design: access controls can prevent a prohibited tool call altogether instead of relying on the agent to obey a prompt. Where limits are non-deterministic or less reliable, the framework recommends additional monitoring or human-in-the-loop review to catch failures.

- 主体：Organisations designing agent limits
- action：Enforce constraints through access controls rather than depending solely on prompt compliance
- condition-or-trigger：Less reliable limits call for additional monitoring or human review
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：legacy-SG02。

修订说明：v3: expanded from legacy retrieval anchors into a complete source-backed reference draft; pending semantic sign-off.

必要证据 g1：Why enforced limits differ from instructions

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 19：`rather than relying on prompts to instruct the agent against accessing certain tools, impose access controls that prevent the tool from being called by the agent at all.`

必要证据 g2：Additional safeguards for less reliable limits

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 19：`Where limits are non-deterministic or less reliable, layer on more monitoring measures or incorporate human-in-the-loop review to catch any failures.`

## DEV-SG03 · development · legacy_lookup

What three design patterns does the framework list for multi-agent systems?

选题目的：Preserve previously observed v3 retrieval examples in development only.

状态：answerable；审核：draft。

参考答案：The three patterns are Sequential (agents run in a structured workflow, passing outputs to the next agent), Supervisor (a supervising agent coordinates specialised agents and calls them as tools), and Swarm (agents work concurrently and hand off when needed). The framework does not prescribe one universally correct architecture; tasks may need hybrid patterns.

- 主体：Multi-agent systems
- action：Sequential, Supervisor and Swarm patterns with their respective coordination behavior
- condition-or-trigger：不适用或题目未要求（待审核）
- timeframe-or-exception：No universally correct architecture; hybrid patterns may suit a task

主题组：legacy-SG03。

修订说明：v3: expanded from legacy retrieval anchors into a complete source-backed reference draft; pending semantic sign-off.

必要证据 g1：Sequential

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 8：`Sequential: Agents work one after another in a linear or otherwise structured workflow`

必要证据 g2：Supervisor

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 8：`Supervisor: One supervising agent coordinates specialised agents under it`

必要证据 g3：Swarm

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 8：`Swarm: Agents work at the same time, handing off to another agent when needed.`

## TEST-01 · test · single_document

Under Australia's responsible AI policy v2.0, which Commonwealth entities must apply the policy and which are only encouraged to do so?

选题目的：Test policy-applicability in policy research using source-backed evidence, without consulting retrieval rankings.

状态：answerable；审核：draft。

参考答案：Non-corporate Commonwealth entities must apply it; corporate Commonwealth entities are encouraged to apply it.

- 主体：Commonwealth entities
- action：NCEs must apply the policy; corporate entities are encouraged
- condition-or-trigger：Entity type determines mandatory versus encouraged application
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：policy-applicability。

必要证据 g1：Mandatory NCE coverage

- Australia_Responsible_AI_Government_v2.pdf，物理页 6：`must apply this policy.`

必要证据 g2：Corporate entities encouraged

- Australia_Responsible_AI_Government_v2.pdf，物理页 6：`are also encouraged to apply this policy.`

## TEST-02 · test · single_document

When did Australia's responsible AI policy v2.0 take effect, and which version did it replace?

选题目的：Test policy-applicability in policy research using source-backed evidence, without consulting retrieval rankings.

状态：answerable；审核：draft。

参考答案：It took effect on 15 December 2025 and replaced v1.1.

- 主体：Responsible AI policy v2.0
- action：Takes effect and replaces v1.1
- condition-or-trigger：不适用或题目未要求（待审核）
- timeframe-or-exception：15 December 2025; replaces v1.1

主题组：policy-applicability。

必要证据 g1：Effective date and replaced version

- Australia_Responsible_AI_Government_v2.pdf，物理页 6：`15 December 2025. It replaces version v1.1`

## TEST-03 · test · single_document

Does Australia's responsible AI policy apply to defence AI use and the national intelligence community, and may they voluntarily adopt elements?

选题目的：Test policy-applicability in policy research using source-backed evidence, without consulting retrieval rankings.

状态：answerable；审核：draft。

参考答案：Defence portfolio AI use and the NIC are excluded. They may voluntarily adopt elements where national security capabilities or interests are not compromised.

- 主体：Defence portfolio AI use and NIC
- action：Excluded; may voluntarily adopt elements
- condition-or-trigger：Voluntary adoption must not compromise national security capabilities or interests
- timeframe-or-exception：National security carveouts

主题组：policy-applicability。

必要证据 g1：Carveouts

- Australia_Responsible_AI_Government_v2.pdf，物理页 6：`This policy does not apply to:`

必要证据 g2：Conditional voluntary adoption

- Australia_Responsible_AI_Government_v2.pdf，物理页 6：`without compromising national security capabilities or interests.`

## TEST-04 · test · single_document

Our agency already follows privacy and cyber security requirements. Can implementing Australia's responsible AI policy replace those obligations, or must the frameworks be applied together?

选题目的：Resolve whether an agency may treat AI-policy implementation as a substitute for existing compliance obligations.

状态：answerable；审核：draft。

参考答案：The AI policy complements and strengthens existing frameworks. It must be read and applied alongside existing frameworks and laws; implementing it does not replace those obligations.

- 主体：Agencies already following privacy/cyber security obligations
- action：Apply the AI policy alongside existing frameworks and laws
- condition-or-trigger：AI-policy compliance does not replace existing obligations
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：policy-existing-obligations。

修订说明：User rated original organisation-name lookup medium relevance; revised to an operational compliance question, pending review.

必要证据 g1：Existing frameworks and laws remain applicable alongside the AI policy.

- Australia_Responsible_AI_Government_v2.pdf，物理页 7：`This policy must be read and applied alongside existing frameworks and laws to ensure agencies meet all their obligations.`

## TEST-05 · test · single_document

Under Australia's responsible AI policy, who should oversee AI incident remediation?

选题目的：Test policy-operations in policy research using source-backed evidence, without consulting retrieval rankings.

状态：answerable；审核：draft。

参考答案：An appropriate governance body or senior executive.

- 主体：Agencies handling AI incidents
- action：Appropriate governance body or senior executive oversees remediation
- condition-or-trigger：AI incident remediation
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：policy-operations。

必要证据 g1：Incident oversight

- Australia_Responsible_AI_Government_v2.pdf，物理页 12：`incident remediation must be overseen by an appropriate governance body or senior executive`

## TEST-06 · test · single_document

At what stage must Australian agencies assess new AI use cases against the in-scope criteria, and must they document the assessment?

选题目的：Test policy-impact-assessment in policy research using source-backed evidence, without consulting retrieval rankings.

状态：answerable；审核：draft。

参考答案：During the design phase while developing requirements; the assessment must be documented.

- 主体：Agencies assessing new AI use cases
- action：Document assessment against in-scope criteria
- condition-or-trigger：New AI use case
- timeframe-or-exception：During design phase while developing requirements

主题组：policy-impact-assessment。

必要证据 g1：Documented design-phase screening

- Australia_Responsible_AI_Government_v2.pdf，物理页 14：`The assessment must be documented and take place during the design phase while developing requirements.`

## TEST-07 · test · single_document

What deadline applies to assessing existing unassessed AI use cases and applying relevant actions under Australia's responsible AI policy?

选题目的：Test policy-impact-assessment in policy research using source-backed evidence, without consulting retrieval rankings.

状态：answerable；审核：draft。

参考答案：30 April 2027.

- 主体：Agencies with existing unassessed use cases
- action：Determine scope and apply relevant policy actions
- condition-or-trigger：Existing use cases not yet assessed
- timeframe-or-exception：By 30 April 2027

主题组：policy-impact-assessment。

必要证据 g1：Existing use-case deadline

- Australia_Responsible_AI_Government_v2.pdf，物理页 14：`apply all relevant policy actions by 30 April 2027.`

## TEST-08 · test · single_document

Can an Australian agency use an internal process instead of the government AI impact assessment tool?

选题目的：Test policy-impact-assessment in policy research using source-backed evidence, without consulting retrieval rankings.

状态：answerable；审核：draft。

参考答案：Yes, if the internal process integrates all provisions of the tool.

- 主体：Agencies using an internal impact-assessment process
- action：May use internal process instead of the government tool
- condition-or-trigger：Must integrate all provisions of the tool
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：policy-impact-assessment。

必要证据 g1：Internal process condition

- Australia_Responsible_AI_Government_v2.pdf，物理页 14：`an internal process that integrates all provisions of the impact assessment tool.`

## TEST-09 · test · single_document

In Singapore's Agentic AI framework, what distinguishes an agent's action-space from its autonomy?

选题目的：Test agent-action-space in policy research using source-backed evidence, without consulting retrieval rankings.

状态：answerable；审核：draft。

参考答案：Action-space concerns accessible tools, systems and actions. Autonomy concerns instructions and the degree of human involvement.

- 主体：Agent design
- action：Action-space concerns accessible tools, systems and actions. Autonomy concerns instructions and the degree of human involvement.
- condition-or-trigger：不适用或题目未要求（待审核）
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：agent-action-space。

必要证据 g1：Action-space

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 9：`An agent’s action-space mainly depends on the tools it has access to`

必要证据 g2：Autonomy

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 9：`An agent’s autonomy mainly depends on its instructions and the level of human involvement`

## TEST-10 · test · single_document

Why can sharing context and intermediate outputs between multiple agents increase sensitive-data exposure?

选题目的：Test agent-multi-risk in policy research using source-backed evidence, without consulting retrieval rankings.

状态：answerable；审核：draft。

参考答案：Sensitive data can be logged, passed to less secure agents or exposed through prompt injection.

- 主体：Multi-agent systems
- action：Sensitive data can be logged, passed to less secure agents or exposed through prompt injection.
- condition-or-trigger：不适用或题目未要求（待审核）
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：agent-multi-risk。

必要证据 g1：Shared-context risks

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 12：`sensitive data to be unintentionally logged, passed to less secure agents, or exposed through prompt injection attacks.`

## TEST-11 · test · single_document

Does the Bank of Singapore Source of Wealth agent independently make credit or onboarding decisions?

选题目的：Test agent-case-ocbc in policy research using source-backed evidence, without consulting retrieval rankings.

状态：answerable；审核：draft。

参考答案：No. It provides decision support; designated human reviewers retain final validation and approval.

- 主体：Bank of Singapore Source of Wealth system
- action：No. It provides decision support; designated human reviewers retain final validation and approval.
- condition-or-trigger：不适用或题目未要求（待审核）
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：agent-case-ocbc。

必要证据 g1：Decision boundary

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 20：`does not make credit, onboarding or risk decisions autonomously`

## TEST-12 · test · single_document

In the MSD case study, what technical measure is planned before enabling higher levels of agent autonomy?

选题目的：Test agent-case-msd in policy research using source-backed evidence, without consulting retrieval rankings.

状态：answerable；审核：draft。

参考答案：A programmatic runtime policy enforcement layer at the AI gateway.

- 主体：MSD agentic AI case
- action：A programmatic runtime policy enforcement layer at the AI gateway.
- condition-or-trigger：不适用或题目未要求（待审核）
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：agent-case-msd。

必要证据 g1：Runtime enforcement

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 21：`A programmatic runtime policy enforcement layer is being implemented at the AI gateway`

## TEST-13 · test · single_document

What does Criterion 95 require humans to verify about AI test design and implementation?

选题目的：Test technical-testing in policy research using source-backed evidence, without consulting retrieval rankings.

状态：answerable；审核：draft。

参考答案：Correctness, consistency and completeness.

- 主体：Australian agencies and the policy/standard named in the question
- action：Correctness, consistency and completeness.
- condition-or-trigger：不适用或题目未要求（待审核）
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：technical-testing。

必要证据 g1：Human verification

- Australia_AI_Technical_Standard_2025.pdf，物理页 21：`Undertake human verification of test design and implementation for correctness, consistency, and completeness.`

## TEST-14 · test · single_document

Under Statement 28 of Australia's AI technical standard, is adversarial testing required or recommended, and what methods are required to test safety measures?

选题目的：Test technical-testing in policy research using source-backed evidence, without consulting retrieval rankings.

状态：answerable；审核：draft。

参考答案：Adversarial testing is recommended; negative testing, failure testing and fault injection are required methods for testing safety measures.

- 主体：Australian agencies and the policy/standard named in the question
- action：Adversarial testing is recommended; negative testing, failure testing and fault injection are required methods for testing safety measures.
- condition-or-trigger：不适用或题目未要求（待审核）
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：technical-testing。

必要证据 g1：Safety testing methods

- Australia_AI_Technical_Standard_2025.pdf，物理页 22：`Test safety measures through negative testing methods, failure testing, and fault injection.`

必要证据 g2：Recommended adversarial testing

- Australia_AI_Technical_Standard_2025.pdf，物理页 22：`Recommended • Criterion 104: Undertake adversarial testing`

## TEST-15 · test · cross_document

Our Australian agency is preparing an in-scope AI use case for deployment. What must be completed for the impact assessment under the responsible AI policy, and what must humans verify about testing under Criterion 95 of the AI technical standard?

选题目的：Assemble impact-assessment and testing checks for the same agency deployment task using the policy and its technical standard.

状态：answerable；审核：draft。

参考答案：Before deployment, the agency must finalise the impact assessment and apply agreed risk treatments. Criterion 95 requires human verification of test design and implementation for correctness, consistency and completeness. These are complementary assessment and testing activities; the cited passages do not establish a single combined approval authority.

- 主体：Australian agency preparing an in-scope AI use case
- action：Finalise assessment/apply risk treatments; human verification of test correctness, consistency, completeness
- condition-or-trigger：In-scope AI use case; policy and Criterion 95 address different checks
- timeframe-or-exception：Assessment and agreed treatments before deployment; do not invent a combined approval authority

主题组：deployment-assessment-testing。

修订说明：User found original Australia/Singapore comparison forced; replaced with complementary requirements for one deployment task, pending review.

必要证据 g1：Finalise the impact assessment and apply agreed risk treatments before deployment.

- Australia_Responsible_AI_Government_v2.pdf，物理页 14：`Before the solution is deployed, agencies must finalise the assessment and apply any agreed risk treatments.`

必要证据 g2：Human verification of test correctness, consistency and completeness.

- Australia_AI_Technical_Standard_2025.pdf，物理页 21：`Undertake human verification of test design and implementation for correctness, consistency, and completeness.`

## TEST-16 · test · cross_document

Compare incident arrangements in Australia's responsible AI policy with Criterion 140 of its technical standard.

选题目的：Test comparison-incidents in policy research using source-backed evidence, without consulting retrieval rankings.

状态：answerable；审核：draft。

参考答案：The policy specifies remediation oversight by a governance body or senior executive; Criterion 140 requires defined incident handling processes.

- 主体：Agencies handling AI incidents
- action：Policy requires remediation oversight; Criterion 140 defines handling processes
- condition-or-trigger：AI incident
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：comparison-incidents。

必要证据 g1：Policy oversight

- Australia_Responsible_AI_Government_v2.pdf，物理页 12：`incident remediation must be overseen by an appropriate governance body or senior executive`

必要证据 g2：Technical process

- Australia_AI_Technical_Standard_2025.pdf，物理页 25：`Criterion 140: Define incident handling processes.`

## TEST-18 · test · missing_detail_candidate

What percentage reduction in processing time did the Bank of Singapore Source of Wealth agent achieve?

选题目的：Plausible in-domain missing detail; requires whole-corpus absence review before scoring.

状态：unresolved_candidate；审核：draft。

参考答案：未确定（null）；没有 gold refusal。

- 主体：不适用或题目未要求（待审核）
- action：不适用或题目未要求（待审核）
- condition-or-trigger：不适用或题目未要求（待审核）
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：agent-case-ocbc。

尚待完成的全文核验：Check the full Singapore case and all corpus documents for measured results; stated objectives do not establish an achieved percentage.

证据不足时预期行为：State the limits of the provided corpus or available material, without inventing the missing detail or asserting global absence. Do not ask for clarification when the question is already clear.

## TEST-19 · test · missing_detail_candidate

Which exact commercial LLM model and model version did MSD deploy in its agentic AI governance case?

选题目的：Plausible in-domain missing detail; requires whole-corpus absence review before scoring.

状态：unresolved_candidate；审核：draft。

参考答案：未确定（null）；没有 gold refusal。

- 主体：不适用或题目未要求（待审核）
- action：不适用或题目未要求（待审核）
- condition-or-trigger：不适用或题目未要求（待审核）
- timeframe-or-exception：不适用或题目未要求（待审核）

主题组：agent-case-msd。

尚待完成的全文核验：Review the full MSD case and corpus for an explicit model/version; do not infer from vendor examples.

证据不足时预期行为：State the limits of the provided corpus or available material, without inventing the missing detail or asserting global absence. Do not ask for clarification when the question is already clear.
