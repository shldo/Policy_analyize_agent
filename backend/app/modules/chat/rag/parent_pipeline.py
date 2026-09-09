"""Shared post-retrieval pipeline for selected-document and full-corpus search."""

import logging

from app.modules.chat.rag.context_packing import available_context_tokens, pack_generation_context
from app.modules.chat.rag.evidence import (
    assess_evidence_sufficiency,
    max_vector_distance,
    min_reranker_score,
)
from app.modules.chat.rag.parent_resolution import resolve_generation_parents

logger = logging.getLogger(__name__)


def prepare_child_context(question: str, children: list[dict], *, overhead: str = "") -> dict:
    distance, score = max_vector_distance(), min_reranker_score()
    supporting = [
        c
        for c in children
        if float(c.get("distance", 1)) <= distance
        and (c.get("reranker_score") is None or float(c["reranker_score"]) >= score)
    ]
    sufficient, reason = assess_evidence_sufficiency(
        question=question,
        raw_chunks=supporting,
        pages=[],
        has_embeddings=True,
        context="\n\n".join(c["text"] for c in supporting),
    )
    parents = resolve_generation_parents(supporting) if sufficient else []
    packed = pack_generation_context(parents, budget=available_context_tokens(question + overhead))
    if sufficient and not packed["context"]:
        sufficient, reason = False, "Insufficient token budget for complete supporting evidence."
    trace = children[0].get("controlled_trace") if children else None
    if trace:
        trace = dict(trace)
        packed_ids = {c["chunk_id"] for c in packed["citations"]}
        inspection = (trace.get("inspections") or [[]])[-1]
        trace["uncovered_after_packing"] = [
            i["need_index"]
            for i in inspection
            if i["status"] != "supported"
            or not {e["chunk_id"] for e in i["evidence"]} <= packed_ids
        ]
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
        "evidence_reason": reason,
        "used_vector_retrieval": True,
    }
