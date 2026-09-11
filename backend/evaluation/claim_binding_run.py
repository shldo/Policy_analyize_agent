"""Frozen-input generation + one Child-only review. No retrieval or gold access."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from app.modules.chat.rag import generation
from app.modules.chat.rag.claim_binding import RUBRIC, review_and_revise
from evaluation.dataset import digest
from evaluation.generation_diagnostic import DEFAULT_IDS, _inputs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--all", action="store_true")
    p.add_argument("--run", action="store_true")
    args = p.parse_args()
    source_report = json.loads((args.source / "report.json").read_text())
    ids = source_report["selected_ids"] if args.all else list(DEFAULT_IDS)
    if not args.run:
        print(json.dumps({"ids": ids, "api_calls": 0}))
        return
    folder = args.output / datetime.now(UTC).strftime("run_%Y%m%dT%H%M%S%fZ")
    folder.mkdir(parents=True, exist_ok=False)
    provider, model, _ = generation.resolve_generation_target(None)
    summary = {
        "model": f"{provider}/{model}",
        "source_report_sha256": digest(source_report),
        "selected_ids": ids,
        "retrieval_calls": 0,
        "database_snapshot": "not_checked",
        "max_calls_per_case": 2,
        "outer_retries": 0,
        "rubric_sha256": digest(RUBRIC),
        "review_method": "model_assisted_not_human",
        "results": [],
    }

    def run(key):
        row = json.loads((args.source / f"{key}.json").read_text(encoding="utf-8"))
        inputs = _inputs(row)
        messages = generation._generation_messages(
            inputs["question"],
            inputs["context"],
            "researcher",
            "analysis",
            None,
            inputs["citations"],
        )
        out = {
            "question_id": key,
            "inputs_sha256": digest(inputs),
            "messages_sha256": digest([m.model_dump() for m in messages]),
            "source_row_sha256": digest(row),
            "model": summary["model"],
        }
        start = perf_counter()
        try:
            client = generation.create_chat_client(provider, model, max_tokens=2048).model_copy(
                update={"request_timeout": 90, "max_retries": 0}
            )
            draft = client.invoke(messages).content
            out["draft"] = draft
            judge = generation.create_chat_client(provider, model, max_tokens=6500).model_copy(
                update={"request_timeout": 120, "max_retries": 0}
            )
            review = review_and_revise(inputs["question"], draft, inputs["citations"], judge)
            out["binding"] = review
            out["generation"] = {
                "status": review["status"],
                "answer": review.get("answer"),
                "model": summary["model"],
            }
        except Exception as exc:
            out["generation"] = {"status": "error", "error_type": type(exc).__name__}
        out["seconds"] = perf_counter() - start
        (folder / f"{key}.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return {
            "question_id": key,
            "status": out["generation"]["status"],
            "removed": len(out.get("binding", {}).get("removed_unit_ids", [])),
        }

    with ThreadPoolExecutor(max_workers=3) as pool:
        for future in as_completed([pool.submit(run, key) for key in ids]):
            result = future.result()
            summary["results"].append(result)
            (folder / "report.json").write_text(
                json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(result, flush=True)
    print(folder, flush=True)


if __name__ == "__main__":
    main()
