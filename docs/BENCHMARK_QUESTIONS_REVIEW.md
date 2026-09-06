# 首版题目审核清单

题集：policy-benchmark-v1-draft。所有问题为英文，说明面向项目维护者。

共有 33 题：13 道历史开发题、1 道新增开发拒答候选题、19 道新测试候选题。全部保持 draft。原文匹配和助手页面抽查不等于独立人工复核；测试排序尚未读取。不要因为题目分数不理想而删题。

审核每题的业务合理性、参考答案完整性、证据支持、跨文件等价答案、与开发题的语义重叠。不可回答题需要审核全部冻结语料；检索不到不是不存在的证据。审核完成后在 JSONL 中填写 reviewed_by 并更新 review_status；修改题集必须更新版本。

## DEV-AU01 · development · legacy_lookup

How often must agencies review their AI transparency statements?

选题目的：Preserve previously observed v3 retrieval examples in development only.

参考答案：Legacy evidence draft: reviewed and updated annually; at least once a year. Expand and review answer completeness before generation scoring.

主题组：legacy-AU01。审核：待人工复核。

必要证据 g1：Known legacy answer anchor; completeness not adjudicated.

- Australia_Responsible_AI_Government_v2.pdf，物理页 10：`reviewed and updated annually`
- Australia_AI_Transparency_Standard_v2.pdf，物理页 4：`at least once a year`

## DEV-AU02 · development · legacy_lookup

Who must agencies notify when publishing or changing an AI transparency statement, and how?

选题目的：Preserve previously observed v3 retrieval examples in development only.

参考答案：Legacy evidence draft: notify the DTA; send the DTA a link. Expand and review answer completeness before generation scoring.

主题组：legacy-AU02。审核：待人工复核。

必要证据 g1：Known legacy answer anchor; completeness not adjudicated.

- Australia_Responsible_AI_Government_v2.pdf，物理页 10：`notify the DTA`
- Australia_AI_Transparency_Standard_v2.pdf，物理页 5：`send the DTA a link`

## DEV-AU03 · development · legacy_lookup

Within what period must agencies develop a strategic position on AI adoption?

选题目的：Preserve previously observed v3 retrieval examples in development only.

参考答案：Legacy evidence draft: within 6 months. Expand and review answer completeness before generation scoring.

主题组：legacy-AU03。审核：待人工复核。

必要证据 g1：Known legacy answer anchor; completeness not adjudicated.

- Australia_Responsible_AI_Government_v2.pdf，物理页 10：`within 6 months`

## DEV-AU04 · development · legacy_lookup

How frequently must agencies share their AI use case register with the DTA?

选题目的：Preserve previously observed v3 retrieval examples in development only.

参考答案：Legacy evidence draft: every 6 months. Expand and review answer completeness before generation scoring.

主题组：legacy-AU04。审核：待人工复核。

必要证据 g1：Known legacy answer anchor; completeness not adjudicated.

- Australia_Responsible_AI_Government_v2.pdf，物理页 11：`every 6 months`

## DEV-AU05 · development · legacy_lookup

When must mandatory responsible AI training be implemented, and which staff does it cover?

选题目的：Preserve previously observed v3 retrieval examples in development only.

参考答案：Legacy evidence draft: mandatory training for all staff. Expand and review answer completeness before generation scoring.

主题组：legacy-AU05。审核：待人工复核。

必要证据 g1：Known legacy answer anchor; completeness not adjudicated.

- Australia_Responsible_AI_Government_v2.pdf，物理页 13：`mandatory training for all staff`

## DEV-TR01 · development · legacy_lookup

According to the staff training guidance, how long does the AI fundamentals module take?

选题目的：Preserve previously observed v3 retrieval examples in development only.

参考答案：Legacy evidence draft: 20 to 30 minutes. Expand and review answer completeness before generation scoring.

主题组：legacy-TR01。审核：待人工复核。

必要证据 g1：Known legacy answer anchor; completeness not adjudicated.

- Australia_AI_Staff_Training_v2.pdf，物理页 5：`20 to 30 minutes`

## DEV-TS01 · development · legacy_lookup

Does the transparency standard require agencies to list individual AI use cases publicly?

选题目的：Preserve previously observed v3 retrieval examples in development only.

参考答案：Legacy evidence draft: not required to list individual use cases. Expand and review answer completeness before generation scoring.

主题组：legacy-TS01。审核：待人工复核。

必要证据 g1：Known legacy answer anchor; completeness not adjudicated.

- Australia_AI_Transparency_Standard_v2.pdf，物理页 5：`not required to list individual use cases`

## DEV-TS02 · development · legacy_lookup

What two classification dimensions must agencies list in their AI transparency statements?

选题目的：Preserve previously observed v3 retrieval examples in development only.

