"""Retry only failed generation using immutable saved context; never retrieve."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

from evaluation.dataset import digest
from evaluation.generation import citation_checks


def recovery_inputs(row):
    if row.get("status") != "error" or row.get("stage") != "generation":
        raise ValueError("Only failed generation may be recovered")
    packed = row.get("packed", {})
    if (
        not packed.get("generation_allowed")
        or not packed.get("context")
        or not packed.get("citations")
    ):
        raise ValueError("Missing approved saved generation inputs")
    return dict(question=row["question"], context=packed["context"], citations=packed["citations"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ids", nargs="+", required=True)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    from app.modules.chat.rag import generation

    report = json.loads((args.source / "report.json").read_text(encoding="utf-8"))
    target = generation.resolve_generation_target(None)
    if report["generation_target"] != f"{target[0]}/{target[1]}":
        parser.error("Generation target changed")
    rows = []
    for key in dict.fromkeys(args.ids):
        if key not in report["selected_ids"]:
            parser.error("Unknown source question")
        row = json.loads((args.source / f"{key}.json").read_text(encoding="utf-8"))
        rows.append((key, row, recovery_inputs(row)))
    if not args.run:
        print(json.dumps({"eligible": [key for key, _, _ in rows], "api_calls": 0}))
        return
    folder = args.output / datetime.now(UTC).strftime("recovery_%Y%m%dT%H%M%S%fZ")
    folder.mkdir(parents=True, exist_ok=False)
    summary = dict(
        source_run=str(args.source),
        source_report_sha256=digest(report),
        generation_target=report["generation_target"],
        attempts=[],
        retrieval_calls=0,
        retries_per_case=0,
        review_status="pending",
    )
    factory = generation.create_chat_client

    def bounded(*a, **kw):
        return factory(*a, **kw).model_copy(update={"request_timeout": 90, "max_retries": 0})

    for key, source_row, inputs in rows:
        result = dict(
            question_id=key,
            source_row_sha256=digest(source_row),
            inputs_sha256=digest(inputs),
            source_error=source_row["error_type"],
            inputs=inputs,
            attempt_count=1,
            generation={"status": "attempted"},
        )
        messages = generation._generation_messages(
            inputs["question"],
            inputs["context"],
            "researcher",
            "analysis",
            None,
            inputs["citations"],
        )
        result["messages_sha256"] = digest([m.model_dump() for m in messages])
        path = folder / f"{key}.json"
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        started = perf_counter()
        try:
            with patch.object(generation, "create_chat_client", bounded):
                answer, model = generation.generate_answer(**inputs)
            result["generation"] = dict(
                status="generated_pending_review",
                answer=answer,
                model=model,
                citation_syntax=citation_checks(answer, len(inputs["citations"])),
            )
        except Exception as exc:
            result["generation"] = dict(status="error", error_type=type(exc).__name__)
        result["seconds"] = perf_counter() - started
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        summary["attempts"].append(
            {
                "question_id": key,
                **{k: v for k, v in result["generation"].items() if k in ("status", "error_type")},
            }
        )
        (folder / "report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(key, result["generation"]["status"], flush=True)
    print(str(folder), flush=True)


if __name__ == "__main__":
    main()
