"""Validate intended multi-child questions against an offline structure audit.

No retrieval score, model calls or reviewer approval is produced.
"""

import argparse
import json
from pathlib import Path

from evaluation.dataset import is_answerable, load_dataset, resolve_groups


def minimum_cover(groups):
    """Exact set cover via evidence-group bitmasks (small question-local groups)."""
    costs = {0: 0}
    for key in set().union(*groups):
        mask = sum(1 << i for i, group in enumerate(groups) if key in group)
        for covered, cost in list(costs.items()):
            merged = covered | mask
            costs[merged] = min(costs.get(merged, len(groups) + 1), cost + 1)
    return costs[(1 << len(groups)) - 1]


def audit_geometry(manifest, cases, audit):
    hashes = {d["filename"]: d["sha256"] for d in manifest["documents"]}
    pool = [
        {
            **child,
            "sha256": hashes[doc["file"]],
            "id": f"{hashes[doc['file']]}:{child['chunk_index']}",
        }
        for doc in audit
        for child in doc["children"]
    ]
    parents = {c["id"]: c["section_id"] for c in pool}
    result = []
    for case in cases:
        row = {"question_id": case["question_id"], "coverage_tags": case.get("coverage_tags", [])}
        if not is_answerable(case):
            row["status"] = "excluded_pending_absence_review"
        else:
            try:
                groups = resolve_groups(case, pool)
                row.update(
                    status="mapped",
                    minimum_children=minimum_cover(groups),
                    minimum_generation_parents=minimum_cover(
                        [{parents[c] for c in group} for group in groups]
                    ),
                )
            except ValueError as exc:
                row.update(status="unmapped", reason=str(exc))
        result.append(row)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest, cases = load_dataset(args.dataset)
    result = audit_geometry(manifest, cases, json.loads(args.audit.read_text(encoding="utf-8")))
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(
            {"dataset": manifest["dataset_version"], "audit": str(args.audit), "results": result},
            handle,
            indent=2,
        )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
