from app.modules.chat.rag import parent_pipeline


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
