"""Export allowlisted, reproducible public artifacts; never copy settings or sessions."""

import argparse
import json
from collections import Counter
from pathlib import Path

from evaluation.dataset import digest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "raw", "replay", "audit", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)

    def read(path):
        return json.loads(path.read_text(encoding="utf-8"))

    base = read(a.raw / "report.json")
    counts, verdicts, labels = Counter(), Counter(), Counter()
    entries = []
    for key in base["selected_ids"]:
        source, raw, final, audit = [
            read(root / f"{key}.json") for root in (a.source, a.raw, a.replay, a.audit)
        ]
        counts["drafts"] += bool(raw.get("draft"))
        counts["binding_responses"] += bool(raw.get("binding", {}).get("raw_review"))
        counts["final_answers"] += bool(final["generation"].get("answer"))
        counts["audit_" + audit["status"]] += 1
        if audit["status"] == "reviewed":
            verdicts[audit["review"]["verdict"]] += 1
            labels.update(c["label"] for c in audit["review"]["claims"])
        entry = {
            "question_id": key,
            "question": source["question"],
            "inputs_sha256": raw["inputs_sha256"],
            "messages_sha256": raw["messages_sha256"],
            "raw_artifact_sha256": digest(raw),
            "final_artifact_sha256": digest(final),
            "draft": raw.get("draft"),
            "generation": final["generation"],
            "binding": final.get("binding"),
            "child_citations": source["packed"]["citations"],
            "audit": {
                k: audit[k]
                for k in (
                    "status",
                    "review",
                    "validation_errors",
                    "error_type",
                    "raw_judge_response",
                )
                if k in audit
            },
            "model": raw["model"],
            "human_signoff": False,
        }
        (a.output / f"{key}.json").write_text(
            json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        entries.append({"id": key, "sha256": digest(entry), "audit_status": audit["status"]})
    summary = {
        "counts": dict(counts),
        "structurally_valid_model_verdicts": dict(verdicts),
        "structurally_valid_model_claim_labels": dict(labels),
        "warning": (
            "Model candidate counts, not certified accuracy or faithfulness; "
            "see adjudication notes."
        ),
        "model": base["model"],
        "retrieval_calls": 0,
        "database_snapshot": "not_checked",
        "generation_and_binding_successful_responses": counts["drafts"]
        + counts["binding_responses"],
        "independent_judge_attempts": len(entries) - counts["audit_no_reviewable_answer"],
        "human_signoff": False,
        "entries": entries,
    }
    (a.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {k: v for k, v in summary.items() if k != "entries"}, ensure_ascii=False, indent=2
        )
    )


if __name__ == "__main__":
    main()
