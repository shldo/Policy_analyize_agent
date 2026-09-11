from types import SimpleNamespace

import pytest

from app.modules.chat.rag import context_packing
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
    assert packed["expanded_parent_count"] == 1
    assert packed["child_only_parent_count"] == 0
    assert pack_generation_context(parents, budget=1)["context"] == ""


def test_legacy_does_not_load_sections():
    legacy = [dict(c, section_id=None) for c in children()]
    parents = resolve_generation_parents(legacy, loader=lambda ids: {} if not ids else 1 / 0)
    assert len(parents) == 2
    assert parents[0]["text"] == legacy[1]["text"]


def parent(context_id, document_id, score, text=""):
    child_id = f"child-{context_id}"
    child = {
        "chunk_id": child_id,
        "document_id": document_id,
        "text": text or f"Evidence {child_id}.",
        "page_start": 1,
        "page_end": 1,
    }
    return {
        "context_id": context_id,
        "document_id": document_id,
        "file": "Policy",
        "parent_score": score,
        "text": "",
        "supporting_children": [child],
    }


def p2_settings(**overrides):
    values = {
        "parent_context_k": 3,
        "max_parents_per_document": 1,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_per_document_backfill_uses_remaining_parent_slot_without_displacing_initial(
    monkeypatch,
):
    monkeypatch.setattr(context_packing, "get_settings", lambda: p2_settings())
    parents = [
        parent("a-1", "doc-a", 3),
        parent("a-2", "doc-a", 1),
        parent("b-1", "doc-b", 2),
    ]

    result = pack_generation_context(
        parents,
        budget=10000,
        count=len,
        packing_policy="per_document_backfill_v1",
    )

    assert [item["context_id"] for item in result["generation_parents"]] == [
        "a-1",
        "b-1",
        "a-2",
    ]
    assert {item["reason"] for item in result["packing_trace"]} >= {
        "selected_initial",
        "per_document_deferred",
        "selected_backfill",
    }
    assert result["packed_token_count"] <= 10000
    assert result["expanded_parent_count"] == 0
    assert result["child_only_parent_count"] == 3


def test_backfill_does_not_break_global_parent_limit(monkeypatch):
    monkeypatch.setattr(context_packing, "get_settings", lambda: p2_settings(parent_context_k=2))
    parents = [
        parent("a-1", "doc-a", 3),
        parent("a-2", "doc-a", 1),
        parent("b-1", "doc-b", 2),
    ]

    result = pack_generation_context(
        parents,
        budget=10000,
        count=len,
        packing_policy="per_document_backfill_v1",
    )

    assert len(result["generation_parents"]) == 2
    assert any(item["reason"] == "global_parent_limit" for item in result["packing_trace"])


def test_backfill_records_token_budget_without_hard_truncation(monkeypatch):
    monkeypatch.setattr(context_packing, "get_settings", lambda: p2_settings())
    initial = [parent("a-1", "doc-a", 3), parent("b-1", "doc-b", 2)]
    baseline = pack_generation_context(initial, budget=10000, count=len)
    parents = [
        initial[0],
        parent("a-2", "doc-a", 1, text="x" * 1000),
        initial[1],
    ]

    result = pack_generation_context(
        parents,
        budget=baseline["packed_token_count"] + 1,
        count=len,
        packing_policy="per_document_backfill_v1",
    )

    assert [item["context_id"] for item in result["generation_parents"]] == ["a-1", "b-1"]
    assert any(item["reason"] == "token_budget" for item in result["packing_trace"])
    assert all("x" * 1000 not in block for block in result["context"].split("\n\n---\n\n"))


def test_duplicate_parent_is_audited_and_not_repacked(monkeypatch):
    monkeypatch.setattr(context_packing, "get_settings", lambda: p2_settings())
    duplicate = parent("same", "doc-a", 3)
    result = pack_generation_context(
        [duplicate, dict(duplicate), parent("other", "doc-b", 1)],
        budget=10000,
        count=len,
        packing_policy="per_document_backfill_v1",
    )

    assert [item["context_id"] for item in result["generation_parents"]] == ["same", "other"]
    assert any(item["reason"] == "duplicate_parent" for item in result["packing_trace"])


def test_unknown_packing_policy_is_rejected():
    with pytest.raises(ValueError, match="Unknown packing policy"):
        pack_generation_context([], budget=100, packing_policy="not-a-policy")
