"""Run the fixed generation-only closeout diagnostic on saved C inputs.

This command deliberately reads only question/context/citations from an
existing retrieval run.  It never retrieves, reads gold/review fields, or
retries a generation call.  Use ``--run`` explicitly to spend model budget.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

from evaluation.dataset import digest

DEFAULT_IDS = (
    "DEV2-UN02",
    "DEV2-UN05",
    "DEV2-UN06",
    "DEV2-MC06",
    "DEV2-MO05",
    "DEV2-CS07",
    "DEV2-MC01",
    "DEV2-CS06",
)


def _inputs(row: dict) -> dict:
    packed = row.get("packed") or {}
    if not packed.get("context") or not packed.get("citations"):
        raise ValueError("saved row does not contain usable generation inputs")
    return {
        "question": row["question"],
        "context": packed["context"],
        "citations": packed["citations"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ids", nargs="+", default=list(DEFAULT_IDS))
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    report = json.loads((args.source / "report.json").read_text(encoding="utf-8"))
    source_ids = set(report.get("selected_ids", []))
    rows = []
    for question_id in dict.fromkeys(args.ids):
        if question_id not in source_ids:
            parser.error(f"unknown source question: {question_id}")
        row = json.loads((args.source / f"{question_id}.json").read_text(encoding="utf-8"))
        inputs = _inputs(row)
        rows.append((question_id, row, inputs))

    if not args.run:
        print(json.dumps({"eligible": [key for key, _, _ in rows], "api_calls": 0}))
        return

    from app.modules.chat.rag import generation

    provider, model, _ = generation.resolve_generation_target(None)
    folder = args.output / datetime.now(UTC).strftime("diagnostic_%Y%m%dT%H%M%S%fZ")
    folder.mkdir(parents=True, exist_ok=False)
    summary = {
        "source_run": str(args.source),
        "source_report_sha256": digest(report),
        "generation_target": f"{provider}/{model}",
        "prompt_version": "closeout-b-v1",
        "retrieval_calls": 0,
        "max_calls_per_case": 1,
        "outer_retries": 0,
        "results": [],
        "review_status": "pending",
    }
    factory = generation.create_chat_client

    def bounded(*call_args, **kwargs):
        return factory(*call_args, **kwargs).model_copy(
            update={"request_timeout": 90, "max_retries": 0}
        )

    for question_id, source_row, inputs in rows:
        messages = generation._generation_messages(
            inputs["question"],
            inputs["context"],
            "researcher",
            "analysis",
            None,
            inputs["citations"],
        )
        result = {
            "question_id": question_id,
            "source_row_sha256": digest(source_row),
            "inputs_sha256": digest(inputs),
            "context_sha256": digest(inputs["context"]),
            "citations_sha256": digest(inputs["citations"]),
            "messages_sha256": digest([message.model_dump() for message in messages]),
            "attempt_count": 1,
            "model": f"{provider}/{model}",
            "generation": {"status": "attempted"},
        }
        started = perf_counter()
        try:
            with patch.object(generation, "create_chat_client", bounded):
                answer, resolved_model = generation.generate_answer(**inputs)
            citation_validation = generation.validate_answer_citations(answer, inputs["citations"])
            result["generation"] = {
                "status": "generated_pending_review",
                "answer": answer,
                "model": resolved_model,
                "citation_validation": citation_validation,
            }
        except Exception as exc:
            result["generation"] = {
                "status": "error",
                "error_type": type(exc).__name__,
            }
        result["seconds"] = perf_counter() - started
        (folder / f"{question_id}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summary["results"].append(
            {
                "question_id": question_id,
                "status": result["generation"]["status"],
                "error_type": result["generation"].get("error_type"),
            }
        )
        (folder / "report.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(question_id, result["generation"]["status"], flush=True)

    print(folder, flush=True)


if __name__ == "__main__":
    main()
