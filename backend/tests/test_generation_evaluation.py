from copy import deepcopy

import pytest

from evaluation.dataset import digest
from evaluation.generation import build_packets, citation_checks, select_packets
from evaluation.prompt_variants import COMPLETENESS_V1, apply_variant


def test_prompt_experiment_preserves_baseline_and_is_question_independent():
    original = "Original system prompt and corpus"
    assert apply_variant(original, "baseline") == original
    assert apply_variant(original, "completeness-v1") == original + "\n\n" + COMPLETENESS_V1
    for forbidden in ("DEV-", "TEST-", "ai@dta", "watermark", "30 April"):
        assert forbidden not in COMPLETENESS_V1
    with pytest.raises(ValueError):
        apply_variant(original, "unknown")


def test_offset_selection_does_not_repeat_collected_cases():
    packets = [{"question_id": str(i)} for i in range(5)]
    assert [p["question_id"] for p in select_packets(packets, 3, 10)] == ["3", "4"]
    for offset, limit in [(-1, 1), (5, 1), (0, 0)]:
        with pytest.raises(ValueError):
            select_packets(packets, offset, limit)


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
