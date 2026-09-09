from collections import Counter
from pathlib import Path

from evaluation.dataset import load_dataset


def test_dev50_keeps_drafts_and_absence_candidates_out_of_approved_gold():
    _, cases = load_dataset(
        Path(__file__).resolve().parents[1] / "evaluation/datasets/policy-parent-child-dev50-v1"
    )
    assert len(cases) == 50
    assert sum(c["review_status"] == "reviewed" for c in cases) == 13
    assert all(c["split"] == "development" for c in cases)
    assert Counter(tag for c in cases for tag in c["coverage_tags"]) == {
        "legacy_regression": 13,
        "multi_child": 10,
        "cross_section": 8,
        "exception": 7,
        "modality": 6,
        "unanswerable_candidate": 6,
    }
    candidates = [c for c in cases if c["answerability"] == "unresolved_candidate"]
    assert len(candidates) == 6
    assert all(c["reference_answer"] is None for c in candidates)