参考答案：Legacy evidence draft: both the usage patterns and domains. Expand and review answer completeness before generation scoring.

主题组：legacy-TS02。审核：待人工复核。

必要证据 g1：Known legacy answer anchor; completeness not adjudicated.

- Australia_AI_Transparency_Standard_v2.pdf，物理页 7：`both the usage patterns and domains`

## DEV-TECH01 · development · legacy_lookup

When does Criterion 22 require watermarking, and what must it provide?

选题目的：Preserve previously observed v3 retrieval examples in development only.

参考答案：Legacy evidence draft: may directly impact a user. Expand and review answer completeness before generation scoring.

主题组：legacy-TECH01。审核：待人工复核。

必要证据 g1：Known legacy answer anchor; completeness not adjudicated.

- Australia_AI_Technical_Standard_2025.pdf，物理页 43：`may directly impact a user`

## DEV-TECH02 · development · legacy_lookup

Which version management practice is required under Statement 7?

选题目的：Preserve previously observed v3 retrieval examples in development only.

参考答案：Legacy evidence draft: end-to-end development lifecycle. Expand and review answer completeness before generation scoring.

主题组：legacy-TECH02。审核：待人工复核。

必要证据 g1：Known legacy answer anchor; completeness not adjudicated.

- Australia_AI_Technical_Standard_2025.pdf，物理页 15：`end-to-end development lifecycle`
- Australia_AI_Technical_Standard_2025.pdf，物理页 41：`end-to-end development lifecycle`

## DEV-SG01 · development · legacy_lookup

Which protocols does the framework name for agent-to-tool and agent-to-agent communication?

选题目的：Preserve previously observed v3 retrieval examples in development only.

参考答案：Legacy evidence draft: Model Context Protocol (MCP). Expand and review answer completeness before generation scoring.

主题组：legacy-SG01。审核：待人工复核。

必要证据 g1：Known legacy answer anchor; completeness not adjudicated.

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 7：`Model Context Protocol (MCP)`

## DEV-SG02 · development · legacy_lookup

Why should organisations prefer deterministic limits over prompt-only limits for agents?

选题目的：Preserve previously observed v3 retrieval examples in development only.

参考答案：Legacy evidence draft: prefer deterministic rather than non-deterministic limits. Expand and review answer completeness before generation scoring.

主题组：legacy-SG02。审核：待人工复核。

必要证据 g1：Known legacy answer anchor; completeness not adjudicated.

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 19：`prefer deterministic rather than non-deterministic limits`

## DEV-SG03 · development · legacy_lookup

What three design patterns does the framework list for multi-agent systems?

选题目的：Preserve previously observed v3 retrieval examples in development only.

参考答案：Legacy evidence draft: Three simple design patterns for multi-agent systems. Expand and review answer completeness before generation scoring.

主题组：legacy-SG03。审核：待人工复核。

必要证据 g1：Known legacy answer anchor; completeness not adjudicated.

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 8：`Three simple design patterns for multi-agent systems`

## TEST-01 · test · single_document

Under Australia's responsible AI policy v2.0, which Commonwealth entities must apply the policy and which are only encouraged to do so?

选题目的：Test policy-applicability in policy research using source-backed evidence, without consulting retrieval rankings.

参考答案：Non-corporate Commonwealth entities must apply it; corporate Commonwealth entities are encouraged to apply it.

主题组：policy-applicability。审核：待人工复核。

必要证据 g1：Mandatory NCE coverage

- Australia_Responsible_AI_Government_v2.pdf，物理页 6：`must apply this policy.`

必要证据 g2：Corporate entities encouraged

- Australia_Responsible_AI_Government_v2.pdf，物理页 6：`are also encouraged to apply this policy.`

## TEST-02 · test · single_document

When did Australia's responsible AI policy v2.0 take effect, and which version did it replace?

选题目的：Test policy-applicability in policy research using source-backed evidence, without consulting retrieval rankings.

参考答案：It took effect on 15 December 2025 and replaced v1.1.

主题组：policy-applicability。审核：待人工复核。

必要证据 g1：Effective date and replaced version

- Australia_Responsible_AI_Government_v2.pdf，物理页 6：`15 December 2025. It replaces version v1.1`

## TEST-03 · test · single_document

Does Australia's responsible AI policy apply to defence AI use and the national intelligence community, and may they voluntarily adopt elements?

选题目的：Test policy-applicability in policy research using source-backed evidence, without consulting retrieval rankings.

参考答案：Defence portfolio AI use and the NIC are excluded. They may voluntarily adopt elements where national security capabilities or interests are not compromised.

主题组：policy-applicability。审核：待人工复核。

必要证据 g1：Carveouts

- Australia_Responsible_AI_Government_v2.pdf，物理页 6：`This policy does not apply to:`

