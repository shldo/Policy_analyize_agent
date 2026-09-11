from app.modules.documents.child_selection import (
    PROTECTED_RRF_BACKFILL_STRATEGY,
    RRF_SELECTION_STRATEGY,
    TOP_K_SELECTION_STRATEGY,
    select_children,
    select_protected_rrf_backfill_children,
    select_ranked_children,
)


def child(chunk_id, *, rrf_score=None, document_id="doc", section_id=None, sources=None):
    value = {
        "chunk_id": chunk_id,
        "document_id": document_id,
        "section_id": section_id,
        "text": f"Evidence {chunk_id}",
    }
    if rrf_score is not None:
        value["rrf_score"] = rrf_score
    if sources is not None:
        value["retrieval_sources"] = sources
    return value


def test_rank_fusion_retains_high_rrf_candidate_below_old_top_k():
    ranked = [
        child("rerank-1", rrf_score=0.010),
        child("rerank-2", rrf_score=0.009),
        child("rerank-3", rrf_score=0.008),
        child("rrf-1", rrf_score=0.040, sources=["dense", "bm25"]),
        child("rrf-2", rrf_score=0.030, sources=["dense"]),
    ]

    selected, trace = select_ranked_children(ranked, limit=3, inspection_pool_k=5)

    selected_ids = {child["chunk_id"] for child in selected}
    assert "rrf-1" in selected_ids
    assert selected_ids & {"rerank-1", "rerank-2", "rerank-3"}
    assert trace["strategy"] == "reranker_rrf_reciprocal_rank_v1"
    assert any(
        item["chunk_id"] == "rrf-1" and item["reason"] == "selected_rank_fusion"
        for item in trace["decisions"]
    )


def test_duplicate_child_does_not_consume_selection_slot():
    selected, trace = select_ranked_children(
        [child("a", rrf_score=0.03), child("a", rrf_score=0.02), child("b", rrf_score=0.01)],
        limit=2,
        inspection_pool_k=3,
    )

    assert [item["chunk_id"] for item in selected] == ["a", "b"]
    assert sum(item["reason"] == "duplicate_chunk_id" for item in trace["decisions"]) == 1


def test_inspection_pool_is_separate_from_selection_limit():
    selected, trace = select_ranked_children(
        [child(str(index), rrf_score=1 / (index + 1)) for index in range(5)],
        limit=2,
        inspection_pool_k=3,
    )

    assert len(selected) == 2
    assert trace["inspection_pool_k"] == 3
    assert any(item["reason"] == "outside_inspection_pool" for item in trace["decisions"])


def test_legacy_list_without_rrf_score_keeps_incoming_order():
    selected, trace = select_ranked_children(
        [child("a"), child("b"), child("c")], limit=2, inspection_pool_k=3
    )

    assert [item["chunk_id"] for item in selected] == ["a", "b"]
    assert [item["rrf_rank"] for item in trace["decisions"] if "rrf_rank" in item] == [1, 2, 3]


def test_missing_child_ids_are_rejected_and_cannot_exceed_limit():
    selected, trace = select_ranked_children(
        [child(None), child("valid"), child("")], limit=1, inspection_pool_k=3
    )

    assert [item["chunk_id"] for item in selected] == ["valid"]
    assert len(selected) <= 1
    assert trace["invalid_id_count"] == 2
    assert sum(item["reason"] == "invalid_child_id" for item in trace["decisions"]) == 2


def test_same_section_children_are_not_hard_deduplicated():
    ranked = [
        child("first", rrf_score=0.03, section_id="shared"),
        child("second", rrf_score=0.02, section_id="shared"),
        child("other", rrf_score=0.01, section_id="other"),
    ]

    selected, _ = select_ranked_children(ranked, limit=3, inspection_pool_k=3)

    assert {item["chunk_id"] for item in selected} == {"first", "second", "other"}


def test_default_strategy_is_explicit_and_preserves_historical_top_k():
    selected, trace = select_children(
        [child("a"), child("b"), child("c")],
        strategy=TOP_K_SELECTION_STRATEGY,
        limit=2,
        inspection_pool_k=20,
    )

    assert [item["chunk_id"] for item in selected] == ["a", "b"]
    assert trace["strategy"] == TOP_K_SELECTION_STRATEGY
    assert RRF_SELECTION_STRATEGY != TOP_K_SELECTION_STRATEGY


def test_protected_backfill_keeps_first_six_and_can_retain_high_rrf_after_old_top_k():
    ranked = [
        child(f"head-{index}", rrf_score=0.01, section_id=f"head-{index}") for index in range(6)
    ] + [
        child("old-7", rrf_score=0.02, section_id="old-7"),
        child("old-8", rrf_score=0.03, section_id="old-8"),
        child("rrf-9", rrf_score=0.90, section_id="new-9"),
        child("rrf-10", rrf_score=0.80, section_id="new-10"),
    ]

    selected, trace = select_protected_rrf_backfill_children(ranked, limit=8, inspection_pool_k=10)

    selected_ids = {item["chunk_id"] for item in selected}
    assert {f"head-{index}" for index in range(6)} <= selected_ids
    assert {"rrf-9", "rrf-10"} <= selected_ids
    assert trace["protected_head_k"] == 6
    assert trace["backfill_limit"] == 2


def test_protected_backfill_prefers_uncovered_section_then_allows_existing_section():
    ranked = [child(f"head-{index}", rrf_score=0.01, section_id="shared") for index in range(6)] + [
        child("existing", rrf_score=0.90, section_id="shared"),
        child("new", rrf_score=0.10, section_id="new-section"),
    ]

    selected, trace = select_children(
        ranked,
        strategy=PROTECTED_RRF_BACKFILL_STRATEGY,
        limit=8,
        inspection_pool_k=8,
    )

    assert {item["chunk_id"] for item in selected} == {
        *(f"head-{index}" for index in range(6)),
        "existing",
        "new",
    }
    reasons = {item["chunk_id"]: item["reason"] for item in trace["decisions"]}
    assert reasons["new"] == "selected_rrf_backfill_new_section"
    assert reasons["existing"] == "selected_rrf_backfill_existing_section"


def test_protected_backfill_missing_structure_is_not_one_shared_section():
    ranked = [child(f"head-{index}", rrf_score=0.01, section_id="shared") for index in range(6)] + [
        child("missing-a", rrf_score=0.02),
        child("missing-b", rrf_score=0.01),
    ]

    selected, _ = select_protected_rrf_backfill_children(ranked, limit=8, inspection_pool_k=8)

    assert {item["chunk_id"] for item in selected} >= {"missing-a", "missing-b"}


def test_protected_backfill_without_rrf_uses_reranker_order_and_handles_invalids():
    ranked = [child(None), *[child(str(index)) for index in range(7)], child("last")]

    selected, trace = select_protected_rrf_backfill_children(ranked, limit=8, inspection_pool_k=9)

    assert [item["chunk_id"] for item in selected] == [str(index) for index in range(7)] + ["last"]
    assert trace["invalid_id_count"] == 1
    assert len(selected) <= 8
