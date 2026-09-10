from app.modules.chat.rag.context_packing import pack_generation_context
from app.modules.documents import service


def test_hybrid_union_keeps_real_distance_and_scope(monkeypatch):
    monkeypatch.setattr(service, "embed_query", lambda q: [1])
    monkeypatch.setattr(service, "vector_literal", lambda v: "vector")
    monkeypatch.setattr(
        service.embedding_repository,
        "retrieve",
        lambda *a, **kw: [{"chunk_id": "a", "distance": 0.2}],
    )
    observed = {}

    def lexical(question, vector, ids, **kwargs):
        observed.update(ids=ids, **kwargs)
        return [
            {"chunk_id": "a", "distance": 0.2, "lexical_score": 1},
            {"chunk_id": "b", "distance": 0.8, "lexical_score": 2},
        ]

    monkeypatch.setattr(service.embedding_repository, "retrieve_lexical", lexical)
    result = service.retrieve_child_candidates("q", document_ids=["doc"])
    assert [c["chunk_id"] for c in result] == ["a", "b"]
    assert result[0]["retrieval_sources"] == ["dense", "bm25"]
    assert result[1]["distance"] == 0.8  # lexical recall cannot bypass vector gate
    assert observed["ids"] == ["doc"] and not observed["include_restricted"]


def test_evidence_reserved_before_expansion_and_exact_dedupe():
    parents = []
    for i in range(2):
        child = {
            "chunk_id": str(i),
            "document_id": str(i),
            "text": f"Evidence {i}.",
            "page_start": 1,
            "page_end": 1,
        }
        parents.append(
            {
                "context_id": str(i),
                "document_id": str(i),
                "file": "Policy",
                "parent_score": 2 - i,
                "text": child["text"] + " Extra context." * 100,
                "supporting_children": [child],
            }
        )
    result = pack_generation_context(parents, budget=700, count=len)
    assert len(result["citations"]) == 2
    assert result["packed_token_count"] <= 700
    assert result["context"].count("Evidence 0.") == 1
    assert result["context"].count("Evidence 1.") == 1
    roomy = pack_generation_context(parents, budget=5000, count=len)
    assert "Extra context." in roomy["context"]
    assert roomy["context"].count("Evidence 0.") == 1
