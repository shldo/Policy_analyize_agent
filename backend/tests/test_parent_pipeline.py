import pytest

from app.modules.chat.rag import parent_pipeline


@pytest.fixture(autouse=True)
def strict_policy(monkeypatch):
    monkeypatch.setattr(parent_pipeline.get_settings(), "rag_allow_partial_answers", False)


def test_gate_precedes_resolution_and_never_judges_parent(monkeypatch):
    passed = {
        "chunk_id": "good",
        "text": "Valid supporting evidence. " * 20,
        "distance": 0.1,
        "reranker_score": 1,
    }
    rejected = dict(passed, chunk_id="bad", reranker_score=-9)
    events = []
    monkeypatch.setattr(parent_pipeline, "max_vector_distance", lambda: 0.5)
    monkeypatch.setattr(parent_pipeline, "min_reranker_score", lambda: -7)

    def gate(**kwargs):
        events.append("gate")
        assert kwargs["raw_chunks"] == [passed]
        assert kwargs["context"] == passed["text"]
        return True, None

    def resolve(children):
        events.append("resolve")
        assert children == [passed]
        return []

    monkeypatch.setattr(parent_pipeline, "assess_evidence_sufficiency", gate)
    monkeypatch.setattr(parent_pipeline, "resolve_generation_parents", resolve)
    parent_pipeline.prepare_child_context("Question", [passed, rejected])
    assert events == ["gate", "resolve"]


def test_failed_gate_does_not_expand(monkeypatch):
    monkeypatch.setattr(
        parent_pipeline, "assess_evidence_sufficiency", lambda **kwargs: (False, "weak evidence")
    )
    monkeypatch.setattr(parent_pipeline, "resolve_generation_parents", lambda _: 1 / 0)
    result = parent_pipeline.prepare_child_context("Question", [])
    assert not result["evidence_sufficient"]
    assert result["citations"] == []


@pytest.mark.parametrize(
    "status,packed_ids,expected",
    [
        ("supported", ["a", "b"], True),
        ("partial", ["a", "b"], False),
        ("background", ["a", "b"], False),
        ("supported", ["a"], False),
    ],
)
def test_controlled_coverage_survives_packing_not_legacy_gate(
    monkeypatch, status, packed_ids, expected
):
    monkeypatch.setattr(parent_pipeline, "max_vector_distance", lambda: 0.5)
    monkeypatch.setattr(parent_pipeline, "min_reranker_score", lambda: -7)
    children = [dict(chunk_id=c, text=c, distance=0.1, reranker_score=1) for c in ("a", "b")]
    trace = dict(
        needs=["need"],
        stop_reason="coverage_sufficient",
        inspections=[
            [dict(need_index=0, status=status, evidence=[dict(chunk_id=c) for c in ("a", "b")])]
        ],
    )
    monkeypatch.setattr(
        parent_pipeline,
        "assess_evidence_sufficiency",
        lambda **k: pytest.fail("legacy gate must not certify controlled coverage"),
    )
    monkeypatch.setattr(parent_pipeline, "resolve_generation_parents", lambda _: [])
    monkeypatch.setattr(parent_pipeline, "available_context_tokens", lambda _: 100)
    monkeypatch.setattr(
        parent_pipeline,
        "pack_generation_context",
        lambda *a, **k: dict(
            context="evidence",
            citations=[dict(chunk_id=c) for c in packed_ids],
            generation_parents=[],
            packed_token_count=10,
        ),
    )
    result = parent_pipeline.prepare_child_context("q", children, controlled_trace=trace)
    assert result["evidence_sufficient"] is expected
    assert result["controlled_trace"]["coverage_sufficient"] is expected


def test_controlled_chat_cannot_bypass_semantic_gate():
    from app.modules.chat.rag.graph.nodes import generate_answer_node, route_after_evidence_check

    state = dict(
        question="q",
        answer_mode="chat",
        evidence_sufficient=True,
        controlled_trace=dict(coverage_stage="packed", coverage_sufficient=False),
    )
    assert route_after_evidence_check(state) == "insufficient_evidence"
    assert "answer" in generate_answer_node(state)
