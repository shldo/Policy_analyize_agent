"""Paired draft comparison: identical cases/settings, common mappable denominator."""

import argparse
import json
from pathlib import Path


def compare(flat_report, parent_report, flat, parent):
    for key in (
        "dataset_sha256",
        "selected_ids",
        "generation_target",
        "embedding_model",
        "candidate_k",
        "rerank_k",
    ):
        if flat_report[key] != parent_report[key]:
            raise ValueError(f"Non-comparable setting: {key}")
    if not all(
        r["status"] == "completed" and r.get("corpus_unchanged")
        for r in (flat_report, parent_report)
    ):
        raise ValueError("Runs must complete with unchanged corpora")
    pairs = []
    for key in flat_report["selected_ids"]:
        a, b = flat[key], parent[key]
        mappable = all(
            r.get("reranked_scores") is not None and r["status"] == "completed" for r in (a, b)
        )
        pairs.append(
            {
                "id": key,
                "category": a["category"],
                "common_mappable": mappable,
                "flat_mapping": a["mapping_status"],
                "parent_mapping": b["mapping_status"],
                "flat_scores": {s: a.get(s) for s in STAGES},
                "parent_scores": {s: b.get(s) for s in STAGES},
            }
        )
    eligible = [p for p in pairs if p["common_mappable"]]
    metrics = {}
    for side in ("flat", "parent"):
        metrics[side] = {}
        for stage in STAGES:
            values = [p[f"{side}_scores"][stage] for p in eligible]
            metrics[side][stage] = {
                k: sum(v[k] for v in values) / len(values) for k in (values[0] if values else {})
            }
    return {
        "formal_score": False,
        "common_denominator": len(eligible),
        "excluded_ids": [p["id"] for p in pairs if not p["common_mappable"]],
        "metrics": metrics,
        "pairs": pairs,
        "generation_correctness": "not scored; manual review needed",
        "limitation": "Flat restored index uses current legacy fallback packer, not old app replay",
    }


STAGES = ("candidate_scores", "reranked_scores", "gated_scores", "packed_scores")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--flat", type=Path, required=True)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    def load(folder):
        report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
        rows = {
            key: json.loads((folder / f"{key}.json").read_text(encoding="utf-8"))
            for key in report["selected_ids"]
        }
        return report, rows

    a, rows_a = load(args.flat)
    b, rows_b = load(args.parent)
    result = compare(a, b, rows_a, rows_b)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != "pairs"}))


if __name__ == "__main__":
    main()
