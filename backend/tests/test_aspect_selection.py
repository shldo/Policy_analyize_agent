from app.modules.documents.aspect_selection import allocate_aspects


def test_lower_global_rank_gets_aspect_slot_without_increasing_limit():
    rows = [dict(chunk_id=str(i), distance=0.2, reranker_score=10 - i) for i in range(16)]
    result = allocate_aspects(
        rows, [rows[:3], [rows[15], rows[14]]], limit=8, distance_threshold=0.7, score_threshold=-7
    )
    assert len(result) == 8
    assert "15" in [c["chunk_id"] for c in result]
    assert result[1]["reranker_score"] == -5  # original, not aspect score


def test_aspect_scores_cannot_bypass_original_gate_and_duplicates():
    rows = [
        dict(chunk_id="a", distance=0.2, reranker_score=1),
        dict(chunk_id="b", distance=0.8, reranker_score=1),
        dict(chunk_id="c", distance=0.2, reranker_score=-8),
    ]
    aspects = [[dict(c, reranker_score=10) for c in rows], [rows[0]]]
    result = allocate_aspects(rows, aspects, limit=8, distance_threshold=0.7, score_threshold=-7)
    assert [c["chunk_id"] for c in result] == ["a"]
