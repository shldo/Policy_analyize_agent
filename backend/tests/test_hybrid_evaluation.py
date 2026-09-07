import math
import subprocess
import sys
from pathlib import Path

import pytest

from evaluation.hybrid import BM25Index, reciprocal_rank_fusion, tokenize


@pytest.mark.parametrize("args", [["--run", "--split", "test"], []])
def test_hybrid_cli_blocks_test_exposure_and_validation_only(args):
    result = subprocess.run(
        [sys.executable, "-m", "evaluation.run", "--compare-hybrid", *args],
        cwd=Path(__file__).parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "requires --run --split development" in result.stderr


def test_tokenization_and_missing_terms():
    assert tokenize("MCP / AI-generated １２") == ["mcp", "ai", "generated", "12"]
    index = BM25Index([{"id": "a", "text": "MCP agent"}, {"id": "b", "text": ""}])
    assert index.search("watermark") == []
    assert index.search("") == []
    assert index.search("MCP")[0]["chunk_id"] == "a"
    assert index.search("MCP MCP") == index.search("MCP")


def test_bm25_hand_computed_score_and_stable_tie():
    index = BM25Index([{"id": "b", "text": "agent"}, {"id": "a", "text": "agent"}])
    result = index.search("agent")
    assert [r["chunk_id"] for r in result] == ["a", "b"]
    assert result[0]["bm25_score"] == pytest.approx(math.log(1 + 0.5 / 2.5))
    with pytest.raises(ValueError):
        BM25Index([])
    with pytest.raises(ValueError):
        BM25Index([{"id": "a", "text": "x"}] * 2)
    assert BM25Index([{"id": "a", "text": ""}]).search("x") == []


def test_rrf_rank_formula_deduplication_and_empty_branch():
    a, b = {"chunk_id": "a"}, {"chunk_id": "b"}
    result = reciprocal_rank_fusion([[a, a, b], [b]])
    assert result[0]["chunk_id"] == "b"
    assert result[0]["rrf_score"] == pytest.approx(1 / 62 + 1 / 61)
    assert result[1]["rrf_score"] == pytest.approx(1 / 61)
    assert len(reciprocal_rank_fusion([[a, b], []], limit=1)) == 1
    assert reciprocal_rank_fusion([[], []]) == []
    with pytest.raises(ValueError):
        reciprocal_rank_fusion([[a]], limit=0)