必要证据 g2：Conditional voluntary adoption

- Australia_Responsible_AI_Government_v2.pdf，物理页 6：`without compromising national security capabilities or interests.`

## TEST-04 · test · single_document

Which organisation's AI definition should agencies use under Australia's responsible AI policy?

选题目的：Test policy-definitions in policy research using source-backed evidence, without consulting retrieval rankings.

参考答案：The OECD definition.

主题组：policy-definitions。审核：待人工复核。

必要证据 g1：OECD definition

- Australia_Responsible_AI_Government_v2.pdf，物理页 7：`Organisation for Economic Co-operation and Development (OECD)`

## TEST-05 · test · single_document

Under Australia's responsible AI policy, who should oversee AI incident remediation?

选题目的：Test policy-operations in policy research using source-backed evidence, without consulting retrieval rankings.

参考答案：An appropriate governance body or senior executive.

主题组：policy-operations。审核：待人工复核。

必要证据 g1：Incident oversight

- Australia_Responsible_AI_Government_v2.pdf，物理页 12：`incident remediation must be overseen by an appropriate governance body or senior executive`

## TEST-06 · test · single_document

At what stage must Australian agencies assess new AI use cases against the in-scope criteria, and must they document the assessment?

选题目的：Test policy-impact-assessment in policy research using source-backed evidence, without consulting retrieval rankings.

参考答案：During the design phase while developing requirements; the assessment must be documented.

主题组：policy-impact-assessment。审核：待人工复核。

必要证据 g1：Documented design-phase screening

- Australia_Responsible_AI_Government_v2.pdf，物理页 14：`The assessment must be documented and take place during the design phase while developing requirements.`

## TEST-07 · test · single_document

What deadline applies to assessing existing unassessed AI use cases and applying relevant actions under Australia's responsible AI policy?

选题目的：Test policy-impact-assessment in policy research using source-backed evidence, without consulting retrieval rankings.

参考答案：30 April 2027.

主题组：policy-impact-assessment。审核：待人工复核。

必要证据 g1：Existing use-case deadline

- Australia_Responsible_AI_Government_v2.pdf，物理页 14：`apply all relevant policy actions by 30 April 2027.`

## TEST-08 · test · single_document

Can an Australian agency use an internal process instead of the government AI impact assessment tool?

选题目的：Test policy-impact-assessment in policy research using source-backed evidence, without consulting retrieval rankings.

参考答案：Yes, if the internal process integrates all provisions of the tool.

主题组：policy-impact-assessment。审核：待人工复核。

必要证据 g1：Internal process condition

- Australia_Responsible_AI_Government_v2.pdf，物理页 14：`an internal process that integrates all provisions of the impact assessment tool.`

## TEST-09 · test · single_document

In Singapore's Agentic AI framework, what distinguishes an agent's action-space from its autonomy?

选题目的：Test agent-action-space in policy research using source-backed evidence, without consulting retrieval rankings.

参考答案：Action-space concerns accessible tools, systems and actions. Autonomy concerns instructions and the degree of human involvement.

主题组：agent-action-space。审核：待人工复核。

必要证据 g1：Action-space

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 9：`An agent’s action-space mainly depends on the tools it has access to`

必要证据 g2：Autonomy

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 9：`An agent’s autonomy mainly depends on its instructions and the level of human involvement`

## TEST-10 · test · single_document

Why can sharing context and intermediate outputs between multiple agents increase sensitive-data exposure?

选题目的：Test agent-multi-risk in policy research using source-backed evidence, without consulting retrieval rankings.

参考答案：Sensitive data can be logged, passed to less secure agents or exposed through prompt injection.

主题组：agent-multi-risk。审核：待人工复核。

必要证据 g1：Shared-context risks

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 12：`sensitive data to be unintentionally logged, passed to less secure agents, or exposed through prompt injection attacks.`

## TEST-11 · test · single_document

Does the Bank of Singapore Source of Wealth agent independently make credit or onboarding decisions?

选题目的：Test agent-case-ocbc in policy research using source-backed evidence, without consulting retrieval rankings.

参考答案：No. It provides decision support; designated human reviewers retain final validation and approval.

主题组：agent-case-ocbc。审核：待人工复核。

必要证据 g1：Decision boundary

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 20：`does not make credit, onboarding or risk decisions autonomously`

## TEST-12 · test · single_document

In the MSD case study, what technical measure is planned before enabling higher levels of agent autonomy?

选题目的：Test agent-case-msd in policy research using source-backed evidence, without consulting retrieval rankings.

参考答案：A programmatic runtime policy enforcement layer at the AI gateway.

主题组：agent-case-msd。审核：待人工复核。

必要证据 g1：Runtime enforcement

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 21：`A programmatic runtime policy enforcement layer is being implemented at the AI gateway`

