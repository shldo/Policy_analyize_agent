"""Re-render saved semantic reviews; no model calls or modification of old runs."""

import argparse
import json
import re
from pathlib import Path

from app.modules.chat.rag.claim_binding import apply_review, child_sources, units_for
from evaluation.dataset import digest
from evaluation.generation_diagnostic import _inputs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report = json.loads((args.run / "report.json").read_text(encoding="utf-8"))
    summary = {"source_run": str(args.run), "api_calls": 0, "results": []}
    for key in report["selected_ids"]:
        row = json.loads((args.run / f"{key}.json").read_text(encoding="utf-8"))
        source = json.loads((args.source / f"{key}.json").read_text(encoding="utf-8"))
        if row["inputs_sha256"] != digest(_inputs(source)):
            raise ValueError("Input hash mismatch")
        out = {**row, "original_artifact_sha256": digest(row)}
        try:
            raw = row["binding"]["raw_review"]
            parsed = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip()))
            revised = apply_review(
                units_for(row["draft"]), child_sources(source["packed"]["citations"]), parsed
            )
            out["binding"] = {"status": "reviewed", "raw_review": raw, **revised}
            out["generation"] = {
                "status": "reviewed",
                "answer": revised["answer"],
                "model": row["model"],
            }
        except (KeyError, ValueError, TypeError) as exc:
            out["generation"] = {"status": "needs_adjudication", "error": str(exc)}
        (args.output / f"{key}.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summary["results"].append({"question_id": key, "status": out["generation"]["status"]})
    (args.output / "report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
