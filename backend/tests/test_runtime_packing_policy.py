import json

import pytest
from langchain_core.messages import HumanMessage, ToolMessage
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.modules.chat.rag import parent_pipeline
from app.modules.chat.rag.agent import context as agent_context
from app.modules.chat.rag.agent import tools as agent_tools
from app.modules.chat.rag.graph import nodes


@pytest.fixture
def children(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "rag_allow_partial_answers", True)
    monkeypatch.setattr(settings, "controlled_retrieval_enabled", False)
    monkeypatch.setattr(settings, "rag_packing_policy", "per_document_backfill_v1")
    monkeypatch.setattr(settings, "max_parents_per_document", 1)
    monkeypatch.setattr(settings, "parent_context_k", 8)
    # Legacy Child fixtures use the real Parent resolver without DB or model calls.
    return [
        dict(
            chunk_id=f"c{i}",
            document_id="doc",
            text=f"Required obligation {i}.",
            file="Policy",
            page_start=i + 1,
            page_end=i + 1,
            reranker_score=3 - i,
        )
        for i in range(3)
    ]


def test_setting_default_validation_and_explicit_rollback(monkeypatch, children):
    monkeypatch.delenv("RAG_PACKING_POLICY", raising=False)
    assert Settings(_env_file=None).rag_packing_policy == "original"
    with pytest.raises(ValidationError):
        Settings(_env_file=None, rag_packing_policy="unknown")
    configured = parent_pipeline.prepare_child_context("q", children)
    rollback = parent_pipeline.prepare_child_context("q", children, packing_policy="original")
    assert len(configured["citations"]) == 3
    assert len(rollback["citations"]) == 1
    assert configured["generation_allowed"] and not configured["coverage_sufficient"]
    assert configured["coverage_status"] == "not_assessed"


def test_classic_node_preserves_policy_and_prompt_history_budget(monkeypatch, children):
    overheads = []
    real_budget = parent_pipeline.available_context_tokens

    def capture(overhead):
        overheads.append(overhead)
        return real_budget(overhead)

    monkeypatch.setattr(parent_pipeline, "available_context_tokens", capture)
    result = nodes.check_evidence_node(
        dict(
            question="q",
            raw_chunks=children,
            used_vector_retrieval=True,
            history=[{"content": "history-marker"}],
        )
    )
    assert result["packing_policy"] == "per_document_backfill_v1"
    assert len(result["citations"]) == 3
    assert "history-marker" in overheads[0] and len(overheads[0]) > len("history-marker")


@pytest.mark.asyncio
@pytest.mark.parametrize("full_corpus", [False, True])
async def test_agent_tools_and_final_pack_share_policy(monkeypatch, children, full_corpus):
    monkeypatch.setattr(agent_tools, "search_full_corpus_service", lambda *a, **k: children)
    monkeypatch.setattr(agent_tools, "load_documents_node", lambda state: {"pages": []})
    # Selected tool runs the real Classic evidence node; only retrieval I/O is replaced.
    monkeypatch.setattr(
        agent_tools,
        "retrieve_context_node",
        lambda state: dict(
            raw_chunks=children, chunks=children, citations=[], used_vector_retrieval=True
        ),
    )
    kwargs = dict(
        query="q",
        decision_reason="policy lookup",
        tool_call_id="call",
        top_k=8,
        include_restricted=False,
        citations=[],
        evidence_sources=[],
        turn_citation_keys=[],
    )
    if full_corpus:
        command = await agent_tools.search_full_corpus.coroutine(**kwargs)
    else:
        command = await agent_tools.search_internal_documents.coroutine(
            **kwargs, document_ids=["doc"], filenames=[]
        )
    tool_message = command.update["messages"][0]
    payload = json.loads(tool_message.content)
    assert len(payload["results"]) == 3
    assert not payload["coverage_sufficient"]
    messages = [HumanMessage(content="history-marker"), tool_message]
    final = agent_context.pack_agent_messages(messages, "system-marker", question="q")
    assert all(f"[{i}] Child evidence" in final[0].content for i in (1, 2, 3))
    assert "system-marker" in final[0].content
    assert messages[1] == tool_message  # Checkpoint remains untouched.
    monkeypatch.setattr(get_settings(), "rag_packing_policy", "original")
    rollback = agent_context.pack_agent_messages(messages, "system-marker", question="q")
    assert rollback[0].content.count("Child evidence, pages") == 1
    assert "Earlier tool coverage claims" in rollback[0].content


def test_final_budget_loss_reports_gap_and_keeps_web_unchanged(monkeypatch, children, caplog):
    packed = parent_pipeline.prepare_child_context("q", children)
    payload = dict(
        generation_parents=packed["generation_parents"],
        results=[
            dict(chunk_id=c["chunk_id"], number=i + 1) for i, c in enumerate(packed["citations"])
        ],
    )
    tool = ToolMessage(content=json.dumps(payload), tool_call_id="doc")
    web = ToolMessage(
        content='{"results":[{"source_url":"https://example.org"}]}', tool_call_id="web"
    )
    overheads = []

    def no_budget(overhead):
        overheads.append(overhead)
        return 0

    monkeypatch.setattr(agent_context, "available_context_tokens", no_budget)
    with caplog.at_level("INFO"):
        final = agent_context.pack_agent_messages(
            [HumanMessage(content="history-marker"), tool, web], "system-marker", question="q"
        )
    assert "system-marker" in overheads[0] and "history-marker" in overheads[0]
    assert "Do not assert document facts" in final[0].content
    assert "lost_children=3" in caplog.text
    assert final[-1] == web
    assert "[1] Child evidence" not in final[0].content
