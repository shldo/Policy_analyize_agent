from copy import deepcopy
from pathlib import Path

import pytest

from evaluation.dataset import (
    answerability,
    is_answerable,
    load_dataset,
    resolve_groups,
    score_groups,
    validate,
)
from evaluation.run import check_pool

DATASET = Path(__file__).parents[1] / "evaluation/datasets/policy-v3"


def test_shipped_dataset_and_holdout_status():
    manifest, cases = load_dataset(DATASET)
    assert len(cases) == 31
    assert sum(c["split"] == "test" for c in cases) == 18
    assert "TEST-20" not in {c["question_id"] for c in cases}
    assert manifest["dataset_version"] == "policy-benchmark-v3-draft"
    assert all(c["review_status"] == "draft" for c in cases)
    assert all(c["split"] == "development" for c in cases if c["question_id"].startswith("DEV-"))
    assert len(manifest["documents"]) == 5


def test_reingestion_matches_new_uuid_and_whitespace():
    _, cases = load_dataset(DATASET)
    case = deepcopy(cases[0])
    case["evidence_groups"] = case["evidence_groups"][:1]
    anchor = case["evidence_groups"][0]["alternatives"][0]
    chunk = {
        "id": "new-uuid",
        "sha256": anchor["document_sha256"],
        "page_start": anchor["page_start"] - 1,
        "page_end": anchor["page_end"],
        "text": anchor["quote"].replace(" ", "\n"),
    }
    assert resolve_groups(case, [chunk]) == [{"new-uuid"}]
    chunk["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="Unresolved"):
        resolve_groups(case, [chunk])


def test_split_across_chunks_requires_remapping_not_false_success():
    _, cases = load_dataset(DATASET)
    case = cases[0]
    anchor = case["evidence_groups"][0]["alternatives"][0]
    chunk = {
        "id": "partial",
        "sha256": anchor["document_sha256"],
        "page_start": anchor["page_start"],
        "page_end": anchor["page_end"],
        "text": anchor["quote"][:5],
    }
    with pytest.raises(ValueError, match="Unresolved"):
        resolve_groups(case, [chunk])


def test_equivalent_chunks_count_once_and_multiple_groups_require_both():
    groups = [{"a", "overlap-a"}, {"b"}]
    scores = score_groups(["a", "overlap-a", "irrelevant"], groups)
    assert scores["hit_at_5"] == 1
    assert scores["evidence_group_coverage_at_5"] == 0.5
    assert scores["all_evidence_at_5"] == 0
    assert score_groups(["b", "a"], groups)["all_evidence_at_5"] == 1
    assert score_groups([], groups)["rr_at_10"] == 0


def test_metric_cutoffs():
    ids = [str(i) for i in range(1, 22)]
    assert score_groups(ids, [{"6"}])["hit_at_5"] == 0
    assert score_groups(ids, [{"10"}])["rr_at_10"] == 0.1
    assert score_groups(ids, [{"11"}])["rr_at_10"] == 0
    with pytest.raises(ValueError):
        score_groups(["a", "a"], [{"a"}])
    with pytest.raises(ValueError):
        score_groups([], [])


def test_cross_split_topic_and_anchor_rejected():
    manifest, cases = load_dataset(DATASET)
    clone = deepcopy(cases[0])
    clone.update(question_id="CLONE", question="Different wording?", split="test")
    with pytest.raises(ValueError, match="Cross-split"):
        validate(manifest, [cases[0], clone])
    clone["leakage_group"] = "different"
    with pytest.raises(ValueError, match="anchor crosses"):
        validate(manifest, [cases[0], clone])


def test_unknown_documents_and_unreviewed_absence():
    manifest, cases = load_dataset(DATASET)
    case = deepcopy(cases[0])
    case["evidence_groups"][0]["alternatives"][0]["document_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="Invalid anchor"):
        validate(manifest, [case])
    negative = deepcopy(next(c for c in cases if not is_answerable(c)))
    del negative["absence_review"]
    with pytest.raises(ValueError, match="absence review"):
        validate(manifest, [negative])


def test_corpus_growth_requires_version_review_and_missing_vectors_fail():
    manifest = {"documents": [{"sha256": "a"}]}
    pool = [{"sha256": "a", "vector": "[1]"}]
    documents = [{"sha256": "a", "status": "ready"}]
    check_pool(manifest, pool, documents)
    with pytest.raises(ValueError, match="membership"):
        check_pool(manifest, pool, documents + [{"sha256": "b", "status": "ready"}])
    with pytest.raises(ValueError, match="vectors"):
        check_pool(manifest, [{"sha256": "a", "vector": None}], documents)


@pytest.mark.parametrize("version,count", [("policy-v1", 33), ("policy-v2", 32)])
def test_historical_versions_remain_loadable(version, count):
    _, cases = load_dataset(DATASET.parent / version)
    assert len(cases) == count
    assert all(answerability(c) == "unresolved_candidate" for c in cases if not is_answerable(c))


def test_candidate_cannot_become_a_gold_refusal_without_full_review():
    manifest, cases = load_dataset(DATASET)
    candidate = deepcopy(next(c for c in cases if not is_answerable(c)))
    assert candidate["reference_answer"] is None
    candidate["reference_answer"] = "The corpus does not establish this."
    with pytest.raises(ValueError, match="cannot have gold"):
        validate(manifest, [candidate])
    candidate["answerability"] = "unanswerable_confirmed"
    with pytest.raises(ValueError, match="entire corpus"):
        validate(manifest, [candidate])
    candidate["absence_review_record"] = {
        "reviewed_by": "test-reviewer",
        "reviewed_at": "2026-09-07",
        "method": "human_full_corpus",
        "document_sha256s": [d["sha256"] for d in manifest["documents"]],
    }
    validate(manifest, [candidate])
    candidate["absence_review_record"]["document_sha256s"].pop()
    with pytest.raises(ValueError, match="entire corpus"):
        validate(manifest, [candidate])


def test_answer_completeness_fields_are_required():
    manifest, cases = load_dataset(DATASET)
    case = deepcopy(cases[0])
    del case["reference_answer_checks"]["condition_or_trigger"]
    with pytest.raises(ValueError, match="Four answer"):
        validate(manifest, [case])


def test_legacy_answers_no_longer_contain_migration_placeholders():
    _, cases = load_dataset(DATASET)
    for case in cases:
        if is_answerable(case):
            assert not case["reference_answer"].startswith("Legacy evidence draft:")
            assert case["required_answer_points"]
    assert {c["question_id"] for c in cases if not is_answerable(c)} == {"TEST-18", "TEST-19"}
