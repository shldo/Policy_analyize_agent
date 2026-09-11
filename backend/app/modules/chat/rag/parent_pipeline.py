"""Shared post-retrieval pipeline for selected-document and full-corpus search."""

import logging

from app.core.config import get_settings
from app.modules.chat.rag.context_packing import (
    available_context_tokens,
    pack_generation_context,
)
from app.modules.chat.rag.evidence import (
    assess_evidence_sufficiency,
    max_vector_distance,
    min_reranker_score,
)
from app.modules.chat.rag.parent_resolution import resolve_generation_parents
from app.modules.documents.controlled_retrieval import uncovered_facets

logger = logging.getLogger(__name__)


def _prepare_partial_context(question, children, overhead, trace, packing_policy):
    # Relevance ranking already happened. Do not veto BM25 hits using dense distance.
    candidates = [c for c in children if c.get("text", "").strip()]
    parents = resolve_generation_parents(candidates) if candidates else []
    packed = pack_generation_context(
        parents,
        budget=available_context_tokens(question + overhead),
        packing_policy=packing_policy,
    )
    allowed = bool(packed["context"].strip()) and bool(packed["citations"])
    complete = False
    status = "not_assessed" if allowed else "no_context"
    if trace is not None:
        trace = dict(trace)
        missing = uncovered_facets(trace, {c["chunk_id"] for c in packed["citations"]})
        verified = bool(trace.get("inspections")) and trace.get("stop_reason") not in (
            "inspection_or_retrieval_error",
            "time_budget",
        )
        complete = allowed and verified and not missing
        status = "complete" if complete else ("partial" if allowed and verified else status)
        trace.update(
            uncovered_after_packing=missing,
            coverage_sufficient=complete,
            coverage_stage="packed",
            generation_allowed=allowed,
            coverage_status=status,
        )
    reason = (
        None
        if complete
        else "Coverage is not certified. Answer only supported parts and explicitly identify gaps "
        "in the provided context; do not infer absence from the entire corpus."
        if allowed
        else "No usable document evidence fits the available context budget."
    )
    logger.info(
        "partial_answer candidates=%d packed=%d tokens=%d allowed=%s coverage=%s",
        len(candidates),
        len(packed["citations"]),
        packed["packed_token_count"],
        allowed,
        status,
    )
    return {
        **packed,
        "controlled_trace": trace,
        "chunks": candidates,
        "raw_chunks": children,
        "generation_allowed": allowed,
        "coverage_sufficient": complete,
        "coverage_status": status,
        "evidence_sufficient": complete,
        "evidence_reason": reason,
        "used_vector_retrieval": True,
    }


def prepare_child_context(
    question: str,
    children: list[dict],
    *,
    overhead: str = "",
    controlled_trace: dict | None = None,
    packing_policy: str | None = None,
) -> dict:
    # Explicit evaluation overrides take precedence over the application setting.
    if packing_policy is None:
        packing_policy = get_settings().rag_packing_policy
    trace = (
        controlled_trace
        if controlled_trace is not None
        else (children[0].get("controlled_trace") if children else None)
    )
    if get_settings().rag_allow_partial_answers:
        return _prepare_partial_context(question, children, overhead, trace, packing_policy)
    controlled = trace is not None or get_settings().controlled_retrieval_enabled
    distance, score = (
        (max_vector_distance(), min_reranker_score()) if children else (1.0, float("-inf"))
    )
    supporting = [
        c
        for c in children
        if float(c.get("distance", 1)) <= distance
        and (c.get("reranker_score") is None or float(c["reranker_score"]) >= score)
    ]
    if controlled:
        # Similarity thresholds filter candidate eligibility, never certify semantic coverage.
        sufficient, reason = bool(supporting) and bool(trace), None
    else:
        sufficient, reason = assess_evidence_sufficiency(
            question=question,
            raw_chunks=supporting,
            pages=[],
            has_embeddings=True,
            context="\n\n".join(c["text"] for c in supporting),
        )
    parents = resolve_generation_parents(supporting) if sufficient else []
    if controlled:
        priority = {c["chunk_id"]: i for i, c in enumerate(supporting)}
        parents.sort(
            key=lambda p: min(
                (priority.get(c["chunk_id"], len(priority)) for c in p["supporting_children"]),
                default=len(priority),
            )
        )
    packing_options = {"preserve_order": True} if controlled else {}
    packed = pack_generation_context(
        parents,
        budget=available_context_tokens(question + overhead),
        packing_policy=packing_policy,
        **packing_options,
    )
    if sufficient and not packed["context"]:
        sufficient, reason = False, "Insufficient token budget for complete supporting evidence."
    if controlled:
        trace = dict(trace or {})
        packed_ids = {c["chunk_id"] for c in packed["citations"]}
        trace["uncovered_after_packing"] = uncovered_facets(trace, packed_ids)
        sufficient = bool(packed["context"]) and not trace["uncovered_after_packing"]
        if trace.get("stop_reason") in ("inspection_or_retrieval_error", "time_budget"):
            sufficient = False
        trace["retrieval_stop_reason"] = trace.get("stop_reason")
        if not sufficient and trace.get("stop_reason") == "coverage_sufficient":
            trace["stop_reason"] = "packed_coverage_incomplete"
        trace.update(coverage_sufficient=sufficient, coverage_stage="packed")
        reason = (
            None
            if sufficient
            else (
                "The available evidence does not completely support all required facets; "
                "generation was stopped without inferring absence from the full corpus."
            )
        )
    coverage_status = "not_assessed"
    if controlled:
        coverage_status = (
            "complete" if sufficient else ("partial" if packed["context"] else "no_context")
        )
    elif not packed["context"]:
        coverage_status = "no_context"
    logger.info(
        "child_context reranked=%d evidence_passed=%d resolved=%s packed=%d tokens=%d",
        len(children),
        len(supporting),
        [(p["context_id"], p["parent_score"]) for p in parents],
        len(packed["generation_parents"]),
        packed["packed_token_count"],
    )
    return {
        **packed,
        "controlled_trace": trace,
        "chunks": supporting,
        "raw_chunks": children,
        "evidence_sufficient": sufficient,
        "generation_allowed": sufficient,
        "coverage_status": coverage_status,
        "coverage_sufficient": coverage_status == "complete",
        "evidence_reason": reason,
        "used_vector_retrieval": True,
    }
