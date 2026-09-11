"""Deterministic selection of reranked Child evidence for the Parent pipeline.

The reranker and the upstream hybrid candidate pool remain unchanged here.  The
selector only decides which already-ranked Children enter the existing Parent
resolution and token packing stages.  It deliberately does not certify semantic
coverage; that remains the responsibility of the downstream evidence contract.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from math import isfinite

logger = logging.getLogger(__name__)

# Keep a small, explicit experimental policy.  The weights below are selection
# weights only, not evidence thresholds or the upstream RRF rank constant.
RERANK_RRF_RERANK_WEIGHT = 0.25
TOP_K_SELECTION_STRATEGY = "reranker_top_k"
RRF_SELECTION_STRATEGY = "reranker_rrf_reciprocal_rank_v1"
PROTECTED_RRF_BACKFILL_STRATEGY = "reranker_protected_rrf_backfill_v1"
PROTECTED_RRF_HEAD_K = 6
SELECTION_STRATEGIES = (
    TOP_K_SELECTION_STRATEGY,
    RRF_SELECTION_STRATEGY,
    PROTECTED_RRF_BACKFILL_STRATEGY,
)


def _structure_unit(child: dict) -> str | None:
    """Return a stable structural identity for audit output only.

    Section/parent quotas belong to the later packing stage.  The protected
    backfill policy uses this only as a soft diversity preference; a Child
    supporting multiple obligations is not silently removed merely for sharing
    a section.
    """

    section_id = child.get("section_id")
    if section_id:
        return str(section_id)
    path = child.get("section_path")
    if path:
        return "/".join(str(part) for part in path)
    return None


def rerank_limit_for_selection(
    strategy: str, *, selection_limit: int, inspection_pool_k: int
) -> int:
    """Return the reranker output size required by a named selector."""

    if selection_limit < 1:
        raise ValueError("selection limit must be positive")
    if strategy == TOP_K_SELECTION_STRATEGY:
        return selection_limit
    if strategy in (RRF_SELECTION_STRATEGY, PROTECTED_RRF_BACKFILL_STRATEGY):
        if inspection_pool_k < selection_limit:
            raise ValueError("child_selection_pool_k must cover child_rerank_k")
        return inspection_pool_k
    raise ValueError(f"Unknown child selection strategy: {strategy}")


def _rrf_order(pool: list[dict]) -> list[dict]:
    """Order a pool by the existing RRF score, with a stable fallback.

    Saved and live hybrid candidates normally carry the upstream ``rrf_score``.
    This function only orders that existing score; it does not recompute RRF or
    apply the upstream rank constant.  If a caller
    supplies a legacy dense-only list without that field, falling back to the
    incoming order preserves the old behavior rather than inventing a score.
    """

    if not pool or not any("rrf_score" in child for child in pool):
        return list(pool)

    def key(item: tuple[int, dict]) -> tuple[float, int, str]:
        index, child = item
        score = child.get("rrf_score")
        try:
            value = float(score)
        except (TypeError, ValueError):
            value = float("-inf")
        if not isfinite(value):
            value = float("-inf")
        return (-value, index, str(child.get("chunk_id", "")))

    return [child for _, child in sorted(enumerate(pool), key=key)]


def select_ranked_children(
    ranked_children: Sequence[dict],
    *,
    limit: int,
    inspection_pool_k: int,
) -> tuple[list[dict], dict]:
    """Select at most ``limit`` Children from an independent inspection pool.

    The selection score is a reciprocal-rank blend: the incoming reranker rank
    supplies 25% and the existing RRF rank supplies 75%.  RRF can therefore
    retain a candidate that the cross-encoder placed below the old Top-8 when
    the two retrieval channels agreed on it.  No document text, gold evidence,
    question ID, or question-specific rule is consulted.

    The returned audit record contains only IDs, ranks, structural identifiers,
    and reasons.  It is suitable for replay reports and does not include source
    document text.
    """

    if limit < 1:
        raise ValueError("selection limit must be positive")
    if inspection_pool_k < 1:
        raise ValueError("inspection_pool_k must be positive")

    unique: list[dict] = []
    invalid_decisions: list[dict] = []
    duplicate_decisions: list[dict] = []
    seen_ids: set[object] = set()
    for incoming_rank, child in enumerate(ranked_children, start=1):
        chunk_id = child.get("chunk_id")
        if not chunk_id:
            invalid_decisions.append(
                {
                    "chunk_id": chunk_id,
                    "incoming_rank": incoming_rank,
                    "selected": False,
                    "reason": "invalid_child_id",
                    "structure_unit": _structure_unit(child),
                }
            )
            continue
        dedupe_key = chunk_id
        if dedupe_key in seen_ids:
            duplicate_decisions.append(
                {
                    "chunk_id": chunk_id,
                    "incoming_rank": incoming_rank,
                    "selected": False,
                    "reason": "duplicate_chunk_id",
                    "structure_unit": _structure_unit(child),
                }
            )
            continue
        seen_ids.add(dedupe_key)
        unique.append(child)

    pool = unique[:inspection_pool_k]
    rrf_rank_by_id = {
        child.get("chunk_id"): rank for rank, child in enumerate(_rrf_order(pool), start=1)
    }

    scored: list[tuple[float, int, str, dict]] = []
    item_by_id: dict[object, dict] = {}
    for rerank_rank, child in enumerate(pool, start=1):
        chunk_id = child.get("chunk_id")
        rrf_rank = rrf_rank_by_id[chunk_id]
        score = RERANK_RRF_RERANK_WEIGHT / rerank_rank + (1 - RERANK_RRF_RERANK_WEIGHT) / rrf_rank
        decision = {
            "chunk_id": chunk_id,
            "selected": False,
            "reason": "not_selected_rank_fusion_limit",
            "reranker_rank": rerank_rank,
            "rrf_rank": rrf_rank,
            "selection_score": round(score, 8),
            "document_id": child.get("document_id"),
            "structure_unit": _structure_unit(child),
            "retrieval_sources": list(child.get("retrieval_sources") or []),
        }
        item_by_id[chunk_id] = decision
        scored.append((score, -rerank_rank, str(chunk_id or ""), child))

    selected_ids = {
        child.get("chunk_id") for _, _, _, child in sorted(scored, reverse=True)[:limit]
    }
    # Keep the incoming reranker order for downstream citations and packing.
    # The rank-fusion score changes membership only; it must not create a new
    # unexplained citation order.
    selected = [child for child in pool if child.get("chunk_id") in selected_ids]
    for chunk_id in selected_ids:
        item_by_id[chunk_id]["selected"] = True
        item_by_id[chunk_id]["reason"] = "selected_rank_fusion"

    decisions = []
    for child in pool:
        decisions.append(item_by_id[child.get("chunk_id")])
    decisions.extend(invalid_decisions)
    decisions.extend(duplicate_decisions)
    for incoming_rank, child in enumerate(unique[inspection_pool_k:], start=inspection_pool_k + 1):
        decisions.append(
            {
                "chunk_id": child.get("chunk_id"),
                "incoming_rank": incoming_rank,
                "selected": False,
                "reason": "outside_inspection_pool",
                "document_id": child.get("document_id"),
                "structure_unit": _structure_unit(child),
                "retrieval_sources": list(child.get("retrieval_sources") or []),
            }
        )

    trace = {
        "strategy": "reranker_rrf_reciprocal_rank_v1",
        "reranker_weight": RERANK_RRF_RERANK_WEIGHT,
        "inspection_pool_k": inspection_pool_k,
        "input_count": len(ranked_children),
        "unique_count": len(unique),
        "invalid_id_count": len(invalid_decisions),
        "pool_count": len(pool),
        "selection_limit": limit,
        "selected_ids": [child.get("chunk_id") for child in selected],
        "decisions": decisions,
    }
    logger.info(
        "child_selection strategy=%s input=%d unique=%d pool=%d selected=%d limit=%d",
        trace["strategy"],
        trace["input_count"],
        trace["unique_count"],
        trace["pool_count"],
        len(selected),
        limit,
    )
    for decision in decisions:
        logger.debug(
            "child_selection_decision chunk_id=%s selected=%s reason=%s "
            "rerank_rank=%s rrf_rank=%s document_id=%s structure_unit=%s",
            decision.get("chunk_id"),
            decision.get("selected"),
            decision.get("reason"),
            decision.get("reranker_rank"),
            decision.get("rrf_rank"),
            decision.get("document_id"),
            decision.get("structure_unit"),
        )
    return selected, trace


def select_protected_rrf_backfill_children(
    ranked_children: Sequence[dict],
    *,
    limit: int,
    inspection_pool_k: int,
) -> tuple[list[dict], dict]:
    """Keep a fixed reranker head, then fill a small tail by RRF and structure."""

    if limit < 1:
        raise ValueError("selection limit must be positive")
    if inspection_pool_k < 1:
        raise ValueError("inspection_pool_k must be positive")

    unique: list[dict] = []
    invalid_decisions: list[dict] = []
    duplicate_decisions: list[dict] = []
    seen_ids: set[object] = set()
    for incoming_rank, child in enumerate(ranked_children, start=1):
        chunk_id = child.get("chunk_id")
        if not chunk_id:
            invalid_decisions.append(
                {
                    "chunk_id": chunk_id,
                    "incoming_rank": incoming_rank,
                    "selected": False,
                    "reason": "invalid_child_id",
                    "structure_unit": _structure_unit(child),
                }
            )
            continue
        if chunk_id in seen_ids:
            duplicate_decisions.append(
                {
                    "chunk_id": chunk_id,
                    "incoming_rank": incoming_rank,
                    "selected": False,
                    "reason": "duplicate_chunk_id",
                    "structure_unit": _structure_unit(child),
                }
            )
            continue
        seen_ids.add(chunk_id)
        unique.append(child)

    pool = unique[:inspection_pool_k]
    protected_limit = min(PROTECTED_RRF_HEAD_K, limit)
    protected = pool[:protected_limit]
    selected_ids = {child["chunk_id"] for child in protected}

    def structure_key(child: dict) -> tuple[str, str]:
        structure = _structure_unit(child)
        # Missing structure is not one shared bucket: each Child remains eligible
        # as a distinct fallback candidate.
        return ("section", structure) if structure is not None else ("child", child["chunk_id"])

    covered_structures = {structure_key(child) for child in protected}
    backfill_decisions: dict[object, str] = {}
    remaining = _rrf_order([child for child in pool if child["chunk_id"] not in selected_ids])
    for _ in range(min(limit - len(protected), len(remaining))):
        fresh = [child for child in remaining if structure_key(child) not in covered_structures]
        candidate = (fresh or remaining)[0]
        remaining.remove(candidate)
        selected_ids.add(candidate["chunk_id"])
        key = structure_key(candidate)
        is_new_section = key not in covered_structures
        covered_structures.add(key)
        backfill_decisions[candidate["chunk_id"]] = (
            "selected_rrf_backfill_new_section"
            if is_new_section
            else "selected_rrf_backfill_existing_section"
        )

    decisions = []
    protected_ids = {child["chunk_id"] for child in protected}
    for child in pool:
        chunk_id = child["chunk_id"]
        if chunk_id in protected_ids:
            reason = "selected_protected_reranker"
            selected = True
        elif chunk_id in backfill_decisions:
            reason = backfill_decisions[chunk_id]
            selected = True
        else:
            reason = "not_selected_protected_rrf_backfill_limit"
            selected = False
        decisions.append(
            {
                "chunk_id": chunk_id,
                "incoming_rank": unique.index(child) + 1,
                "selected": selected,
                "reason": reason,
                "reranker_rank": unique.index(child) + 1,
                "rrf_rank": next(
                    rank for rank, item in enumerate(_rrf_order(pool), start=1) if item is child
                ),
                "document_id": child.get("document_id"),
                "structure_unit": _structure_unit(child),
                "retrieval_sources": list(child.get("retrieval_sources") or []),
            }
        )
    decisions.extend(invalid_decisions)
    decisions.extend(duplicate_decisions)
    for incoming_rank, child in enumerate(unique[inspection_pool_k:], start=inspection_pool_k + 1):
        decisions.append(
            {
                "chunk_id": child.get("chunk_id"),
                "incoming_rank": incoming_rank,
                "selected": False,
                "reason": "outside_inspection_pool",
                "document_id": child.get("document_id"),
                "structure_unit": _structure_unit(child),
                "retrieval_sources": list(child.get("retrieval_sources") or []),
            }
        )

    selected = [child for child in pool if child["chunk_id"] in selected_ids]
    trace = {
        "strategy": PROTECTED_RRF_BACKFILL_STRATEGY,
        "inspection_pool_k": inspection_pool_k,
        "input_count": len(ranked_children),
        "unique_count": len(unique),
        "invalid_id_count": len(invalid_decisions),
        "pool_count": len(pool),
        "selection_limit": limit,
        "protected_head_k": protected_limit,
        "backfill_limit": limit - protected_limit,
        "selected_ids": [child["chunk_id"] for child in selected],
        "decisions": decisions,
    }
    return selected, trace


def select_children(
    ranked_children: Sequence[dict],
    *,
    strategy: str,
    limit: int,
    inspection_pool_k: int,
) -> tuple[list[dict], dict]:
    """Apply an explicitly named selection policy.

    ``reranker_top_k`` is the safe default and preserves the historical
    behavior.  The RRF policy is experimental and must be selected explicitly
    by a caller or an evaluation run.
    """

    if strategy == RRF_SELECTION_STRATEGY:
        rerank_limit_for_selection(
            strategy, selection_limit=limit, inspection_pool_k=inspection_pool_k
        )
        return select_ranked_children(
            ranked_children,
            limit=limit,
            inspection_pool_k=inspection_pool_k,
        )
    if strategy == PROTECTED_RRF_BACKFILL_STRATEGY:
        rerank_limit_for_selection(
            strategy, selection_limit=limit, inspection_pool_k=inspection_pool_k
        )
        return select_protected_rrf_backfill_children(
            ranked_children,
            limit=limit,
            inspection_pool_k=inspection_pool_k,
        )
    if strategy != TOP_K_SELECTION_STRATEGY:
        raise ValueError(f"Unknown child selection strategy: {strategy}")
    if limit < 1:
        raise ValueError("selection limit must be positive")
    selected = []
    decisions = []
    for incoming_rank, child in enumerate(ranked_children, start=1):
        chunk_id = child.get("chunk_id")
        valid = bool(chunk_id)
        keep = valid and len(selected) < limit
        if keep:
            selected.append(child)
        decisions.append(
            {
                "chunk_id": chunk_id,
                "incoming_rank": incoming_rank,
                "selected": keep,
                "reason": "selected_reranker_top_k"
                if keep
                else ("invalid_child_id" if not valid else "outside_reranker_top_k"),
                "document_id": child.get("document_id"),
                "structure_unit": _structure_unit(child),
                "retrieval_sources": list(child.get("retrieval_sources") or []),
            }
        )
    return selected, {
        "strategy": TOP_K_SELECTION_STRATEGY,
        "input_count": len(ranked_children),
        "selection_limit": limit,
        "selected_ids": [child.get("chunk_id") for child in selected],
        "invalid_id_count": sum(not bool(child.get("chunk_id")) for child in ranked_children),
        "decisions": decisions,
    }
