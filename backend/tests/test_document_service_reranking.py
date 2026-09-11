from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.modules.documents import service


def configure_retrieval_dependencies(monkeypatch) -> dict:
    captured: dict = {}
    monkeypatch.setattr(service, "reranker_enabled", lambda: True)

    monkeypatch.setattr(
        service.document_repository,
        "get_record",
        lambda identifier, include_restricted=False: {
            "id": identifier,
        },
    )
    monkeypatch.setattr(
        service,
        "embed_query",
        lambda question: [0.1] * 384,
    )
    monkeypatch.setattr(
        service,
        "vector_literal",
        lambda vector: "[query-vector]",
    )

    candidates = [
        {
            "chunk_id": f"chunk-{index}",
            "text": f"Candidate {index}",
            "distance": index / 100,
        }
        for index in range(24)
    ]

    def fake_retrieve(
        query_vector: str,
        document_ids: list[str],
        *,
        limit: int,
    ) -> list[dict]:
        captured["query_vector"] = query_vector
        captured["document_ids"] = document_ids
        captured["candidate_limit"] = limit
        return candidates[:limit]

    monkeypatch.setattr(
        service.embedding_repository,
        "retrieve",
        fake_retrieve,
    )

    captured["candidates"] = candidates
    monkeypatch.setattr(service.embedding_repository, "retrieve_lexical", lambda *a, **kw: [])
    return captured


def test_retrieve_relevant_chunks_uses_reranker(
    monkeypatch,
) -> None:
    captured = configure_retrieval_dependencies(monkeypatch)

    def fake_rerank(
        question: str,
        chunks: list[dict],
        *,
        limit: int,
    ) -> list[dict]:
        captured["rerank_question"] = question
        captured["rerank_chunk_count"] = len(chunks)
        captured["final_limit"] = limit
        return list(reversed(chunks))[:limit]

    monkeypatch.setattr(
        service,
        "rerank_chunks",
        fake_rerank,
    )

    results = service.retrieve_relevant_chunks(
        "Policy question",
        ["document-1"],
        limit=8,
    )

    assert captured["candidate_limit"] == 30
    assert captured["rerank_chunk_count"] == 24
    assert captured["final_limit"] == 8
    assert captured["rerank_question"] == "Policy question"
    assert len(results) == 8
    assert results[0]["chunk_id"] == "chunk-23"


def test_retrieve_relevant_chunks_falls_back_when_reranker_fails(
    monkeypatch,
) -> None:
    captured = configure_retrieval_dependencies(monkeypatch)

    def failing_reranker(
        question: str,
        chunks: list[dict],
        *,
        limit: int,
    ) -> list[dict]:
        raise RuntimeError("Reranker unavailable")

    monkeypatch.setattr(
        service,
        "rerank_chunks",
        failing_reranker,
    )

    results = service.retrieve_relevant_chunks(
        "Policy question",
        ["document-1"],
        limit=8,
    )

    assert captured["candidate_limit"] == 30
    assert len(results) == 8
    assert results[0]["chunk_id"] == "chunk-0"


@pytest.mark.parametrize("full_corpus", [False, True])
def test_selected_and_full_corpus_share_explicit_selection_strategy(monkeypatch, full_corpus):
    settings = SimpleNamespace(
        controlled_retrieval_enabled=False,
        child_candidate_k=5,
        child_selection_pool_k=40,
        child_selection_strategy="reranker_rrf_reciprocal_rank_v1",
        child_rerank_k=2,
        child_lexical_candidate_k=30,
    )
    candidates = [
        {"chunk_id": f"chunk-{index}", "text": f"Candidate {index}", "rrf_score": score}
        for index, score in enumerate((0.01, 0.009, 0.008, 0.04, 0.03))
    ]
    monkeypatch.setattr(service, "get_settings", lambda: settings)
    monkeypatch.setattr(service, "resolve_document_ids", lambda *args: ["doc"])

    def retrieve(*args, **kwargs):
        captured = getattr(retrieve, "captured", {})
        captured["candidate_limit"] = kwargs["limit"]
        retrieve.captured = captured
        return candidates

    monkeypatch.setattr(service, "retrieve_child_candidates", retrieve)
    monkeypatch.setattr(service, "_rerank_or_dense", lambda question, rows, limit: rows)

    result = (
        service.search_full_corpus("q", limit=2)
        if full_corpus
        else service.retrieve_relevant_chunks("q", ["doc"], limit=2)
    )

    assert len(result) == 2
    assert "chunk-3" in {row["chunk_id"] for row in result}
    assert retrieve.captured["candidate_limit"] == 20


def test_experimental_selection_rejects_pool_smaller_than_selection_limit(monkeypatch):
    settings = SimpleNamespace(
        controlled_retrieval_enabled=False,
        child_candidate_k=5,
        child_selection_pool_k=1,
        child_selection_strategy="reranker_rrf_reciprocal_rank_v1",
        child_rerank_k=2,
        child_lexical_candidate_k=30,
    )
    monkeypatch.setattr(service, "get_settings", lambda: settings)

    with pytest.raises(ValueError, match="child_selection_pool_k"):
        service.search_full_corpus("q", limit=2)


def test_protected_backfill_strategy_reaches_beyond_top_k_online(monkeypatch):
    settings = SimpleNamespace(
        controlled_retrieval_enabled=False,
        child_candidate_k=5,
        child_selection_pool_k=10,
        child_selection_strategy="reranker_protected_rrf_backfill_v1",
        child_rerank_k=8,
        child_lexical_candidate_k=30,
    )
    candidates = [
        {
            "chunk_id": f"chunk-{index}",
            "text": f"Candidate {index}",
            "rrf_score": 0.01 if index < 6 else (0.9 if index == 8 else 0.02),
            "section_id": f"section-{index}",
        }
        for index in range(10)
    ]
    captured = {}
    monkeypatch.setattr(service, "get_settings", lambda: settings)
    monkeypatch.setattr(service, "resolve_document_ids", lambda *args: ["doc"])

    def retrieve(*args, **kwargs):
        captured["candidate_limit"] = kwargs["limit"]
        return candidates

    monkeypatch.setattr(service, "retrieve_child_candidates", retrieve)
    monkeypatch.setattr(service, "_rerank_or_dense", lambda question, rows, limit: rows)

    result = service.search_full_corpus("q", limit=8)

    assert captured["candidate_limit"] == 24
    assert len(result) == 8
    assert "chunk-8" in {row["chunk_id"] for row in result}
