from app.modules.chat.rag.context_packing import pack_generation_context
from app.modules.chat.rag.parent_resolution import resolve_generation_parents


def children():
    return [
        {
            "chunk_id": str(i),
            "document_id": "doc",
            "section_id": "section",
            "text": f"Evidence {i}. " * 20,
            "page_start": 3,
            "page_end": 4,
            "reranker_score": score,
            "distance": 0.2,
            "file": "Policy",
        }
        for i, score in enumerate([2, 8])
    ]


def test_dedupe_max_and_provenance():
    parents = resolve_generation_parents(
        children(),
        loader=lambda ids: {
            "section": {
                "document_id": "doc",
                "text": "Full policy context.",
                "token_count": 100,
                "page_start": 2,
                "page_end": 5,
            }
        },
    )
    assert len(parents) == 1
    assert parents[0]["parent_score"] == 8
    assert parents[0]["supporting_child_ids"] == ["0", "1"]
    packed = pack_generation_context(parents, budget=3000)
    assert [c["chunk_id"] for c in packed["citations"]] == ["0", "1"]
    assert packed["citations"][0]["page"] == 3
    assert "Full policy context." in packed["context"]
    assert packed["packed_token_count"] <= 3000
    assert pack_generation_context(parents, budget=1)["context"] == ""


def test_legacy_does_not_load_sections():
    legacy = [dict(c, section_id=None) for c in children()]
    parents = resolve_generation_parents(legacy, loader=lambda ids: {} if not ids else 1 / 0)
    assert len(parents) == 2
    assert parents[0]["text"] == legacy[1]["text"]
