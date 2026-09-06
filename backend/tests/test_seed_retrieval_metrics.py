import pytest

from scripts.evaluate_seed_corpus import score


def test_rank_boundaries():
    ids = [str(i) for i in range(1, 22)]
    assert score(ids, {"5"})["hit_at_5"] == 1
    assert score(ids, {"6"})["hit_at_5"] == 0
    assert score(ids, {"10"})["rr_at_10"] == 0.1
    assert score(ids, {"11"})["rr_at_10"] == 0
    assert score(ids, {"20"})["hit_at_20"] == 1
    assert score(ids, {"21"})["hit_at_20"] == 0


def test_missing_label_and_empty_results():
    assert score([], {"gold"})["first_label_rank"] is None
    assert score(["other"], {"gold"})["rr_at_10"] == 0


def test_invalid_inputs():
    with pytest.raises(ValueError):
        score(["a", "a"], {"a"})
    with pytest.raises(ValueError):
        score(["a"], set())
