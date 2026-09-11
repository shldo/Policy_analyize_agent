"""Shared status contract for chat answers and persisted history.

The legacy ``evidence_sufficient`` field is retained for clients that still
read it, but it is deliberately not the source of truth for either generation
permission or coverage.  In particular, a non-empty source list is not proof
that the original question is completely covered.
"""

from __future__ import annotations

from typing import Literal

CoverageStatus = Literal["not_assessed", "partial", "complete", "no_context"]
AnswerStatus = Literal["pending", "streaming", "generated", "withheld", "error", "unknown"]


def normalize_coverage_status(value: object) -> CoverageStatus:
    if value in {"not_assessed", "partial", "complete", "no_context"}:
        return value  # type: ignore[return-value]
    return "not_assessed"


def normalize_answer_status(value: object) -> AnswerStatus:
    if value in {"pending", "streaming", "generated", "withheld", "error", "unknown"}:
        return value  # type: ignore[return-value]
    return "unknown"


def coverage_is_complete(value: object) -> bool:
    return value == "complete"


def legacy_evidence_sufficient(coverage_status: object) -> bool | None:
    """Map the new status to the nullable legacy field.

    Unknown and partial coverage stay distinguishable from a verified complete
    answer.  ``None`` is intentional for old/unknown records.
    """

    status = normalize_coverage_status(coverage_status)
    if status == "complete":
        return True
    if status in {"partial", "no_context"}:
        return False
    return None


def status_from_result(result: dict, *, answer_status: AnswerStatus | None = None) -> dict:
    """Return the normalized public status fields for a retrieval result."""

    coverage_status = normalize_coverage_status(result.get("coverage_status"))
    # A caller must provide both sides of the completeness proof.  A
    # contradictory or incomplete pair is normalized to unknown rather than
    # leaving a misleading ``complete`` label for history/UI to upgrade.
    coverage_sufficient = result.get("coverage_sufficient") is True and coverage_is_complete(
        coverage_status
    )
    if coverage_status == "complete" and not coverage_sufficient:
        coverage_status = "not_assessed"
    generation_allowed = result.get("generation_allowed")
    if not isinstance(generation_allowed, bool):
        generation_allowed = bool(result.get("context") or result.get("answer"))
    legacy = legacy_evidence_sufficient(coverage_status)
    evidence_signal = (
        coverage_sufficient
        or result.get("evidence_sufficient") is True
        or bool(result.get("evidence_sources"))
    )
    return {
        "generation_allowed": generation_allowed,
        "coverage_status": coverage_status,
        "coverage_sufficient": coverage_sufficient,
        "evidence_sufficient": legacy,
        "suggestions_allowed": bool(generation_allowed and evidence_signal),
        "answer_status": normalize_answer_status(
            answer_status or result.get("answer_status") or "unknown"
        ),
    }


def status_for_history(row: dict) -> dict:
    """Normalize nullable/new and legacy history columns conservatively."""

    coverage_status = normalize_coverage_status(row.get("coverage_status"))
    if coverage_status == "complete" and row.get("coverage_sufficient") is False:
        coverage_status = "not_assessed"
    answer_status = normalize_answer_status(row.get("answer_status"))
    generation_allowed = row.get("generation_allowed")
    if not isinstance(generation_allowed, bool):
        generation_allowed = None
    return {
        "generation_allowed": generation_allowed,
        "coverage_status": coverage_status,
        "coverage_sufficient": coverage_is_complete(coverage_status),
        "answer_status": answer_status,
    }
