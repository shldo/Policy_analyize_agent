"""Summarize saved paired Gate outputs without calling models or reading the DB."""

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import mean, median


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    report = json.loads((args.run / "report.json").read_text(encoding="utf-8"))
    rows = [
        json.loads((args.run / f"{key}.json").read_text(encoding="utf-8"))
        for key in report["selected_ids"]
        if (args.run / f"{key}.json").exists()
    ]
    scored = [r for r in rows if r.get("evidence_groups") and r.get("packed_scores")]
    stages = {}
    for stage in ("dense", "bm25", "candidate", "reranked", "strict", "packed"):
        scores = [
            (r["strict_baseline"]["packed_scores"] if stage == "strict" else r[f"{stage}_scores"])
            for r in scored
        ]
        stages[stage] = {
            "n": len(scores),
            **({key: mean(s[key] for s in scores) for key in scores[0]} if scores else {}),
        }
        stages[stage]["complete_count_at_20"] = sum(s["all_evidence_at_20"] for s in scores)
        stages[stage]["complete_count_at_5"] = sum(s["all_evidence_at_5"] for s in scores)
    changed = [
        {
            "id": r["question_id"],
            "strict": r["strict_baseline"]["packed_scores"]["evidence_group_coverage_at_20"],
            "partial": r["packed_scores"]["evidence_group_coverage_at_20"],
        }
        for r in scored
        if r["strict_baseline"]["packed_scores"] != r["packed_scores"]
    ]
    incomplete = [
        {
            "id": r["question_id"],
            "coverage": r["packed_scores"]["evidence_group_coverage_at_20"],
            "generation": r["generation"]["status"],
        }
        for r in scored
        if not r["packed_scores"]["all_evidence_at_20"]
    ]
    summary = {
        "run": str(args.run),
        "status": report["status"],
        "cases": len(rows),
        "scored": len(scored),
        "unscored_ids": [r["question_id"] for r in rows if not r.get("evidence_groups")],
        "corpus_unchanged": report.get("corpus_unchanged"),
        "stages": stages,
        "strict_generation_allowed": sum(
            r.get("strict_baseline", {}).get("generation_allowed", False) for r in rows
        ),
        "partial_generation_allowed": sum(
            r.get("packed", {}).get("generation_allowed", False) for r in rows
        ),
        "generation_statuses": dict(Counter(r["generation"]["status"] for r in rows)),
        "error_types": dict(Counter(r.get("error_type") for r in rows if r["status"] == "error")),
        "coverage_statuses": dict(
            Counter(r.get("packed", {}).get("coverage_status") for r in rows)
        ),
        "changed_scores": changed,
        "incomplete_packed": incomplete,
        "false_certified_complete": [
            r["question_id"]
            for r in scored
            if r["packed"].get("coverage_sufficient")
            and not r["packed_scores"]["all_evidence_at_20"]
        ],
        "context_tokens_mean": mean(r["packed"]["packed_token_count"] for r in scored)
        if scored
        else None,
        "strict_context_tokens_mean": mean(r["strict_baseline"]["context_tokens"] for r in scored)
        if scored
        else None,
        "retrieval_seconds_median": median(
            r["retrieval_seconds"] for r in rows if "retrieval_seconds" in r
        ),
        "generation_seconds_median": median(
            r["generation"]["seconds"] for r in rows if "seconds" in r["generation"]
        ),
        "semantic_review": "Not inferred from successful generation or citation syntax.",
    }
    (args.run / "paired_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
