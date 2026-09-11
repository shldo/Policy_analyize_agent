from evaluation.exploratory_parent_child import (
    _prepare_child_context_with_policy,
    draft_cases,
    evidence_mapping,
    stage_scores,
)


def test_draft_selection_never_uses_test_or_approves_labels():
    cases = [
        {"split": "development", "review_status": "draft"},
        {"split": "development", "review_status": "reviewed"},
        {"split": "test", "review_status": "draft"},
    ]
    assert draft_cases(cases) == [cases[0]]
    assert cases[0]["review_status"] == "draft"


def test_candidate_has_no_score_and_unmapped_is_not_skipped():
    assert evidence_mapping({"answerability": "unresolved_candidate"}, []) == (
        None,
        "unresolved_candidate_not_scored",
    )
    groups, status = evidence_mapping(
        {
            "answerability": "answerable",
            "question_id": "X",
            "evidence_groups": [{"id": "g", "alternatives": []}],
        },
        [],
    )
    assert groups is None and "Unresolved evidence" in status
    assert stage_scores([], groups) is None
    assert stage_scores([], [{"gold"}])["all_evidence_at_5"] == 0


def test_full_evaluator_passes_explicit_packing_policy_to_pipeline():
    captured = {}

    def fake_prepare(question, children, **kwargs):
        captured.update(kwargs)
        return {"question": question, "children": children}

    _prepare_child_context_with_policy(
        fake_prepare,
        "Question",
        [],
        packing_policy="per_document_backfill_v1",
        controlled_trace={"stop_reason": "coverage_sufficient"},
    )

    assert captured == {
        "packing_policy": "per_document_backfill_v1",
        "controlled_trace": {"stop_reason": "coverage_sufficient"},
    }
