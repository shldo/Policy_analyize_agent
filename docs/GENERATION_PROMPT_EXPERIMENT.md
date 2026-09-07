# 生成完整性提示词对照

## 运行前固定的范围

本轮只评价 v4 的 13 道开发题；沿用先前 dense + reranker top-5 的固定上下文。v5 的四道测试修订不参与，未决负样本不评分。参考答案不发送给模型，不改 gold 或线上提示词。

对照为先前两批共 13 道 baseline 与单次 completeness-v1。新增提示只提出通用要求：保留主体、具体动作/交付物、条件、期限、例外与规范强度，逐项核验引用，不引入题号专用答案。

先比较全部 13 题，不只挑之前失败题；保留新增遗漏或过度解释。DEV-TECH01 的实施方式是否必答、DEV-TECH02 的扩展范围风险仍待用户复核，不能以这些争议项给出正式准确率提升。

这是一轮在已观察开发集上的探索性改进，不是盲评或独立测试。单次、非同时 API 调用无法隔离模型服务波动；temperature=0 也不保证完全确定性。证据不足与澄清行为虽然在新提示中约束，但当前 13 道均可回答，不能据此宣称拒答能力得到验证。

## 复现

在 backend 运行 `python -m evaluation.generation --retrieval-report data/evaluation/benchmark_20260907T033441395971Z.json --run --limit 13 --prompt-variant completeness-v1 --code-version <commit>`。

原始输出保存模型配置、token 用量、每题实际消息与片段；前后只允许系统提示增加预先固定的通用约束。实际模型配置、语料与数据哈希须与基线一致，否则不能视作单变量对照。


## 本轮实测结果

报告：`backend/data/evaluation/generation_20260907T083952570112Z.json`。执行代码：`d1e31b54716b05be50a7420fe3c169cfac710222`。

13 次调用均正常结束，finish_reason=stop；合计输入 37438、输出 937、总计 38375 tokens。机械引用编号检查均未发现越界，不等同语义支持率。

对照检查：模型配置、数据/语料/检索哈希一致，逐题问题和片段完全相同，原始系统消息保留为前缀，用户消息不变。参考答案未进入生成请求。本轮只新增预先固定的提示约束。

结论：不采用为应用默认提示。结果有局部改善，也有未解决遗漏、条款归属风险和评分口径问题，不发布准确率提升数字。33 项自动化检查通过；测试包含基线提示原样保留及实验不含专用题号/答案。宿主禁用插件自动加载导致一条 asyncio_mode 配置警告。

## 全量逐题初审

以下为助手核对，非用户签核或盲评。基线全文见 [开发集基线](GENERATION_DEV_REVIEW.md)。

### DEV-AU01

观察：年度与提前触发条件保持完整，未见核心退步。

实验答案：

Agencies must review and update their AI transparency statements at least once a year, as well as when making a significant change to the agency’s approach to AI, or when any new factor materially impacts the existing statement’s accuracy [2][4].

### DEV-AU02

观察：仍遗漏发送声明链接；通用完整性提醒未解决该遗漏。

实验答案：

Agencies must notify the Digital Transformation Agency (DTA) when they publish or make any changes to their AI transparency statement by emailing ai@dta.gov.au [1][2]. This notification requirement applies both when the statement is first published and whenever it is updated [2].

### DEV-AU03

观察：期限正确，新增的战略目的和向员工传达要求可见原引用片段；比基线更长。

实验答案：

Agencies must develop a strategic position on AI adoption within 6 months of the policy taking effect [1][2]. This position is to emphasise how AI opportunities can be identified and embraced by the agency, and agencies must communicate it to give staff clear direction on AI adoption [1][2].

### DEV-AU04

观察：分享周期和起算点保持完整。

实验答案：

Agencies must share their AI use case register with the DTA every 6 months, commencing from when they create the register [1][2].

### DEV-AU05

观察：期限和全体员工范围保持完整，仍有轻微重复。

实验答案：

Mandatory responsible AI training must be implemented within 12 months of the policy taking effect [1]. It covers all staff, regardless of their role [2]. Agencies must implement this training for all staff on responsible AI use [1][2].

### DEV-SG01

观察：MCP/A2A 及通信方向正确。

实验答案：

The framework names the **Model Context Protocol (MCP)** for agent-to-tool communication and the **Agent2Agent Protocol (A2A)** for agent-to-agent communication [1][2]. It notes that this is a fast-developing space, with more protocols being developed to standardise agent interactions, especially in agentic commerce [1][2].

