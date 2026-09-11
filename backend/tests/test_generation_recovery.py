"""Recovery eligibility is independent of retrieval and never changes saved inputs."""

import copy

import pytest

from evaluation.recover_generation import recovery_inputs


def test_source_instruction_preserves_explicit_noncontiguous_numbers():
    from app.modules.chat.rag.generation import _build_citation_instruction

    instruction = _build_citation_instruction(
        [{"number": 1, "title": "One"}, {"number": 7, "title": "Seven"}]
    )
    assert "[1] One" in instruction
    assert "[7] Seven" in instruction
    assert "[2] Seven" not in instruction


def test_source_instruction_preserves_legacy_numbering():
    from app.modules.chat.rag.generation import _build_citation_instruction

    instruction = _build_citation_instruction([{"title": "One"}, {"title": "Two"}])
    assert "[1] One" in instruction
    assert "[2] Two" in instruction


def failed_row():
    return {
        "status": "error",
        "stage": "generation",
        "question": "What training is required?",
        "packed": {
            "generation_allowed": True,
            "context": "Exact saved context",
            "citations": [{"chunk_id": "child-1", "quote": "Exact evidence"}],
        },
    }


def test_recovery_preserves_saved_inputs():
    row = failed_row()
    before = copy.deepcopy(row)
    assert recovery_inputs(row) == {
        "question": row["question"],
        "context": row["packed"]["context"],
        "citations": row["packed"]["citations"],
    }
    assert row == before


@pytest.mark.parametrize("field,value", [("status", "ok"), ("stage", "retrieval")])
def test_recovery_rejects_non_generation_failures(field, value):
    row = failed_row()
    row[field] = value
    with pytest.raises(ValueError, match="Only failed generation"):
        recovery_inputs(row)


@pytest.mark.parametrize(
    "field,value", [("generation_allowed", False), ("context", ""), ("citations", [])]
)
def test_recovery_rejects_unapproved_or_missing_inputs(field, value):
    row = failed_row()
    row["packed"][field] = value
    with pytest.raises(ValueError, match="Missing approved"):
        recovery_inputs(row)
