"""Read-only real-corpus smoke: python -m evaluation.hybrid_retrieval_smoke.

Uses the configured embedding provider and reranker. Does not invoke generation,
change documents/vectors, or edit benchmark questions. JSON goes to stdout.
"""

import json
from time import perf_counter

from app.core.config import get_settings
from app.core.database import get_connection
from app.modules.documents.repositories.embeddings import _active_table_dim
from app.modules.documents.service import _rerank_or_dense, retrieve_child_candidates


def fingerprint():
    table, _ = _active_table_dim()
    with get_connection() as connection:
        children = connection.execute(
            "SELECT count(*) AS count, "
            "md5(string_agg(md5(id::text || text), '' ORDER BY id)) AS hash "
            "FROM document_chunks"
        ).fetchone()
        vectors = connection.execute(
            "SELECT count(*) AS count, "
            "md5(string_agg(md5(chunk_id::text || embedding::text), '' ORDER BY chunk_id)) "
            f'AS hash FROM "{table}"'
        ).fetchone()
    return {"children": dict(children), "vectors": dict(vectors)}


def main():
    settings = get_settings()
    if settings.child_lexical_candidate_k <= 0:
        raise RuntimeError("BM25 is disabled; set CHILD_LEXICAL_CANDIDATE_K=30")
    before = fingerprint()
    cases = []
    for question in (
        "What requirements apply to AI-generated media and watermarking?",
        "When must staff complete mandatory AI training?",
    ):
        started = perf_counter()
        candidates = retrieve_child_candidates(question, expand_aspects=False)
        retrieval_seconds = perf_counter() - started
        assert candidates, "No candidates in configured corpus"
        assert all(
            candidates[i]["rrf_score"] >= candidates[i + 1]["rrf_score"]
            for i in range(len(candidates) - 1)
        )
        assert any("bm25" in c["retrieval_sources"] for c in candidates)
        for c in candidates:
            expected = sum(
                1 / (settings.hybrid_rrf_rank_constant + rank)
                for rank in c["retrieval_ranks"].values()
            )
            assert abs(c["rrf_score"] - expected) < 1e-12
        reranked = _rerank_or_dense(question, candidates, settings.child_rerank_k)
        assert reranked and all("rrf_score" in c for c in reranked)
        selected = retrieve_child_candidates(
            question, document_ids=[candidates[0]["document_id"]], expand_aspects=False
        )
        assert all(c["document_id"] == candidates[0]["document_id"] for c in selected)
        cases.append(
            {
                "question": question,
                "dense": sum("dense" in c["retrieval_sources"] for c in candidates),
                "bm25": sum("bm25" in c["retrieval_sources"] for c in candidates),
                "both": sum(len(c["retrieval_sources"]) == 2 for c in candidates),
                "fused": len(candidates),
                "reranked": len(reranked),
                "reranker_scored": sum("reranker_score" in c for c in reranked),
                "selected_scope_candidates": len(selected),
                "retrieval_seconds": round(retrieval_seconds, 3),
                "total_seconds": round(perf_counter() - started, 3),
                "top_ids": [c["chunk_id"] for c in candidates[:5]],
            }
        )
    after = fingerprint()
    assert before == after, "Corpus changed during smoke"
    print(json.dumps({"corpus_unchanged": True, "snapshot": before, "cases": cases}, indent=2))


if __name__ == "__main__":
    main()
