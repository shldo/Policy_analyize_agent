# ruff: noqa: E501

"""Build an offline agent review over the saved answer audit.

The eight priority cases below are reviewed from the saved answer and final
Child text. The optional remaining-case recheck enriches the saved machine
candidate with the actual cited Child records and keeps its provenance visible;
it is still not human sign-off and remains a provisional quality denominator.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PRIORITY_CASES = (
    "DEV2-UN02",
    "DEV2-UN05",
    "DEV2-UN06",
    "DEV2-MC06",
    "DEV2-CS07",
    "DEV2-MO05",
    "DEV2-MC01",
    "DEV2-CS06",
)


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _manual_claim(
    span: str,
    label: str,
    citation_numbers: list[int],
    reason: str,
) -> dict[str, Any]:
    return {
        "answer_span": span,
        "citation_numbers": citation_numbers,
        "label": label,
        "reason": reason,
    }


MANUAL_REVIEWS: dict[str, dict[str, Any]] = {
    "DEV2-UN02": {
        "verdict": "needs_revision",
        "summary": "结论对摘录范围的限定是谨慎的，但第一条事实把 Technical Standard 的内容错误挂到了 Policy Child [6]。",
        "claims": [
            _manual_claim(
                "The AI Technical Standard states that incident remediation must be overseen by an appropriate governance body or senior executive, and that agencies must establish an approach embedding responsible AI practices within 12 months of the policy taking effect, including a process for adopting AI use cases aligned with the agency's enterprise risk management and governance approach [6].",
                "unsupported",
                [6],
                "Child [6] is the Policy for the Responsible Use of AI in Government. It supports agency-specific policies and mandatory staff training, not the cited Technical Standard incident-remediation statement or the claimed governance approach.",
            ),
            _manual_claim(
                "The Policy for the Responsible Use of AI in Government leaves the governance approach to the agency: agencies with greater AI adoption could create dedicated AI policies, procedures and/or frameworks, and accountable officials are responsible for deciding the appropriate approach for their agency [6].",
                "supported",
                [6],
                "Child [6] states that agencies with greater AI adoption could create dedicated policies/frameworks and accountable officials decide the appropriate approach.",
            ),
            _manual_claim(
                "The Standard for AI Transparency Statements requires agencies to send the DTA a link to their transparency statement when it is published or updated [4], but this is a notification obligation tied to statement publication, not a governance board calendar.",
                "supported",
                [4],
                "Child [4] states the transparency statement publication/update notification requirement; it does not establish a board calendar.",
            ),
            _manual_claim(
                "No excerpt identifies a named agency AI governance board, nor any dated meeting calendar, schedule, or cadence for such a body.",
                "not_verifiable",
                [],
                "This is a bounded statement about the provided excerpts, not proof of absence from the full corpus; it should remain explicitly qualified.",
            ),
        ],
    },
    "DEV2-UN05": {
        "verdict": "pass_partial",
        "summary": "回答谨慎限定为可用摘录；核心 RAG Recall@5 否定结论没有被写成全文不存在，但属于摘录范围内的部分回答。",
        "claims": [
            _manual_claim(
                "No. The available excerpts do not establish any prescribed minimum RAG Recall@5 score, let alone a single one applicable to every agency deployment.",
                "partial",
                [],
                "The retrieved excerpts do not show such a numeric floor, but absence in the excerpts cannot prove absence from the full standard.",
            ),
            _manual_claim(
                "The standard adopts an agency-first approach and emphasises reuse of agency policies, frameworks and practices rather than introducing new processes or duplication [1].",
                "supported",
                [1],
                "Child [1] states the agency-first approach and reuse of existing policies/frameworks.",
            ),
            _manual_claim(
                "Grounding such as RAG is treated as one adaptation technique among several [6].",
                "supported",
                [6],
                "Child [6] lists RAG alongside fine-tuning, pre/post-processing and prompt engineering as adaptation techniques.",
            ),
            _manual_claim(
                "Where RAG is used, the standard requires a feedback loop covering what components would need update or refresh, explicitly including a RAG knowledge base [8].",
                "supported",
                [8],
                "Child [8] includes a decision matrix for components such as a RAG knowledge base.",
            ),
            _manual_claim(
                "Model validation criteria are framed as techniques informed by the AI system's own success criteria, including factual correctness, relevance, benchmarking, consistency and source attribution [7].",
                "supported",
                [7],
                "Child [7] lists these validation considerations.",
            ),
            _manual_claim(
                "The provided excerpts do not state any quantitative retrieval metric or numeric performance floor for RAG.",
                "not_verifiable",
                [],
                "Correctly limited to the retrieved excerpts; not a whole-corpus absence claim.",
            ),
        ],
    },
    "DEV2-UN06": {
        "verdict": "needs_revision",
        "summary": "总体结论对保留年限缺口的表述谨慎，但第一条把预测/动作记录与 commit hash 归到了不包含该完整审计要求的 Child [1]。",
        "claims": [
            _manual_claim(
                "On audit logging, the standard requires agencies to record AI predictions and actions taken, and to use a commit hash to identify the control state of all elements [1].",
                "partial",
                [1],
                "Child [1] states that information used to generate a decision/outcome must be captured and describes version management, but the quoted Child does not establish the full audit-logging/commit-hash claim as written.",
            ),
            _manual_claim(
                "It also addresses configuring audit logging of AI tools and systems, including recording modifications, who made them, authority, rationale and system version [4].",
                "supported",
                [4],
                "Child [4] directly lists audit-log configuration, inputs/outputs, modifications, actor, authority, rationale and system version.",
            ),
            _manual_claim(
                "The only explicit retention obligation in the excerpts concerns documents, not logs, under the Archives Act 1983 [2].",
                "supported",
                [2],
                "Child [2] states retention of documents relating to establishment, design and governance under the Archives Act.",
            ),
            _manual_claim(
                "Retention-adjacent provisions concern data/model retention policies and archival/destruction criteria rather than a fixed number of years [7][8].",
                "supported",
                [7, 8],
                "Children [7] and [8] contain retention-policy and archival/destruction considerations, not a universal year count.",
            ),
            _manual_claim(
                "The available excerpts do not establish any numeric retention period for AI prediction logs.",
                "not_verifiable",
                [],
                "This is properly scoped to the available excerpts and does not assert whole-corpus absence.",
            ),
        ],
    },
    "DEV2-MC06": {
        "verdict": "pass_partial",
        "summary": "两案例的自主性与人工检查均由对应 Child 支持；对自动解决等级的审批细节保留了明确缺口，综合映射也标为 synthesis。",
        "claims": [
            _manual_claim(
                "Dayos grants the agent end-to-end handling of every internal IT request: it reads the ticket, judges urgency and complexity, and either resolves it automatically or routes it to a human [2].",
                "supported",
                [2],
                "Dayos Child [2] states this workflow directly.",
            ),
            _manual_claim(
                "Bank of Singapore grants only task-level autonomy and no decision authority [1].",
                "supported",
                [1],
                "Bank of Singapore Child [1] states extraction/drafting/checking only, no self-initiation and no decision authority.",
            ),
            _manual_claim(
                "Each Dayos ticket type was scored for severity, reversibility and feasibility of human oversight, and the tier dictated autonomy [2].",
                "supported",
                [2],
                "Child [2] lists the three risk-assessment questions and their effect on tier/autonomy.",
            ),
            _manual_claim(
                "Bank of Singapore retains final validation and approval with designated human reviewers, including review after financial documents are assessed [1].",
                "supported",
                [1],
                "Child [1] states final validation/approval and human review at critical decision points.",
            ),
            _manual_claim(
                "The framework excerpt does not state what approval or review applies to Dayos's auto-resolved tier [2].",
                "not_verifiable",
                [2],
                "This is a qualified gap statement; the Child describes routing/autonomy tiering but does not specify the auto-resolved tier's review rule.",
            ),
            _manual_claim(
                "The framework-level mapping of the two cases is synthesis rather than a source label [6].",
                "supported",
                [6],
                "The answer explicitly labels this as synthesis and Child [6] supplies the autonomy-level vocabulary; it must not be presented as a framework classification of either case.",
            ),
        ],
    },
    "DEV2-CS07": {
        "verdict": "pass_partial",
        "summary": "设计风险、性能可靠性和用户透明度均有 Child 支持；没有把摘录未确立的 alternatives assessment 假装成要求。",
        "claims": [
            _manual_claim(
                "The excerpts support design-stage obligations to define the problem, success criteria, performance/reliability metrics and consider malfunctions and harms [1].",
                "supported",
                [1],
                "Child [1] directly lists these design-stage considerations.",
            ),
            _manual_claim(
                "The excerpts do not establish a formal alternatives-assessment requirement as such.",
                "not_verifiable",
                [1],
                "Child [1] discusses design, harms and metrics but does not prescribe a comparison of non-AI or lower-risk alternatives; the answer correctly limits this to the excerpts.",
            ),
            _manual_claim(
                "Criterion 33 requires a mechanism to inform users of AI interactions and output, with possible cues, AI disclosure, watermarks and limitations disclaimers [7].",
                "supported",
                [7],
                "Child [7] states the mechanism and the use-case-dependent examples.",
            ),
            _manual_claim(
                "Criterion 32 covers eliciting and translating human values into technical requirements [7].",
                "supported",
                [7],
                "Child [7] lists surveys/interviews, translation into technical requirements, review and contextual values.",
            ),
            _manual_claim(
                "Agencies should consider watermarking across the lifecycle [3].",
                "supported",
                [3],
                "Child [3] includes watermarking among whole-of-lifecycle considerations.",
            ),
            _manual_claim(
                "The design-stage implication for generated media is explicitly presented as synthesis, not as a source-stated alternatives rule.",
                "supported",
                [1, 7],
                "The synthesis is labelled and bounded by the two cited Child texts; it should not be counted as a mandatory policy requirement.",
            ),
        ],
    },
    "DEV2-MO05": {
        "verdict": "pass_complete",
        "summary": "Required 与 Recommended 的拆分由 Statement 26 原文直接支持，回答没有强化义务强度。",
        "claims": [
            _manual_claim(
                "Mitigating bias in the testing process (Criterion 91) and defining test criteria approaches (Criterion 92) are Required [1][2].",
                "supported",
                [1, 2],
                "Children [1] and [2] label Criteria 91 and 92 Required.",
            ),
            _manual_claim(
                "Defining how test coverage will be measured (Criterion 93) and defining a strategy to ensure test adequacy (Criterion 94) are Recommended [1][4].",
                "supported",
                [1, 4],
                "Children [1] and [4] label Criteria 93 and 94 Recommended.",
            ),
        ],
    },
    "DEV2-MC01": {
        "verdict": "pass_complete",
        "summary": "回答覆盖了设计筛查、影响评估、部署前定稿、登记、持续监测、材料变化重验证和风险分层治理；未把建议性治理写成强制。",
        "claims": [
            _manual_claim(
                "New AI use cases must be assessed against in-scope criteria during design, with the assessment documented and started within 12 months; existing unassessed cases have the stated 30 April 2027 deadline [2].",
                "supported",
                [2],
                "Child [2] states all of these timing and documentation requirements.",
            ),
            _manual_claim(
                "In-scope cases require an impact assessment at design stage and finalisation/risk treatment before deployment [2].",
                "supported",
                [2],
                "Child [2] states commencement at design and finalisation before deployment.",
            ),
            _manual_claim(
                "Deployment requires registration updates, regular monitoring/evaluation and re-validation after material changes; vendor/regulatory changes should also be monitored [1][4].",
                "supported",
                [1, 4],
                "Children [1] and [4] directly support registration, monitoring, material-change re-validation and out-of-scope transition.",
            ),
            _manual_claim(
                "Medium-risk governance is a should-consider option, while high-risk cases have the stated must-report, governance and at-least-annual review obligations [3].",
                "supported",
                [3],
                "Child [3] distinguishes medium-risk should-consider from high-risk must requirements.",
            ),
            _manual_claim(
                "The excerpts do not define material change or the medium-risk monitoring cadence.",
                "not_verifiable",
                [1, 3],
                "The answer correctly records these as gaps rather than inventing thresholds or a cadence.",
            ),
        ],
    },
    "DEV2-CS06": {
        "verdict": "pass_complete",
        "summary": "回答覆盖残余风险接受后的内部责任分配、人工监督、PwC案例、外部价值链和跨框架适用边界；建议与必须的语气保持区分。",
        "claims": [
            _manual_claim(
                "Accepting residual risk does not end the accountability work; organisations should allocate responsibilities and meaningful human oversight [1][6].",
                "supported",
                [1, 6],
                "Children [1] and [6] directly state residual-risk acceptance and accountability/oversight measures.",
            ),
            _manual_claim(
                "Internal arrangements include lifecycle responsibilities for decision makers, product teams, cybersecurity teams and users [2].",
                "supported",
                [2],
                "Child [2] describes these role allocations in the PwC use case.",
            ),
            _manual_claim(
                "The use-case owner remains accountable, while risk, AI Factory and end-user review roles remain defined [2].",
                "supported",
                [2],
                "Child [2] explicitly assigns these operating-accountability roles.",
            ),
            _manual_claim(
                "External arrangements should clarify contractual obligations, security/performance/data protection and third-party controls such as scoped credentials and logging [3].",
                "supported",
                [3],
                "Child [3] directly lists contract allocation, third-party opacity, scoped keys, identity tokens and observability.",
            ),
            _manual_claim(
                "The answer distinguishes the separate Australian high-risk obligations and does not claim they apply to all agentic deployments [5].",
                "supported",
                [5],
                "Child [5] contains the Australian high-risk obligations; the answer explicitly limits their applicability.",
            ),
        ],
    },
}


def _attach_evidence(claim: dict[str, Any], records: dict[int, dict[str, Any]]) -> dict[str, Any]:
    enriched = dict(claim)
    citation_numbers = claim.get("citation_numbers", [])
    evidence = [records[number] for number in citation_numbers if number in records]
    enriched["citation_numbers"] = citation_numbers
    enriched["evidence_child_ids"] = [item.get("child_id") for item in evidence]
    enriched["evidence_quotes"] = [item.get("quote") for item in evidence]
    enriched["citation_numbers_resolved"] = len(evidence) == len(citation_numbers)
    return enriched


def _recheck_candidate(
    case: dict[str, Any],
    records: dict[int, dict[str, Any]],
    prior: dict[str, Any],
    prior_report: Path | None,
) -> dict[str, Any]:
    """Make the saved candidate auditable without upgrading it to sign-off.

    The prior model result is triage input only. This pass verifies that every
    cited number resolves to the saved Child identity and exposes the exact
    Child quote next to each claim. It does not silently change the candidate's
    verdict or infer completeness from citation resolution.
    """
    candidate = prior.get("review") or {}
    claims = []
    answer = case.get("answer", "")
    for claim in candidate.get("claims", []):
        normalized = dict(claim)
        normalized["reason"] = normalized.get("reason") or normalized.get("reason_zh", "")
        normalized["span_in_answer"] = normalized.get("answer_span", "") in answer
        claims.append(_attach_evidence(normalized, records))
    unresolved_numbers = sorted(
        {
            number
            for claim in claims
            for number in claim.get("citation_numbers", [])
            if number not in records
        }
    )
    return {
        "question_id": case["question_id"],
        "question": case["question"],
        "review_method": "agent_recheck_of_machine_candidate",
        "status": "provisional_rechecked",
        "verdict": candidate.get("verdict"),
        "summary": candidate.get("summary_zh"),
        "human_signoff": False,
        "claims": claims,
        "faithfulness": "provisional_not_counted",
        "citation_semantics_checked": False,
        "citation_identity_rechecked": True,
        "unresolved_citation_numbers": unresolved_numbers,
        "provenance": {
            "prior_report": str(prior_report) if prior_report else None,
            "prior_review_method": prior.get("review_method"),
            "machine_candidate_used_as_triage_only": True,
            "human_signoff": False,
        },
    }


def build_review(
    audit_path: Path,
    output_dir: Path,
    prior_report: Path | None = None,
    recheck_remaining: bool = False,
) -> dict[str, Any]:
    audit = _read(audit_path)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty review output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    prior_results = {}
    if prior_report and prior_report.exists():
        report_dir = prior_report.parent
        report = _read(prior_report)
        for item in report.get("results", []):
            case_path = report_dir / f"{item['question_id']}.json"
            if case_path.exists():
                prior_results[item["question_id"]] = _read(case_path)

    cases = []
    for case in audit["cases"]:
        question_id = case["question_id"]
        records = {item["number"]: item for item in case["citation_identity"]["records"]}
        if question_id in MANUAL_REVIEWS:
            decision = MANUAL_REVIEWS[question_id]
            reviewed = {
                "question_id": question_id,
                "question": case["question"],
                "review_method": "agent_review",
                "status": "reviewed",
                "verdict": decision["verdict"],
                "summary": decision["summary"],
                "human_signoff": False,
                "claims": [_attach_evidence(item, records) for item in decision["claims"]],
                "faithfulness": "needs_revision"
                if any(
                    item["label"] in {"unsupported", "contradicted"} for item in decision["claims"]
                )
                else "supported_or_qualified",
                "citation_semantics_checked": True,
            }
        elif recheck_remaining and question_id in prior_results:
            reviewed = _recheck_candidate(case, records, prior_results[question_id], prior_report)
        else:
            prior = prior_results.get(question_id, {})
            candidate = prior.get("review") or {}
            reviewed = {
                "question_id": question_id,
                "question": case["question"],
                "review_method": "machine_assisted_candidate_not_independent",
                "status": "provisional",
                "verdict": candidate.get("verdict"),
                "summary": candidate.get("summary_zh"),
                "human_signoff": False,
                "claims": candidate.get("claims", []),
                "faithfulness": "not_counted",
                "citation_semantics_checked": False,
                "provisional_source": str(prior_report) if prior_report else None,
            }
        cases.append(reviewed)
        (output_dir / f"{question_id}.json").write_text(
            json.dumps(reviewed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    manual_cases = [case for case in cases if case["review_method"] == "agent_review"]
    rechecked_cases = [
        case for case in cases if case["review_method"] == "agent_recheck_of_machine_candidate"
    ]
    manual_claims = [claim for case in manual_cases for claim in case["claims"]]
    rechecked_claims = [claim for case in rechecked_cases for claim in case["claims"]]
    label_counts = {}
    for claim in manual_claims:
        label_counts[claim["label"]] = label_counts.get(claim["label"], 0) + 1
    summary = {
        "schema_version": "agent-review-v1",
        "created_at": datetime.now(UTC).isoformat(),
        "review_method": "agent_review_not_human_signoff",
        "source_audit": str(audit_path.resolve()),
        "counts": {
            "total_cases": len(cases),
            "agent_reviewed_cases": len(manual_cases),
            "agent_rechecked_cases": len(rechecked_cases),
            "provisional_machine_assisted_cases": len(cases)
            - len(manual_cases)
            - len(rechecked_cases),
            "agent_review_claims": len(manual_claims),
            "agent_recheck_claims": len(rechecked_claims),
            "agent_review_label_counts": label_counts,
            "human_signoff_cases": 0,
        },
        "quality_metrics": {
            "faithfulness_denominator": len(manual_claims),
            "citation_semantic_denominator": len(manual_claims),
            "complete_answer_denominator": len(manual_cases),
            "rechecked_case_count": len(rechecked_cases),
            "rechecked_claim_count": len(rechecked_claims),
            "note": "Strict quality metrics cover the eight independently agent-reviewed cases only. Remaining-case rechecks are evidence-traceable but provisional and excluded from strict denominators.",
        },
        "cases": cases,
    }
    (output_dir / "report.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Agent review of saved answers",
        "",
        "`agent_review` is not human sign-off. Eight priority cases were reviewed against saved Child text. Remaining cases, when `--recheck-remaining` is used, expose cited Child evidence and candidate claims but remain provisional and are excluded from strict quality denominators.",
        "",
        f"- Independently agent-reviewed: {len(manual_cases)}/50",
        f"- Agent-rechecked provisional cases: {len(rechecked_cases)}/50",
        f"- Unrechecked machine-assisted candidates: {len(cases) - len(manual_cases) - len(rechecked_cases)}/50",
        f"- Agent-reviewed atomic claims: {len(manual_claims)}",
        "- Human sign-off: 0",
        "",
        "| Question | Status | Verdict | Review method | Human sign-off |",
        "|---|---|---|---|---|",
    ]
    for case in cases:
        lines.append(
            f"| {case['question_id']} | {case['status']} | {case.get('verdict')} | "
            f"{case['review_method']} | no |"
        )
    (output_dir / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prior-report", type=Path)
    parser.add_argument(
        "--recheck-remaining",
        action="store_true",
        help="Attach saved Child evidence to the other cases' machine candidates without counting them as strict quality review.",
    )
    args = parser.parse_args()
    summary = build_review(
        args.audit, args.output, args.prior_report, recheck_remaining=args.recheck_remaining
    )
    print(json.dumps(summary["counts"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
