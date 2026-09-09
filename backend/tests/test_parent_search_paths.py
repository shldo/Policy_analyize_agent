import json

import pytest

from app.modules.chat.rag.agent import tools
from app.modules.chat.rag.graph import nodes


@pytest.mark.asyncio
async def test_full_corpus_and_classic_delegate_to_same_child_pipeline(monkeypatch):
    observed = []
    children = [{"chunk_id": "c", "text": "evidence"}]

    def prepare(question, candidates, **kwargs):
        observed.append((question, candidates))
        return {
            "evidence_sufficient": False,
            "evidence_reason": "test gate",
            "generation_parents": [],
            "citations": [],
        }

    monkeypatch.setattr(nodes, "prepare_child_context", prepare)
    monkeypatch.setattr(tools, "prepare_child_context", prepare)
    monkeypatch.setattr(tools, "search_full_corpus_service", lambda *a, **kw: children)
    nodes.check_evidence_node(
        {"question": "q", "raw_chunks": children, "used_vector_retrieval": True}
    )
    result = await tools.search_full_corpus.coroutine(
        query="q",
        decision_reason="search library",
        tool_call_id="tool",
        top_k=8,
        include_restricted=False,
        citations=[],
        evidence_sources=[],
        turn_citation_keys=[],
    )
    assert observed == [("q", children), ("q", children)]
    assert not json.loads(result.update["messages"][0].content)["evidence_sufficient"]