### DEV-SG02

观察：原答案中缺乏支持的 only 限制已消失；保留系统约束及监控/人工复核要点。本轮观察到改善，不证明多次运行稳定。

实验答案：

Organisations should prefer deterministic, system-level limits over prompt-only (non-deterministic) limits because prompt-layer safeguards can be bypassed or "forgotten" by the agent [2]. Instead of relying on prompts to instruct an agent against accessing certain tools, organisations should impose access controls that prevent the tool from being called by the agent at all [1][3]. This "bound by design" approach is more robust because system-level controls are consistently defined and enforced, whereas prompt-layer safeguards tend to be inconsistently defined across users [4]. Where limits are non-deterministic or less reliable, organisations should layer on more monitoring measures or incorporate human-in-the-loop review to catch any failures [1][3].

### DEV-SG03

观察：只列三种名称，省略各自工作方式和混合架构说明。相对 gold 变短，但原题只问列出三种模式，不能不经审核就将缺少额外说明直接计错；需要先确定最小必答项。

实验答案：

The framework lists three simple design patterns for multi-agent systems: sequential, supervisor, and swarm [1].

### DEV-TECH01

观察：补齐 visual watermarks and metadata，但新增 WCAG 要求实际属于相邻 Criterion 23，而非 Criterion 22。引用片段包含该要求，不过未明确区分条款来源，有条款归属混淆风险。不能简单记作全面修复。

实验答案：

Based on the supplied excerpts, Criterion 22 requires agencies to apply visual watermarks and metadata to generated media content to provide transparency and provenance, including authorship [1][3]. This requirement applies only where AI-generated content may directly impact a user; for example, using AI to generate a team logo would not need to be watermarked [1][3]. The watermark must be WCAG compatible where relevant [1][3].

### DEV-TECH02

观察：核心版本管理要求正确，但扩展更长，仍未说明 [4] 的第三方软件排除条款；相邻段落又说适用于低代码/无代码第三方工具，需在解释中保留层级与范围差异，不宜自行合并为无条件规则。

实验答案：

Under Statement 7, the required version management practice is **Criterion 18: Apply version management practices to the end-to-end development lifecycle** [2][3]. This applies to all AI products, including low code or no code third-party tools [1][5].

The standard mandates that agencies apply version management to the model, training and operation dataset, data in the AI system, training algorithm, and hyperparameters [4][5]. It also requires maintaining design documentation outlining the end-to-end AI system state in line with existing organisational control mechanisms, including point-in-time date and timestamps to data and any changes in data, authorship, relevant licencing details, and changes since last version [4][5]. Additionally, agencies must capture approvals from accountable officials for workflow and model reviews, datasets used for training, and relevant hyperparameters [4][5].

The standard notes that Australian Government API guidelines mandate the use of semantic versioning, which should be enhanced to cater for AI-related information and processes, and that version standards should clearly document the difference between production and non-production data, models, and code [1][5].

### DEV-TR01

观察：约 20–30 分钟保持正确。

实验答案：

According to the staff training guidance, the AI fundamentals training module takes approximately 20 to 30 minutes to complete [1].

### DEV-TS01

观察：核心否定及自愿补充例外保留；比基线减少非必要扩展。

实验答案：

No, the transparency standard does not require agencies to list individual AI use cases publicly. The standard states that agency transparency statements are intended to provide a high-level overview of AI use and management, and agencies are not required to list individual use cases or provide use case level detail [1]. However, agencies may choose to provide detail beyond the requirements to publicly explain their approach to AI [1].

### DEV-TS02

观察：usage patterns 和 domains 保持正确。

实验答案：

Based on the supplied excerpts, agencies must list both the **usage patterns** and **domains** which apply to their use of AI in their transparency statements [1].

## 下一步优先级

1. 先确定评分最小必答项与附加说明边界，尤其 DEV-SG03、DEV-TECH01，不能看到输出后随意切换严格程度。
2. 在审核口径固定后，再尝试独立的结构化证据要点抽取＋答案检查实验；必须记录新增调用/成本，禁止注入 gold，不直接改生产行为。
3. 引用核验需包含条款归属和范围，不能只判断片段中存在类似句子。当前实验暴露出的 Criterion 22/23 混淆可作为开发诊断样例。
4. 扩充新问题前仍以真实业务任务为依据，旧测试主题的变体不当作新的未见测试。
