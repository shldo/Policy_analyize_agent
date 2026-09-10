"""Fixed synthetic Inspector checks. No planner, retrieval, generation or database writes."""

import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from app.modules.documents import controlled_retrieval as cr


def cases():
    question = "What checks are required for external suppliers handling confidential records?"
    requirement = {"requirement_id": "r1", "anchors": ["checks"], "question_scope": question}
    # Expected outcomes are used after the model call only.
    rows = [
        (
            "complete_scope",
            question,
            [requirement],
            [
                "External suppliers handling confidential records must pass an access review "
                "and enable audit logging."
            ],
            [True],
        ),
        (
            "wrong_scope",
            question,
            [requirement],
            [
                "Internal teams handling public records must enable audit logging. "
                "External supplier controls are addressed in a separate section not provided here."
            ],
            [False],
        ),
        (
            "background",
            question,
            [requirement],
            ["Confidential records are important. Supplier governance is a strategic priority."],
            [False],
        ),
        (
            "negative",
            "Must all prototype services publish their source code?",
            [
                {
                    "requirement_id": "r1",
                    "anchors": ["publish their source code"],
                    "modality": "yes_no",
                }
            ],
            ["Prototype services are not required to publish their source code."],
            [True],
        ),
        (
            "comparison_missing_side",
            "Compare Cedar and Birch on response time.",
            [
                {
                    "requirement_id": "r1",
                    "anchors": ["Cedar", "response time"],
                    "subject_anchors": ["Cedar"],
                    "dimension_anchors": ["response time"],
                },
                {
                    "requirement_id": "r2",
                    "anchors": ["Birch", "response time"],
                    "subject_anchors": ["Birch"],
                    "dimension_anchors": ["response time"],
                },
            ],
            ["Cedar responds in 20 milliseconds. No measurements for Birch are provided."],
            [True, False],
        ),
        (
            "complementary",
            "Which identity and retention checks must suppliers perform?",
            [{"requirement_id": "r1", "anchors": ["identity and retention checks"]}],
            [
                "Suppliers must verify the identity of each account holder.",
                "Suppliers must review record retention every quarter.",
            ],
            [True],
        ),
    ]
    return rows


def evaluate(case):
    name, question, requirements, texts, expected = case
    children = [
        dict(
            chunk_id=f"synthetic-{i}",
            text=text,
            doc_title="Synthetic policy",
            page_start=1,
            page_end=1,
        )
        for i, text in enumerate(texts)
    ]

    def isolated(q, *, inspect, **unused):
        checked = cr.validate_inspection(inspect(q, requirements, children), requirements, children)
        selected, contract = cr.build_evidence_set(children, checked, limit=8)
        return selected, dict(
            requirements=requirements, inspections=[checked], core_contract=contract
        )

    # Run the exact production nested Inspector and its adapter; never invoke retrieve/plan.
    with patch.object(cr, "run_controlled", isolated):
        selected, trace = cr.retrieve_controlled(question)
    actual = [i["status"] == "complete" for i in trace["inspections"][-1]]
    passed = actual == expected
    if name == "complementary":
        passed = passed and all(
            {r["chunk_id"] for r in bundle} == {c["chunk_id"] for c in children}
            for bundle in trace["inspections"][-1][0]["core_bundles"]
        )
    if name == "negative":
        passed = passed and trace["inspections"][-1][0]["modality_conclusion"] == "negative"
    return dict(
        case_id=name,
        question=question,
        requirements=requirements,
        children=children,
        expected_complete=expected,
        actual_complete=actual,
        passed=passed,
        trace=trace,
        selected_child_ids=[c["chunk_id"] for c in selected],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    summary = dict(
        formal_benchmark=False,
        source_sha256=hashlib.sha256(Path(cr.__file__).read_bytes()).hexdigest(),
        results=[],
    )
    for case in cases():
        try:
            result = evaluate(case)
        except Exception as exc:
            result = dict(case_id=case[0], passed=False, error_type=type(exc).__name__)
        (args.output / f"{case[0]}.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
        )
        summary["results"].append({k: result[k] for k in ("case_id", "passed")})
        print(f"{case[0]}: {result['passed']}", flush=True)
        (args.output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
