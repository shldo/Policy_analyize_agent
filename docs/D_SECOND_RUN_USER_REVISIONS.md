# Agent RAG 修订答案包

本文件包含审核中发现问题的 11 个答案的替换稿。原始运行文件未覆盖；`DEV2-CS07` 还需要重新检索/打包水印证据后，再回写带编号引用的 JSON。

## DEV2-MC06

Dayos and Bank of Singapore use different autonomy designs.

- **Dayos:** Tier 1 tickets are low-severity and reversible. They are automated without a human engineer in the execution loop, but a designated reviewer audits a cross-section of actions every two weeks. Tier 2 actions require human engineer approval before execution. Tier 3 actions, such as production deployments and security changes, are not performed by the agent.
- **Bank of Singapore:** The system has task-level autonomy only: it extracts information, drafts and checks a Source of Wealth memo, operates only when triggered by predefined workflows, does not self-initiate actions, and has no decision authority. Designated human reviewers perform final validation and approval.

Thus, Dayos uses risk-tiered autonomy with retrospective oversight for the lowest-risk tier, while Bank of Singapore uses a uniformly narrow decision-support design with human approval at critical points.

## DEV2-MC08

The test plan should separate formal test data from development data, keep test subjects independent from development of the system under test, and provide an appropriate degree of tester/developer independence. It should also use peer review, bias-awareness training, and documented test decisions to reduce testing bias.

Human verification of test design and implementation is a separate required step: people must verify correctness, consistency and completeness. Controllability testing must verify that human oversight and control, as well as system-control requirements, work as intended.

Where the full required set in Statement 27 is being described, it contains six areas: human verification (Criterion 95), functional performance (96), controllability (97), explainability and transparency (98), calibration (99), and logging (100). Test coverage measurement and test adequacy strategy are recommended under Statement 26, not required.

## DEV2-CS01

The agency should keep three deliverables distinct:

- **Public transparency statement:** Publish it on the public-facing website, review and update it at least annually, when the agency makes a significant change to its AI approach, or when a new factor materially affects its accuracy. The statement should follow the transparency standard and the agency must notify the DTA when it is published or changed.
- **Staff-facing strategic position:** Develop the agency’s strategic position on AI adoption within six months of the policy taking effect and communicate it to staff to give clear direction. It may be a standalone strategy, an addition to an existing strategy, or other staff-facing materials.
- **Staff training:** Implement mandatory responsible-AI training for all staff within twelve months. Additional role-specific training may be needed for staff involved in procurement, development, training or deployment.

The policy separately requires an operational approach to responsible AI within twelve months. That approach must include staff and public pathways for AI safety concerns and incident-handling processes; those are operational governance requirements and should not be presented as mandatory content requirements for every training course. The cited provisions specify internal communication for the strategic position, but do not state that the staff-facing materials must be publicly published.

## DEV2-CS02

For a new AI use case, the agency must screen it against the in-scope criteria in Appendix C during design while developing requirements, and document that screening. If it is in scope, the agency starts the impact assessment at design, finalises it and applies agreed risk treatments before deployment.

For a use case already assessed as out of scope, the agency may adopt it while continuing to meet existing obligations such as privacy and security. If its scope, usage or operation changes materially, the agency must reassess whether it has become in scope. If it is now in scope, the applicable policy actions follow.

The key difference is therefore the trigger: new use cases are screened proactively during design; an adopted out-of-scope use case is reassessed when a material change occurs. The cited provision requires the reassessment, but does not state that it carries exactly the same design-phase documentation requirement as a new use case.

## DEV2-CS05

External-system exposure should be assessed because greater exposure makes an agent more vulnerable to prompt injection and cyberattacks. An agent that can send data to third-party APIs may also leak information or disrupt external systems through excessive requests. Cross-platform actions are an additional concern because a vendor may have tested its agent within its own ecosystem without exhaustively testing interactions across platforms.

The Singapore framework gives MSD’s restriction of vendor-embedded SaaS agents to their own ecosystems as a containment example. It contains residual risk while preserving approved-use-case benefits, but it is a case-specific strategy, not a universal ban. An organisation should assess the exposure, action scope, reversibility, vendor visibility and available controls before approving broader cross-platform access.

## DEV2-CS07

Before building an AI-generated-media service, the agency should first complete the required design-stage pre-work: define the problem, context, intended use and impacted stakeholders; assess AI and non-AI alternatives; consider environmental impact; perform cost analysis; and analyse how AI changes the solution and its delivery. The alternatives assessment should start with the simplest design, justify the need for AI with objective evidence, compare relevant KPIs, and distinguish work better handled by traditional software from work that benefits from AI.

