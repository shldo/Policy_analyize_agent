"""Replay Child selection and packing from a saved run without model calls.

The source run supplies the already-computed candidate and reranker records.
This script applies one named deterministic selector, then uses the public
Parent resolution and token packing path.  It never changes the source run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

from evaluation.dataset import digest
from evaluation.exploratory_parent_child import stage_scores, write_report
from evaluation.parent_child import section_snapshot
from evaluation.run import snapshot


def _score_groups(groups: list[list[str]] | None) -> list[set[str]]:
    """Use the source row's exact groups so replay shares the baseline scorer."""

    return [set(group) for group in groups or []]


def _loss_row(row: dict, selected_ids: list[str], packed_ids: list[str]) -> dict:
    candidate_ids = [child["chunk_id"] for child in row.get("candidates", [])]
    selected_set = set(selected_ids)
    packed_set = set(packed_ids)
    return {
        "question_id": row["question_id"],
        "candidate_count": len(candidate_ids),
        "candidate_ids": candidate_ids,
        "selected_ids": selected_ids,
        "selected_not_packed_ids": [
            chunk_id for chunk_id in selected_ids if chunk_id not in packed_set
        ],
        "packed_ids": packed_ids,
        "candidate_not_selected_count": len(set(candidate_ids) - selected_set),
        "selected_not_packed_count": len(selected_set - packed_set),
        "packed_token_count": row["packed"]["packed_token_count"],
    }


def _configuration_differences(source: dict, replay: dict) -> dict:
    fields = (
        "selection_strategy",
        "packing_policy",
        "context_tokens",
        "parent_context_k",
        "max_parents_per_document",
        "tokenizer_sha256",
        "allow_partial_answers",
        "strict_comparison",
        "candidate_k",
        "lexical_candidate_k",
        "rerank_k",
    )
    differences = {}
    for field in fields:
        source_value = source.get(field)
        replay_value = replay.get(field)
        if source_value != replay_value:
            differences[field] = {"source": source_value, "replay": replay_value}
    return differences


