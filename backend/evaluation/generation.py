"""Collect development answers for human review; no automatic semantic scoring."""

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from evaluation.dataset import digest, load_dataset
from evaluation.prompt_variants import apply_variant
from evaluation.run import check_pool, snapshot


def build_packets(manifest, cases, retrieval, pool):
    if retrieval.get("split") != "development" or retrieval.get("mode") != "retrieval":
        raise ValueError("Generation pilot requires a development retrieval report")
    if retrieval.get("dataset_sha256") != digest({"manifest": manifest, "cases": cases}):
        raise ValueError("Dataset differs from retrieval report")
    by_id = {str(row["id"]): row for row in pool}
    questions = {c["question_id"]: c for c in cases if c["split"] == "development"}
    packets, seen = [], set()
    for result in retrieval["results"]:
        key = result["question_id"]
        if key not in questions or key in seen:
            raise ValueError("Unexpected or duplicate question")
        seen.add(key)
        case = questions[key]
        if case["review_status"] != "reviewed" or case["answerability"] != "answerable":
            raise ValueError("Generation pilot needs reviewed answerable references")
        ids = result["rerank_ids"][:5]
        if not ids or len(set(ids)) != len(ids) or any(key not in by_id for key in ids):
            raise ValueError("Invalid retrieved context IDs")
        sources = [
            {
                "chunk_id": key,
                "file": by_id[key]["original_filename"],
                "page_start": by_id[key]["page_start"],
                "page_end": by_id[key]["page_end"],
                "text": by_id[key]["text"],
            }
            for key in ids
        ]
        packets.append(
            {
                "question_id": case["question_id"],
                "request": {"question": case["question"], "sources": sources},
                "review_only": {
                    "reference_answer": case["reference_answer"],
                    "required_answer_points": case["required_answer_points"],
                    "reference_answer_checks": case["reference_answer_checks"],
                    "evidence_groups": case["evidence_groups"],
                    "semantic_review_status": "pending",
                },
            }
        )
    return packets


def citation_checks(answer, source_count):
    """Syntax/range only: a valid citation number does not prove support."""
    markers = [int(value) for value in re.findall(r"\[(\d+)\]", answer)]
    return {
        "markers": markers,
        "invalid_markers": sorted({n for n in markers if not 1 <= n <= source_count}),
        "has_numbered_citation": bool(markers),
        "semantic_support": "not_scored_requires_review",
    }


def select_packets(packets, offset, limit):
    if offset < 0 or limit < 1 or offset >= len(packets):
        raise ValueError("Invalid or empty generation selection")
    return sorted(packets, key=lambda p: p["question_id"])[offset : offset + limit]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retrieval-report", type=Path, required=True)
    parser.add_argument(
        "--dataset", type=Path, default=Path(__file__).parent / "datasets/policy-v4"
    )
    parser.add_argument("--output", type=Path, default=Path("data/evaluation"))
    parser.add_argument(
        "--run", action="store_true", help="Call configured provider; incurs API usage"
    )
    parser.add_argument(
        "--limit", type=int, default=3, help="First N development cases, fixed ID order"
    )
    parser.add_argument("--code-version", required=True)
    parser.add_argument(
        "--prompt-variant", choices=["baseline", "completeness-v1"], default="baseline"
    )
    parser.add_argument(
        "--offset", type=int, default=0, help="Skip N IDs without calling the model"
    )
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")
    manifest, cases = load_dataset(args.dataset)
    retrieval = json.loads(args.retrieval_report.read_text(encoding="utf-8"))
    pool, documents = snapshot()
    check_pool(manifest, pool, documents)
    snapshot_hash = digest([pool, documents])
    if snapshot_hash != retrieval["corpus_snapshot_sha256"]:
        raise ValueError("Corpus differs from retrieval report")
    packets = sorted(
        build_packets(manifest, cases, retrieval, pool), key=lambda p: p["question_id"]
    )
    selected = select_packets(packets, args.offset, args.limit)
    report = {
        "created_at": datetime.now(UTC).isoformat(),
        "code_version": args.code_version,
        "retrieval_report_sha256": digest(retrieval),
        "dataset_sha256": retrieval["dataset_sha256"],
        "corpus_snapshot_sha256": snapshot_hash,
        "scope": "development fixed retrieved-context generation; not full agent end-to-end",
        "selection": {
            "order": "question_id",
            "offset": args.offset,
            "limit": args.limit,
            "selected_ids": [p["question_id"] for p in selected],
        },
        "status": "running" if args.run else "prepared_no_api_calls",
        "semantic_scores": None,
        "prompt_variant": args.prompt_variant,
        "results": [],
    }
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / datetime.now(UTC).strftime("generation_%Y%m%dT%H%M%S%fZ.json")
    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    if args.run:
        from app.modules.chat.rag.generation import (
            _generation_messages,
            create_chat_client,
            format_context,
            resolve_generation_target,
        )

        provider, model, _ = resolve_generation_target(None)
        client = create_chat_client(provider, model, max_tokens=1200).model_copy(
            update={"request_timeout": 90.0, "max_retries": 0}
        )
        report["config"] = {
            "provider": provider,
            "model": model,
            "max_tokens": 1200,
            "temperature": 0,
            "response_mode": "policymaker",
            "answer_mode": "analysis",
            "timeout_seconds": 90,
            "max_retries": 0,
            "web_search": False,
        }
    for packet in selected:
        if args.run:
            sources = packet["request"]["sources"]
            context, truncated = format_context(sources)
            if truncated:
                raise ValueError("Context truncated; review context budget before execution")
            citations = [{"title": s["file"], "page": s["page_start"]} for s in sources]
            messages = _generation_messages(
                packet["request"]["question"], context, "policymaker", "analysis", None, citations
            )
            messages[0] = messages[0].model_copy(
                update={"content": apply_variant(messages[0].content, args.prompt_variant)}
            )
            packet["messages_sent"] = [{"type": m.type, "content": m.content} for m in messages]
            start = perf_counter()
            try:
                response = client.invoke(messages)
                packet["answer"] = response.content
                packet["usage"] = response.usage_metadata
                packet["finish_reason"] = response.response_metadata.get("finish_reason")
                packet["citation_syntax"] = citation_checks(str(response.content), len(sources))
                packet["status"] = "generated_pending_review"
            except Exception as exc:
                packet["status"] = "failed"
                packet["error_type"] = type(exc).__name__
            packet["seconds"] = perf_counter() - start
        report["results"].append(packet)
        report["status"] = "partial" if args.run else "prepared_no_api_calls"
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        print(f"Saved {packet['question_id']}", flush=True)
        if packet.get("status") == "failed":
            break
    if digest(list(snapshot())) != snapshot_hash:
        report["status"] = "invalid_corpus_changed"
    elif args.run:
        report["status"] = (
            "failed"
            if any(p.get("status") == "failed" for p in report["results"])
            else "collected_pending_review"
        )
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {"report": str(path), "status": report["status"], "count": len(report["results"])}
        )
    )


if __name__ == "__main__":
    main()