The technical standard also contains media-specific transparency controls. Under Statement 8, where AI-generated content may directly impact a user, the agency must apply visual watermarks and metadata providing transparency, provenance and authorship. Watermarks and metadata should be WCAG-compatible where relevant, and visual and accessible content must indicate when a user is interacting with an AI system. Hidden-watermark tooling based on use case/content risk and assessment of watermarking risks and limitations are recommended rather than required.

These watermark requirements are conditional: they should not be generalised to every internal artefact, such as a team logo that does not directly affect users.

Source to remap after retrieval repair: *Australian Government AI Technical Standard*, pp. 43–44, Statement 8, Criteria 22–26.

## DEV2-CS08

Model version control and logging tests are complementary but distinct.

- **Version control:** Under Criterion 90, track datasets and models, including the algorithm, learning type, hyperparameters, compile-time parameters and tool versions, and maintain rollback options to historical models so performance can be compared and changes can be traced.
- **Logging tests:** Under Criterion 100, test whether the system records warnings and errors and relevant system changes, together with who made the change, the timestamp and the system version.

Version control identifies the model and system states that can be compared or restored. Logging tests verify that the required audit information is actually recorded during operation. The logging requirement concerns relevant system changes; it should not be expanded into a claim that every possible change or every model update is automatically logged.

## DEV2-EX05

No. Criterion 22 does not prohibit adding a watermark to an internal team logo. It says that the mandatory watermarking condition applies where AI-generated content may directly impact a user, and gives a team logo as an example of content that would not need to be watermarked. The agency therefore retains discretion to add one voluntarily. Criterion 26 recommends assessing watermarking risks and limitations; it does not make that assessment mandatory for this out-of-scope example.

## DEV2-MO01

No. The policy expresses the two measures with different obligation strength:

- Agencies **must** implement mandatory responsible-AI training for all staff within twelve months of the policy taking effect.
- Agencies are **strongly recommended** to apply the Australian Government AI technical standard.

The policy does not give adoption of the technical standard the same mandatory status or the same twelve-month deadline as staff training. The technical standard itself contains both required and recommended criteria, but that internal distinction does not turn adoption of the whole standard into a mandatory policy requirement.

## DEV2-MO04

No. Statement 8 separates the criteria by obligation strength:

- **Required:** Criterion 22 requires visual watermarks and metadata for AI-generated media that may directly impact a user; Criterion 23 requires WCAG compatibility where relevant; Criterion 24 requires visual and accessible content indicating when a user is interacting with an AI system.
- **Recommended:** Criterion 25 recommends choosing hidden-watermark tools based on use case and content risk. Criterion 26 recommends assessing watermarking risks and limitations.

Therefore hidden-watermark tooling and risk assessment are not labelled with the same required status as the visual watermark and metadata controls, and the required controls themselves have scope conditions.

## DEV2-UN06

No. The provided corpus does not specify a universal number of years for retaining AI prediction logs across all agencies.

It requires agencies to capture information used to generate a decision or outcome, retain documents relating to the establishment, design and governance of an AI solution under the Archives Act 1983, and retain AI-system compliance records, including records generated during retirement. It also requires planning for archival and destruction criteria across the AI lifecycle.

Those provisions do not establish a fixed retention period for all prediction logs, nor do they show that every prediction log is subject to one uniform retention duty. The applicable number of years would need to be determined from the relevant records-management and archival requirements for the agency and use case.

## 审核归档说明

以上为用户提交的11题人工修订稿，保留提交原文，不覆盖原始模型运行文件，也不作为重新生成后的模型成绩。
用户另行明确：CS07必须删除“supplied documents do not contain media-specific provisions”；Statement 8 Criteria 22–24为required，25–26为recommended。Criterion 23的WCAG要求保留where relevant条件，不能因修订稿使用should而把其标签降为recommended。
技术标准内部required/recommended分类不等于该技术标准对所有机构整体强制适用；仍须保留政策与标准各自适用范围。
CS07引用修复尚未执行：不得把43–44页证据直接绑定到原运行未支持它的引用编号。后续须检索、gate、打包并保存新的独立运行产物。
UN06的人工修订不自动改变整个冻结语料的absence-review状态；正式标签变更须有全文复核记录。
本次仅归档人工审核与修订，未执行新的模型测试，未宣称修复链路已通过。