## TEST-13 · test · single_document

What does Criterion 95 require humans to verify about AI test design and implementation?

选题目的：Test technical-testing in policy research using source-backed evidence, without consulting retrieval rankings.

参考答案：Correctness, consistency and completeness.

主题组：technical-testing。审核：待人工复核。

必要证据 g1：Human verification

- Australia_AI_Technical_Standard_2025.pdf，物理页 21：`Undertake human verification of test design and implementation for correctness, consistency, and completeness.`

## TEST-14 · test · single_document

Under Statement 28 of Australia's AI technical standard, is adversarial testing required or recommended, and what methods are required to test safety measures?

选题目的：Test technical-testing in policy research using source-backed evidence, without consulting retrieval rankings.

参考答案：Adversarial testing is recommended; negative testing, failure testing and fault injection are required methods for testing safety measures.

主题组：technical-testing。审核：待人工复核。

必要证据 g1：Safety testing methods

- Australia_AI_Technical_Standard_2025.pdf，物理页 22：`Test safety measures through negative testing methods, failure testing, and fault injection.`

必要证据 g2：Recommended adversarial testing

- Australia_AI_Technical_Standard_2025.pdf，物理页 22：`Recommended • Criterion 104: Undertake adversarial testing`

## TEST-15 · test · cross_document

Compare human oversight in Australia's Criterion 95 with the Bank of Singapore Source of Wealth case in Singapore's framework. What does each require people to review?

选题目的：Test comparison-oversight in policy research using source-backed evidence, without consulting retrieval rankings.

参考答案：Criterion 95 concerns human verification of test design and implementation. The bank case retains human validation and approval of advisory Source of Wealth outputs.

主题组：comparison-oversight。审核：待人工复核。

必要证据 g1：Australian testing oversight

- Australia_AI_Technical_Standard_2025.pdf，物理页 21：`Undertake human verification of test design and implementation for correctness, consistency, and completeness.`

必要证据 g2：Bank output oversight

- Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf，物理页 20：`final validation and approval remain with designated human reviewers.`

## TEST-16 · test · cross_document

Compare incident arrangements in Australia's responsible AI policy with Criterion 140 of its technical standard.

选题目的：Test comparison-incidents in policy research using source-backed evidence, without consulting retrieval rankings.

参考答案：The policy specifies remediation oversight by a governance body or senior executive; Criterion 140 requires defined incident handling processes.

主题组：comparison-incidents。审核：待人工复核。

必要证据 g1：Policy oversight

- Australia_Responsible_AI_Government_v2.pdf，物理页 12：`incident remediation must be overseen by an appropriate governance body or senior executive`

必要证据 g2：Technical process

- Australia_AI_Technical_Standard_2025.pdf，物理页 25：`Criterion 140: Define incident handling processes.`

## DEV-NEG01 · development · unanswerable_candidate

What exact fine in Australian dollars does the responsible AI policy v2.0 prescribe for a late transparency statement?

选题目的：Plausible in-domain missing detail; requires whole-corpus absence review before scoring.

参考答案：The frozen corpus does not establish the requested detail; state that evidence is insufficient.

主题组：legacy-AU01。审核：待人工复核。

缺失证据审核方法：Check all five documents for an explicit penalty and monetary amount; do not infer from deadlines.

## TEST-18 · test · unanswerable_candidate

What percentage reduction in processing time did the Bank of Singapore Source of Wealth agent achieve?

选题目的：Plausible in-domain missing detail; requires whole-corpus absence review before scoring.

参考答案：The frozen corpus does not establish the requested detail; state that evidence is insufficient.

主题组：agent-case-ocbc。审核：待人工复核。

缺失证据审核方法：Check the full Singapore case and all corpus documents for measured results; stated objectives do not establish an achieved percentage.

## TEST-19 · test · unanswerable_candidate

Which exact commercial LLM model and model version did MSD deploy in its agentic AI governance case?

选题目的：Plausible in-domain missing detail; requires whole-corpus absence review before scoring.

参考答案：The frozen corpus does not establish the requested detail; state that evidence is insufficient.

主题组：agent-case-msd。审核：待人工复核。

缺失证据审核方法：Review the full MSD case and corpus for an explicit model/version; do not infer from vendor examples.

## TEST-20 · test · unanswerable_candidate

Which cloud GPU instance type must every Australian agency use under the AI technical standard?

选题目的：Plausible in-domain missing detail; requires whole-corpus absence review before scoring.

参考答案：The frozen corpus does not establish the requested detail; state that evidence is insufficient.

主题组：technical-compute。审核：待人工复核。

缺失证据审核方法：Review the technical standard and full corpus for a universally mandatory instance SKU; generic compute requirements are insufficient.