def _replay_summary(rows: list[dict], *, context_tokens: int) -> dict:
    scored = [row for row in rows if row.get("packed_scores")]
    reason_counts = Counter(
        item.get("reason")
        for row in rows
        for item in row.get("packed", {}).get("packing_trace", [])
        if item.get("reason")
    )
    recovered = []
    regressed = []
    for row in scored:
        before = row.get("baseline_packed_scores") or {}
        after = row["packed_scores"]
        before_complete = before.get("all_evidence_at_20")
        after_complete = after.get("all_evidence_at_20")
        before_egc = before.get("evidence_group_coverage_at_20")
        after_egc = after.get("evidence_group_coverage_at_20")
        if before_complete != after_complete or before_egc != after_egc:
            (
                recovered
                if (after_complete or 0, after_egc or 0) > (before_complete or 0, before_egc or 0)
                else regressed
            ).append(
                {
                    "question_id": row["question_id"],
                    "before_complete_at_20": before_complete,
                    "after_complete_at_20": after_complete,
                    "before_egc_at_20": before_egc,
                    "after_egc_at_20": after_egc,
                }
            )
    packed_token_counts = [row["packed"]["packed_token_count"] for row in rows]
    scored_token_counts = [row["packed"]["packed_token_count"] for row in scored]
    expanded_parent_count = sum(row["packed"].get("expanded_parent_count", 0) for row in rows)
    child_only_parent_count = sum(row["packed"].get("child_only_parent_count", 0) for row in rows)
    scored_expanded_parent_count = sum(
        row["packed"].get("expanded_parent_count", 0) for row in scored
    )
    scored_child_only_parent_count = sum(
        row["packed"].get("child_only_parent_count", 0) for row in scored
    )
    duplicate_child_count = 0
    selected_not_packed_count = 0
    for row in rows:
        packed_ids = [citation.get("chunk_id") for citation in row["packed"]["citations"]]
        duplicate_child_count += len(packed_ids) - len(set(packed_ids))
        selected_not_packed_count += row["loss_table"]["selected_not_packed_count"]
    return {
        "scored": len(scored),
        "total_cases": len(rows),
        "complete_at_5": sum(row["packed_scores"]["all_evidence_at_5"] for row in scored),
        "complete_at_20": sum(row["packed_scores"]["all_evidence_at_20"] for row in scored),
        "macro_egc_at_5": mean(
            row["packed_scores"]["evidence_group_coverage_at_5"] for row in scored
        )
        if scored
        else None,
        "macro_egc_at_20": mean(
            row["packed_scores"]["evidence_group_coverage_at_20"] for row in scored
        )
        if scored
        else None,
        "recovered_vs_source": recovered,
        "regressed_vs_source": regressed,
        "packing_reason_counts": dict(reason_counts),
        "selected_to_packed_loss_count": selected_not_packed_count,
        "duplicate_packed_child_count": duplicate_child_count,
        "over_budget_count": sum(
            row["packed"]["packed_token_count"] > context_tokens for row in rows
        ),
        "average_packed_tokens": mean(packed_token_counts) if packed_token_counts else None,
        "max_packed_tokens": max(packed_token_counts) if packed_token_counts else None,
        "average_packed_tokens_all_cases": mean(packed_token_counts)
        if packed_token_counts
        else None,
        "average_packed_tokens_scored_cases": mean(scored_token_counts)
        if scored_token_counts
        else None,
        "max_packed_tokens_all_cases": max(packed_token_counts) if packed_token_counts else None,
        "max_packed_tokens_scored_cases": max(scored_token_counts) if scored_token_counts else None,
        "expanded_parent_count_all_cases": expanded_parent_count,
        "child_only_parent_count_all_cases": child_only_parent_count,
        "expanded_parent_count_scored_cases": scored_expanded_parent_count,
        "child_only_parent_count_scored_cases": scored_child_only_parent_count,
        "generation_calls": 0,
        "semantic_correctness": "not scored; offline selection and packing only",
        "error_types": dict(
            Counter(row.get("error_type") for row in rows if row["status"] == "error")
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/evaluation/selection_replay"))
    from app.modules.chat.rag.context_packing import PACKING_POLICIES
    from app.modules.documents.child_selection import SELECTION_STRATEGIES

    parser.add_argument(
        "--selection-strategy",
        choices=SELECTION_STRATEGIES,
        default="reranker_top_k",
    )
    parser.add_argument(
        "--packing-policy",
        choices=PACKING_POLICIES,
        default="original",
    )
    args = parser.parse_args()

    from app.core.config import get_settings, resolve_backend_path
    from app.modules.chat.rag.parent_pipeline import prepare_child_context
    from app.modules.documents.child_selection import rerank_limit_for_selection, select_children

    settings = get_settings()
    try:
        rerank_limit_for_selection(
            args.selection_strategy,
            selection_limit=settings.child_rerank_k,
            inspection_pool_k=settings.child_selection_pool_k,
        )
    except ValueError as exc:
        parser.error(str(exc))
    source = json.loads((args.source / "report.json").read_text(encoding="utf-8"))
    if source["status"] != "completed":
        parser.error("Source run must be complete")
    if source.get("corpus_unchanged") is not True:
        parser.error("Source run must explicitly set corpus_unchanged=true")
    corpus = digest(list(snapshot()))
    parents = section_snapshot()
    if corpus != source["corpus_snapshot"] or parents != source["parent_snapshot"]:
        parser.error("Source corpus or Parent snapshot changed")

    folder = args.output / datetime.now(UTC).strftime("selection_%Y%m%dT%H%M%S%fZ")
    folder.mkdir(parents=True, exist_ok=False)
    tokenizer_sha256 = hashlib.sha256(
        resolve_backend_path(settings.rag_tokenizer_path).read_bytes()
    ).hexdigest()
    replay_config = {
        "selection_strategy": args.selection_strategy,
        "packing_policy": args.packing_policy,
        "context_tokens": settings.rag_max_context_tokens,
        "parent_context_k": settings.parent_context_k,
        "max_parents_per_document": settings.max_parents_per_document,
        "tokenizer_sha256": tokenizer_sha256,
        "allow_partial_answers": settings.rag_allow_partial_answers,
        "strict_comparison": source.get("strict_comparison"),
        "candidate_k": source.get("candidate_k"),
        "lexical_candidate_k": source.get("lexical_candidate_k"),
        "rerank_k": settings.child_rerank_k,
    }
    report = {
        "status": "preparing",
        "formal_score": False,
        "variant": "deterministic_selection_offline_replay",
        "source_report": str(args.source),
        "source_report_sha256": digest(source),
        "dataset_sha256": source["dataset_sha256"],
        "corpus_snapshot": corpus,
        "parent_snapshot": parents,
        "generation_target": source["generation_target"],
        "embedding_model": source.get("embedding_model"),
        "reranker_model": source.get("reranker_model"),
        "candidate_k": source.get("candidate_k"),
        "lexical_candidate_k": source.get("lexical_candidate_k"),
        "rrf_rank_constant": source.get("rrf_rank_constant"),
        "rerank_k": settings.child_rerank_k,
        "selection_pool_k": settings.child_selection_pool_k,
        "selection_strategy": args.selection_strategy,
        "packing_policy": args.packing_policy,
        "context_tokens": settings.rag_max_context_tokens,
        "parent_context_k": settings.parent_context_k,
        "max_parents_per_document": settings.max_parents_per_document,
        "tokenizer_sha256": tokenizer_sha256,
        "replay_config": replay_config,
        "configuration_differences": _configuration_differences(source, replay_config),
        "source_corpus_unchanged": True,
        "selected_ids": source["selected_ids"],
        "results": [],
        "corpus_unchanged": None,
        "source_code_sha256": digest(
            {
                str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for root in (Path("app"), Path("evaluation"))
                for path in sorted(root.rglob("*.py"))
            }
        ),
    }
    write_report(folder / "report.json", report)

    rows = []
    loss_table = []
    for question_id in report["selected_ids"]:
        source_row = json.loads((args.source / f"{question_id}.json").read_text(encoding="utf-8"))
        ranked = source_row.get("ranked") or []
        selected, selection_trace = select_children(
            ranked,
            strategy=args.selection_strategy,
            limit=settings.child_rerank_k,
            inspection_pool_k=settings.child_selection_pool_k,
        )
        packed = prepare_child_context(
            source_row["question"],
            selected,
            packing_policy=args.packing_policy,
        )
        groups = _score_groups(source_row.get("evidence_groups"))
        row = {
            "question_id": question_id,
            "question": source_row["question"],
            "category": source_row.get("category"),
            "mapping_status": source_row.get("mapping_status"),
            "evidence_groups": source_row.get("evidence_groups"),
            "candidate_count": len(source_row.get("candidates") or []),
            "ranked_count": len(ranked),
            "selected_child_ids": [child["chunk_id"] for child in selected],
            "selection_trace": selection_trace,
            "packed": packed,
            "baseline_packed_scores": source_row.get("packed_scores"),
            "selected_scores": stage_scores(
                [child["chunk_id"] for child in selected], groups or None
            ),
            "packed_scores": stage_scores(
                [child["chunk_id"] for child in packed["citations"]], groups or None
            ),
            "status": "completed",
        }
        row["loss_table"] = _loss_row(
            {
                "question_id": question_id,
                "candidates": source_row.get("candidates"),
                "packed": packed,
            },
            row["selected_child_ids"],
            [citation["chunk_id"] for citation in packed["citations"]],
        )
        write_report(folder / f"{question_id}.json", row)
        rows.append(row)
        loss_table.append(row["loss_table"])

    report["loss_table"] = loss_table
    report["summary"] = _replay_summary(rows, context_tokens=settings.rag_max_context_tokens)
    report["corpus_unchanged"] = (
        digest(list(snapshot())) == corpus and section_snapshot() == parents
    )
    report["status"] = "completed" if report["corpus_unchanged"] else "invalid_snapshot"
    write_report(folder / "report.json", report)
    print(json.dumps({"output": str(folder), **report["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
