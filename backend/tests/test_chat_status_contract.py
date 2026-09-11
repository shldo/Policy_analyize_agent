from uuid import uuid4

import pytest

from app.modules.chat import history_repository
from app.modules.chat.contracts import status_for_history, status_from_result
from app.modules.chat.rag.agent.state import final_packed_citations
from app.modules.chat.rag.generation import validate_answer_citations
from app.modules.chat.schemas import Citation


def test_status_migration_is_additive_and_declares_nullable_columns() -> None:
    from pathlib import Path

    migration = (
        Path(__file__).parents[1] / "database" / "migrations" / "020_add_chat_status_contract.sql"
    ).read_text(encoding="utf-8")
    assert "ADD COLUMN IF NOT EXISTS generation_allowed boolean" in migration
    assert "ADD COLUMN IF NOT EXISTS coverage_status text" in migration
    assert "ADD COLUMN IF NOT EXISTS answer_status text" in migration
    assert "DROP COLUMN" not in migration.upper()


def test_missing_status_migration_fails_with_explicit_message(monkeypatch) -> None:
    class MissingColumnConnection:
        def execute(self, _query: str) -> None:
            raise RuntimeError('column "coverage_status" does not exist')

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

    monkeypatch.setattr(
        history_repository,
        "get_connection",
        lambda: MissingColumnConnection(),
    )

    with pytest.raises(
        history_repository.ChatStatusMigrationRequired,
        match="migration 020 is required",
    ):
        history_repository.ChatHistoryRepository().ensure_status_contract()


def test_sources_do_not_certify_complete_coverage() -> None:
    status = status_from_result(
        {
            "context": "partial evidence",
            "citations": [{"chunk_id": "child-1"}],
            "evidence_sources": ["internal"],
        },
        answer_status="generated",
    )

    assert status["generation_allowed"] is True
    assert status["coverage_status"] == "not_assessed"
    assert status["coverage_sufficient"] is False
    assert status["evidence_sufficient"] is None
    assert status["suggestions_allowed"] is True
    assert status["answer_status"] == "generated"


def test_verified_complete_coverage_is_explicit() -> None:
    status = status_from_result(
        {
            "generation_allowed": True,
            "coverage_status": "complete",
            "coverage_sufficient": True,
        },
        answer_status="generated",
    )

    assert status["coverage_sufficient"] is True
    assert status["evidence_sufficient"] is True
    assert status["suggestions_allowed"] is True


def test_contradictory_complete_flag_fails_closed() -> None:
    status = status_from_result(
        {"coverage_status": "complete", "coverage_sufficient": False},
        answer_status="generated",
    )

    assert status["coverage_sufficient"] is False
    assert status["coverage_status"] == "not_assessed"
    assert status["evidence_sufficient"] is None
    assert status["suggestions_allowed"] is False


def test_history_does_not_upgrade_contradictory_complete_status() -> None:
    status = status_for_history({"coverage_status": "complete", "coverage_sufficient": False})

    assert status["coverage_status"] == "not_assessed"
    assert status["coverage_sufficient"] is False


def test_old_history_is_conservative_even_if_execution_finished() -> None:
    status = status_for_history({"status": "complete", "evidence_sufficient": True})

    assert status == {
        "generation_allowed": None,
        "coverage_status": "not_assessed",
        "coverage_sufficient": False,
        "answer_status": "unknown",
    }


def test_partial_answer_stays_generatable_but_not_complete() -> None:
    status = status_from_result(
        {
            "generation_allowed": True,
            "coverage_status": "partial",
            "coverage_sufficient": False,
        },
        answer_status="generated",
    )

    assert status["generation_allowed"] is True
    assert status["coverage_status"] == "partial"
    assert status["coverage_sufficient"] is False
    assert status["evidence_sufficient"] is False
    assert status["suggestions_allowed"] is False


def test_citation_identity_check_does_not_claim_semantic_support() -> None:
    result = validate_answer_citations(
        "Supported fact [4].",
        [{"number": 4, "chunk_id": "child-1", "quote": "Supported fact"}],
    )

    assert result["valid_identity"] is True
    assert result["semantic_support_checked"] is False


def test_unknown_citation_number_is_reported_without_rebinding() -> None:
    result = validate_answer_citations(
        "Unsupported marker [2].",
        [{"number": 1, "chunk_id": "child-1"}],
    )

    assert result["valid_identity"] is False
    assert result["unknown_numbers"] == [2]


def test_explicit_noncontiguous_citation_numbers_are_checked_as_identity() -> None:
    result = validate_answer_citations(
        "First [1], third [7], unknown [2].",
        [
            {"number": 1, "chunk_id": "child-1"},
            {"number": 3, "chunk_id": "child-3"},
            {"number": 7, "chunk_id": "child-7"},
        ],
    )

    assert result["valid_identity"] is False
    assert result["unknown_numbers"] == [2]


def test_legacy_citations_without_numbers_use_array_order() -> None:
    result = validate_answer_citations(
        "Legacy source [2].",
        [{"chunk_id": "child-1"}, {"chunk_id": "child-2"}],
    )

    assert result["valid_identity"] is True
    assert result["unknown_numbers"] == []


def test_citation_schema_preserves_explicit_number() -> None:
    citation = Citation(number=7, title="Policy", chunk_id=uuid4())

    assert citation.model_dump()["number"] == 7


def test_final_citations_drop_unpacked_children_but_keep_web_sources() -> None:
    citations = [
        {"number": 1, "chunk_id": "kept-child"},
        {"number": 2, "chunk_id": "dropped-child"},
        {"number": 3, "source_url": "https://example.org"},
    ]

    assert final_packed_citations(citations, {"kept-child"}) == [citations[0], citations[2]]
