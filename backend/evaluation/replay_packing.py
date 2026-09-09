"""Replay saved candidates with D packing; no new retrieval, indexing or gold input."""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from evaluation.dataset import digest
from evaluation.exploratory_parent_child import stage_scores, write_report
from evaluation.generation import citation_checks
from evaluation.parent_child import section_snapshot
from evaluation.run import snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/evaluation/packing_d"))
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    from app.core.config import get_settings, resolve_backend_path
    from app.modules.chat.rag.generation import (
        _generation_messages,
        create_chat_client,
        resolve_generation_target,
    )
    from app.modules.chat.rag.parent_pipeline import prepare_child_context

    settings = get_settings()
    source = json.loads((args.source / "report.json").read_text(encoding="utf-8"))
    if source["status"] != "completed" or not source["corpus_unchanged"]:
        parser.error("Source run must be complete and valid")
    corpus = digest(list(snapshot()))
    parents = section_snapshot()
    if corpus != source["corpus_snapshot"] or parents != source["parent_snapshot"]:
        parser.error("Source corpus or parents changed")
    provider, model, _ = resolve_generation_target(None)
    if f"{provider}/{model}" != source["generation_target"]:
        parser.error("Generation model changed")
    folder = args.output / datetime.now(UTC).strftime("D_%Y%m%dT%H%M%S%fZ")
    folder.mkdir(parents=True, exist_ok=False)
    report = {
        **source,
        "status": "preparing",
        "corpus_unchanged": None,
        "results": [],
        "variant": "D",
        "source_report": str(args.source),
        "source_report_sha256": digest(source),
        "config": {
            "budget": settings.rag_max_context_tokens,
            "max_blocks": settings.parent_context_k,
            "per_document": settings.max_parents_per_document,
            "tokenizer_sha256": hashlib.sha256(
                resolve_backend_path(settings.rag_tokenizer_path).read_bytes()
            ).hexdigest(),
        },
        "source_code_sha256": digest(
            {
                str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for root in (Path("app"), Path("evaluation"))
                for p in sorted(root.rglob("*.py"))
            }
        ),
    }
    rows = []
    for key in source["selected_ids"]:
        row = json.loads((args.source / f"{key}.json").read_text(encoding="utf-8"))
        old_packed = row["packed"]
        packed = prepare_child_context(row["question"], row["ranked"][: settings.child_rerank_k])
        groups = [set(g) for g in row["evidence_groups"]] if row["evidence_groups"] else None
        row.update(
            packed=packed,
            packed_scores=stage_scores([c["chunk_id"] for c in packed["citations"]], groups),
            generation={"status": "not_run"},
            status="prepared",
            baseline_packed_scores=row["packed_scores"],
            baseline_context_bytes=len(old_packed["context"].encode("utf-8")),
        )
        row.pop("seconds", None)
        row["retrieval_seconds"] = 0
        assert packed["packed_token_count"] <= settings.rag_max_context_tokens
        # Check complete prompt before making any API calls.
        if packed["evidence_sufficient"]:
            _generation_messages(
                row["question"],
                packed["context"],
                "researcher",
                "analysis",
                None,
                packed["citations"],
            )
        write_report(folder / f"{key}.json", row)
        rows.append(row)
    report["status"] = "generating" if args.run else "prepared_no_api_calls"
    write_report(folder / "report.json", report)
    print(f"Prepared {len(rows)} cases: {folder}", flush=True)
    for row in rows:
        started = perf_counter()
        try:
            if args.run and row["packed"]["evidence_sufficient"]:
                messages = _generation_messages(
                    row["question"],
                    row["packed"]["context"],
                    "researcher",
                    "analysis",
                    None,
                    row["packed"]["citations"],
                )
                response = create_chat_client(
                    provider, model, max_tokens=settings.rag_reserved_output_tokens
                ).invoke(messages)
                answer = str(response.content)
                row["generation"] = {
                    "status": "generated_pending_review",
                    "answer": answer,
                    "model": f"{provider}/{model}",
                    "seconds": perf_counter() - started,
                    "usage": response.usage_metadata,
                    "finish_reason": response.response_metadata.get("finish_reason"),
                    "citation_syntax": citation_checks(answer, len(row["packed"]["citations"])),
                }
            row["status"] = "completed" if args.run else "prepared"
        except Exception as exc:
            row.update(status="error", error_type=type(exc).__name__)
        row["seconds"] = perf_counter() - started
        write_report(folder / f"{row['question_id']}.json", row)
        report["results"].append(
            {
                k: row.get(k)
                for k in (
                    "question_id",
                    "category",
                    "status",
                    "mapping_status",
                    "reranked_scores",
                    "packed_scores",
                )
            }
        )
        write_report(folder / "report.json", report)
        print(
            f"{len(report['results'])}/{len(rows)} {row['question_id']}: {row['status']}",
            flush=True,
        )
    report["corpus_unchanged"] = (
        digest(list(snapshot())) == corpus and section_snapshot() == parents
    )
    report["status"] = "completed" if args.run and report["corpus_unchanged"] else "prepared"
    write_report(folder / "report.json", report)


if __name__ == "__main__":
    main()
