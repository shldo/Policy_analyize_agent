"""Observe new draft development cases through real Parent–Child RAG.

Does not approve labels, alter the corpus, or weaken the reviewed benchmark.
Persists every case, including unmapped evidence and provider failures.
"""

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from evaluation.dataset import digest, is_answerable, load_dataset, resolve_groups, score_groups
from evaluation.generation import citation_checks
from evaluation.parent_child import section_snapshot
from evaluation.run import check_pool, snapshot


def draft_cases(cases):
    return [c for c in cases if c["split"] == "development" and c["review_status"] == "draft"]


def evidence_mapping(case, pool):
    if not is_answerable(case):
        return None, "unresolved_candidate_not_scored"
    try:
        return resolve_groups(case, pool), "mapped_draft"
    except ValueError as exc:
        return None, str(exc)


def stage_scores(ids, groups):
    if groups is None:
        return None
    return {key: value for k in (5, 10, 20) for key, value in score_groups(ids, groups, k).items()}


def write_report(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/evaluation/exploratory"))
    parser.add_argument("--run", action="store_true", help="Call configured generation API")
    parser.add_argument("--remaining-from", type=Path, help="Run unfinished cases in a new folder")
    parser.add_argument(
        "--all-development", action="store_true", help="Include reviewed legacy cases unchanged"
    )
    args = parser.parse_args()
    from app.core.config import get_settings
    from app.modules.chat.rag.generation import generate_answer, resolve_generation_target
    from app.modules.chat.rag.parent_pipeline import prepare_child_context
    from app.modules.chat.rag.prompts import get_insufficient_evidence_message
    from app.modules.documents.service import _rerank_or_dense, retrieve_child_candidates
    from app.modules.embedding import service as embedding

    manifest, cases = load_dataset(args.dataset)
    selected = draft_cases(cases)
    if args.all_development:
        selected = [c for c in cases if c["split"] == "development"]
    if not selected:
        parser.error("No draft development cases")
    pool, documents = snapshot()
    check_pool(manifest, pool, documents)
    corpus_hash = digest([pool, documents])
    parent_hash = section_snapshot()
    settings = get_settings()
    provider, model, _ = resolve_generation_target(None)
    if args.remaining_from:
        previous = json.loads((args.remaining_from / "report.json").read_text(encoding="utf-8"))
        if (
            previous["dataset_sha256"] != digest([manifest, cases])
            or previous["corpus_snapshot"] != corpus_hash
            or previous["parent_snapshot"] != parent_hash
            or previous["generation_target"] != f"{provider}/{model}"
        ):
            parser.error("Resume dataset, corpus or model mismatch")
        done = set()
        for key in previous["selected_ids"]:
            path = args.remaining_from / f"{key}.json"
            if path.exists():
                prior = json.loads(path.read_text(encoding="utf-8"))
                if prior["status"] == "completed" and prior["generation"]["status"] in (
                    "generated_pending_review",
                    "gate_refusal_no_api_call",
                ):
                    done.add(key)
        selected = [
            c
            for c in selected
            if c["question_id"] in previous["selected_ids"] and c["question_id"] not in done
        ]
        if not selected:
            parser.error("No unfinished cases")
    folder = args.output / datetime.now(UTC).strftime("draft_%Y%m%dT%H%M%S%fZ")
    folder.mkdir(parents=True, exist_ok=False)
    report = {
        "status": "running",
        "continuation_of": str(args.remaining_from) if args.remaining_from else None,
        "scope": "full-corpus Classic RAG core; no Agent routing or UI",
        "formal_score": False,
        "dataset_sha256": digest([manifest, cases]),
        "corpus_snapshot": corpus_hash,
        "parent_snapshot": parent_hash,
        "source_code_sha256": digest(
            {
                str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for folder in (Path("app"), Path("evaluation"))
                for p in sorted(folder.rglob("*.py"))
            }
        ),
        "generation_target": f"{provider}/{model}",
        "embedding_model": embedding.active_model_id(),
        "candidate_k": settings.child_candidate_k,
        "lexical_candidate_k": settings.child_lexical_candidate_k,
        "rerank_k": settings.child_rerank_k,
        "selected_ids": [c["question_id"] for c in selected],
        "results": [],
        "semantic_review": "pending; citation syntax is not correctness",
        "thresholds": "unchanged",
        "web_search": False,
    }
    write_report(folder / "report.json", report)
    print(f"Output: {folder}; cases={len(selected)}", flush=True)
    for case in selected:
        started = perf_counter()
        groups, mapping = evidence_mapping(case, pool)
        row = {
            "question_id": case["question_id"],
            "question": case["question"],
            "category": case["category"],
            "answerability": case["answerability"],
            "reference_answer": case["reference_answer"],
            "required_answer_points": case["required_answer_points"],
            "mapping_status": mapping,
            "evidence_groups": [sorted(g) for g in groups] if groups else None,
            "status": "running",
            "stage": "retrieval",
            "generation": {"status": "not_run"},
        }
        try:
            if settings.controlled_retrieval_enabled:
                from app.modules.documents.controlled_retrieval import retrieve_controlled

                selected_children, trace = retrieve_controlled(
                    case["question"], limit=settings.child_rerank_k
                )
                row["controlled_trace"] = trace
                candidates = list(
                    {c["chunk_id"]: c for batch in trace["rounds"] for c in batch}.values()
                )
                ranked = [dict(c, controlled_trace=trace) for c in selected_children]
                row["candidate_stage_semantics"] = "union of gated rounds, not raw ANN"
            else:
                candidates = retrieve_child_candidates(
                    case["question"], limit=settings.child_candidate_k
                )
                ranked = _rerank_or_dense(case["question"], candidates, len(candidates))
            row["candidates"] = candidates
            row["candidate_scores"] = stage_scores([c["chunk_id"] for c in candidates], groups)
            row["stage"] = "rerank"
            row["ranked"] = ranked
            row["cross_encoder_used"] = bool(ranked) and all("reranker_score" in c for c in ranked)
            row["reranked_scores"] = stage_scores([c["chunk_id"] for c in ranked], groups)
            row["stage"] = "evidence_and_packing"
            packed = prepare_child_context(case["question"], ranked[: settings.child_rerank_k])
            row["packed"] = packed
            row["gated_scores"] = stage_scores([c["chunk_id"] for c in packed["chunks"]], groups)
            row["packed_scores"] = stage_scores(
                [c["chunk_id"] for c in packed["citations"]], groups
            )
            row["retrieval_seconds"] = perf_counter() - started
            row["stage"] = "generation"
            write_report(folder / f"{case['question_id']}.json", row)
            if not packed["evidence_sufficient"]:
                row["generation"] = {
                    "status": "gate_refusal_no_api_call",
                    "answer": get_insufficient_evidence_message(
                        question=case["question"],
                        reason=packed["evidence_reason"],
                        mode="researcher",
                    ),
                }
            elif args.run:
                generation_started = perf_counter()
                # Only user question and retrieved context reach the model, never gold answers.
                answer, resolved_model = generate_answer(
                    case["question"], packed["context"], citations=packed["citations"]
                )
                row["generation"] = {
                    "status": "generated_pending_review",
                    "answer": answer,
                    "model": resolved_model,
                    "seconds": perf_counter() - generation_started,
                    "citation_syntax": citation_checks(answer, len(packed["citations"])),
                }
            row["status"] = "completed"
        except Exception as exc:
            # Provider error strings may contain credentials or request payloads.
            row.update(status="error", error_type=type(exc).__name__)
        row["seconds"] = perf_counter() - started
        write_report(folder / f"{case['question_id']}.json", row)
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
            f"{len(report['results'])}/{len(selected)} {case['question_id']}: "
            f"{row['status']} / {row['generation']['status']}",
            flush=True,
        )
    report["corpus_unchanged"] = (
        digest(list(snapshot())) == corpus_hash and section_snapshot() == parent_hash
    )
    report["status_counts"] = dict(Counter(r["status"] for r in report["results"]))
    report["status"] = "completed" if report["corpus_unchanged"] else "invalid_corpus_changed"
    write_report(folder / "report.json", report)
    print(f"Finished: {folder / 'report.json'}", flush=True)


if __name__ == "__main__":
    main()
