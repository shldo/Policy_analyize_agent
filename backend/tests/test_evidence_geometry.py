from evaluation.evidence_geometry import minimum_cover


def test_minimum_evidence_cover_not_number_of_groups():
    assert minimum_cover([{"a", "b"}, {"b", "c"}]) == 1
    assert minimum_cover([{"a"}, {"b"}, {"a", "c"}]) == 2
