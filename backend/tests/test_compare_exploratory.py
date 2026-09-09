import pytest

from evaluation.compare_exploratory import STAGES, compare


def test_paired_denominator_excludes_mapping_failure_on_either_side():
    report = dict(
        dataset_sha256="same",
        selected_ids=["a", "b"],
        generation_target="model",
        embedding_model="embedding",
        candidate_k=30,
        rerank_k=8,
        status="completed",
        corpus_unchanged=True,
    )
    row = dict(
        category="multi_child",
        mapping_status="mapped",
        status="completed",
        **{stage: {"hit_at_5": 1.0} for stage in STAGES},
    )
    a = {"a": row, "b": row}
    b = {"a": row, "b": {**row, "reranked_scores": None}}
    result = compare(report, report, a, b)
    assert result["common_denominator"] == 1
    assert result["excluded_ids"] == ["b"]
    with pytest.raises(ValueError, match="generation_target"):
        compare(report, {**report, "generation_target": "other"}, a, b)
