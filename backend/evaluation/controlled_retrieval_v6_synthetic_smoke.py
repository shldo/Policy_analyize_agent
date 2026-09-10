"""Run a small, auditable non-benchmark Planner-only smoke."""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

CASES = [
    {
        "case_id": "yes_no",
        "question": "Does the policy require agencies to publish a transparency statement?",
        "semantic_checkpoints": ["yes_no requirement", "explicit obligation scope"],
    },
    {
        "case_id": "enumeration",
        "question": "Which two controls are required for safe AI use: oversight and logging?",
        "semantic_checkpoints": ["oversight", "logging", "two independent requirements"],
    },
    {
        "case_id": "comparison_2x2",
        "question": "Compare Alpha and Beta on cost and speed.",
        "semantic_checkpoints": [
            "Alpha x cost",
            "Alpha x speed",
            "Beta x cost",
            "Beta x speed",
        ],
    },
    {
        "case_id": "scenario",
        "question": (
            "For an external vendor handling sensitive customer data, "
            "what safeguards should an organisation assess?"
        ),
        "semantic_checkpoints": [
            "external vendor",
            "sensitive customer data",
            "safeguard obligation",
        ],
    },
    {
        "case_id": "negation_exception",
        "question": "Is watermarking required, and what exception applies?",
        "semantic_checkpoints": ["yes/no or modality", "watermarking", "exception"],
    },
    {
        "case_id": "yes_no_variant",
        "question": "Are agencies required to publish an AI transparency statement?",
        "semantic_checkpoints": ["yes/no requirement", "agencies", "publish statement"],
    },
    {
        "case_id": "comparison_variant",
        "question": "How do Orion and Nova compare in cost and speed?",
        "semantic_checkpoints": [
            "Orion x cost",
            "Orion x speed",
            "Nova x cost",
            "Nova x speed",
        ],
    },
    {
        "case_id": "scenario_variant",
        "question": (
            "When a supplier handles private customer records, "
            "which safeguards should a department assess?"
        ),
        "semantic_checkpoints": ["supplier", "private customer records", "safeguards"],
    },
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    from app.modules.documents.controlled_retrieval import run_planner_smoke

    args.output.mkdir(parents=True, exist_ok=False)
    report = {
        "status": "running",
        "formal_benchmark": False,
        "scope": "eight fixed non-benchmark synthetic Planner questions; no retrieval or Inspector",
        "started_at": datetime.now(UTC).isoformat(),
        "source_sha256": hashlib.sha256(
            (
                Path(__file__).resolve().parents[1]
                / "app/modules/documents/controlled_retrieval.py"
            ).read_bytes()
        ).hexdigest(),
        "cases": [],
    }
    for case in CASES:
        try:
            planner = run_planner_smoke(case["question"])
            row = {
                **case,
                "status": "completed",
                "planner_audit": planner,
            }
        except Exception as exc:
            row = {
                **case,
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        (args.output / f"{case['case_id']}.json").write_text(
            json.dumps(row, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        report["cases"].append(
            {
                "case_id": case["case_id"],
                "status": row["status"],
                "question_type": row.get("planner_audit", {})
                .get("normalized_plan", {})
                .get("question_type"),
                "requirement_count": len(
                    row.get("planner_audit", {}).get("normalized_plan", {}).get("requirements", [])
                ),
                "error_type": row.get("planner_audit", {})
                .get("normalization_error", {})
                .get("type")
                or row.get("error_type"),
            }
        )
        (args.output / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
    report["status"] = "completed"
    report["finished_at"] = datetime.now(UTC).isoformat()
    (args.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
