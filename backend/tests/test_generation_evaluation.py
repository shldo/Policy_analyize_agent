from copy import deepcopy

import pytest

from evaluation.dataset import digest
from evaluation.generation import build_packets, citation_checks


def fixture():
    manifest = {"version": "fixture"}
    cases = [
        {
            "question_id": "DEV-1",
            "split": "development",
            "question": "When?",
            "review_status": "reviewed",
            "answerability": "answerable",
            "reference_answer": "SECRET_GOLD",
            "required_answer_points": ["deadline"],
            "reference_answer_checks": {},
            "evidence_groups": [],
        }
    ]
    retrieval = {
        "split": "development",
        "mode": "retrieval",
        "dataset_sha256": digest({"manifest": manifest, "cases": cases}),
        "results": [{"question_id": "DEV-1", "rerank_ids": ["c"]}],
    }
    pool = [
        {
            "id": "c",
            "original_filename": "policy.pdf",
            "page_start": 1,
            "page_end": 2,
            "text": "Original excerpt",
        }
    ]
    return manifest, cases, retrieval, pool


def test_generation_request_excludes_gold_and_preserves_source():
    packets = build_packets(*fixture())
    assert "SECRET_GOLD" not in str(packets[0]["request"])
    assert packets[0]["request"]["sources"][0]["text"] == "Original excerpt"
    assert packets[0]["review_only"]["reference_answer"] == "SECRET_GOLD"


@pytest.mark.parametrize("change", ["test", "hash", "missing", "duplicate"])
def test_generation_rejects_wrong_inputs(change):
    manifest, cases, retrieval, pool = deepcopy(fixture())
    if change == "test":
        retrieval["split"] = "test"
    elif change == "hash":
        retrieval["dataset_sha256"] = "wrong"
    elif change == "missing":
        retrieval["results"][0]["rerank_ids"] = ["missing"]
    else:
        retrieval["results"] *= 2
    with pytest.raises(ValueError):
        build_packets(manifest, cases, retrieval, pool)


def test_citation_numbers_are_not_semantic_scores():
    checks = citation_checks("Claim [1]. Unsupported [8]. [0]", 5)
    assert checks["invalid_markers"] == [0, 8]
    assert checks["semantic_support"] == "not_scored_requires_review"
    assert not citation_checks("No citations", 5)["has_numbered_citation"]
