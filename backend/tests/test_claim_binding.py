import pytest

from app.modules.chat.rag.claim_binding import apply_review, child_sources, units_for


def fixture():
    return units_for("Training is required [7].\nUnrelated obligation [7]."), child_sources(
        [{"number": 7, "chunk_id": "child", "quote": "Training is required."}]
    )


def test_partial_is_removed_not_upgraded():
    units, sources = fixture()
    result = apply_review(
        units,
        sources,
        {
            "units": [
                {
                    "id": "u1",
                    "status": "supported",
                    "bindings": [{"number": 7, "quote": "Training is required."}],
                },
                {"id": "u2", "status": "partial", "bindings": []},
            ]
        },
    )
    assert result["answer"] == "Training is required [7]."
    assert result["removed_unit_ids"] == ["u2"]
    assert result["coverage_sufficient"] is None


def test_review_cannot_skip_units():
    units, sources = fixture()
    with pytest.raises(ValueError, match="every unit"):
        apply_review(units, sources, {"units": []})


def test_parent_only_quote_rejected():
    units, sources = fixture()
    with pytest.raises(ValueError, match="No reviewed"):
        apply_review(
            units,
            sources,
            {
                "units": [
                    {
                        "id": "u1",
                        "status": "supported",
                        "bindings": [{"number": 7, "quote": "Parent-only duty"}],
                    },
                    {"id": "u2", "status": "unsupported", "bindings": []},
                ]
            },
        )


def test_binding_repairs_number_without_rewriting_fact():
    sources = child_sources([{"number": 7, "quote": "Training is required."}])
    result = apply_review(
        units_for("Training is required [2]."),
        sources,
        {
            "units": [
                {
                    "id": "u1",
                    "status": "supported",
                    "bindings": [{"number": 7, "quote": "Training is required."}],
                },
            ]
        },
    )
    assert result["answer"] == "Training is required . [7]"
    assert result["rebound_unit_ids"] == ["u1"]


def test_non_factual_label_cannot_exempt_prose():
    with pytest.raises(ValueError, match="No reviewed"):
        apply_review(
            units_for("Agencies must do something."),
            {},
            {
                "units": [
                    {"id": "u1", "status": "non_factual", "bindings": []},
                ]
            },
        )


def test_bold_subject_heading_is_retained():
    units = units_for("**Agency A**\nTraining is required [7].")
    result = apply_review(
        units,
        child_sources([{"number": 7, "quote": "Training is required."}]),
        {
            "units": [
                {"id": "u1", "status": "non_factual", "bindings": []},
                {
                    "id": "u2",
                    "status": "supported",
                    "bindings": [{"number": 7, "quote": "Training is required."}],
                },
            ]
        },
    )
    assert result["answer"].startswith("**Agency A**")


def test_invalid_binding_does_not_discard_other_supported_units():
    units, sources = fixture()
    result = apply_review(
        units,
        sources,
        {
            "units": [
                {
                    "id": "u1",
                    "status": "supported",
                    "bindings": [{"number": 7, "quote": "Training is required."}],
                },
                {
                    "id": "u2",
                    "status": "supported",
                    "bindings": [{"number": 7, "quote": "Not present"}],
                },
            ]
        },
    )
    assert result["answer"] == "Training is required [7]."
    assert "u2" in result["binding_errors"]


def test_streaming_does_not_emit_unreviewed_draft(monkeypatch):
    import asyncio
    from types import SimpleNamespace

    from app.modules.chat.rag import generation

    monkeypatch.setattr(
        generation, "get_settings", lambda: SimpleNamespace(rag_claim_binding_enabled=True)
    )
    monkeypatch.setattr(generation, "generate_answer", lambda *args: ("Reviewed", "model"))

    async def collect():
        return [token async for token in generation.generate_answer_streaming("q", "c")]

    assert asyncio.run(collect()) == ["Reviewed"]
