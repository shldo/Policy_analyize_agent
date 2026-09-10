import json

import pytest
from langchain_core.messages import HumanMessage, ToolMessage

from app.modules.chat.rag.agent.context import pack_agent_messages


@pytest.fixture(autouse=True)
def strict_policy(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "rag_allow_partial_answers", False)


def test_final_context_keeps_exact_child_number_and_dedupes_parent():
    child = {
        "chunk_id": "c",
        "document_id": "d",
        "text": "Required action.",
        "page_start": 2,
        "page_end": 2,
    }
    parent = {
        "context_id": "s",
        "section_id": "s",
        "document_id": "d",
        "file": "Policy",
        "parent_score": 4,
        "text": "Larger policy context.",
        "supporting_children": [child],
        "supporting_child_ids": ["c"],
    }
    payload = {"generation_parents": [parent], "results": [{"chunk_id": "c", "number": 7}]}
    messages = [
        HumanMessage(content="Question?"),
        ToolMessage(content=json.dumps(payload), tool_call_id="one"),
        ToolMessage(content=json.dumps(payload), tool_call_id="two"),
    ]
    packed = pack_agent_messages(messages, "Answer based on evidence.")
    assert packed[0].content.count("Larger policy context.") == 1
    assert "[7] Child evidence" in packed[0].content
    assert "[1] Child evidence" not in packed[0].content
    assert json.loads(messages[1].content)["generation_parents"]  # No checkpoint mutation.


def test_live_web_payload_unchanged():
    web = ToolMessage(
        content='{"results":[{"source_url":"https://example.org"}]}', tool_call_id="web"
    )
    assert pack_agent_messages([web], "Answer")[-1] == web


@pytest.mark.parametrize(
    "scope,ids,sufficient",
    [("Question", ["a"], True), ("Subquestion", ["a", "b"], True), ("Question", ["a", "b"], False)],
)
def test_agent_final_pack_cannot_bypass_coverage(monkeypatch, scope, ids, sufficient):
    from app.modules.chat.rag.agent import context

    trace = dict(
        question=scope,
        needs=["need"],
        coverage_stage="packed",
        coverage_sufficient=sufficient,
        inspections=[
            [
                dict(
                    need_index=0,
                    status="supported",
                    evidence=[dict(chunk_id=c) for c in ("a", "b")],
                )
            ]
        ],
    )
    tool = ToolMessage(
        content=json.dumps(dict(controlled_trace=trace, generation_parents=[], results=[])),
        tool_call_id="one",
    )
    monkeypatch.setattr(
        context,
        "pack_generation_context",
        lambda *a, **k: dict(context="evidence", citations=[dict(chunk_id=c) for c in ids]),
    )
    with pytest.raises(context.IncompleteControlledEvidence):
        pack_agent_messages([tool], "Answer", question="Question")


def test_later_incomplete_inspection_invalidates_old_agent_success(monkeypatch):
    from app.modules.chat.rag.agent import context

    trace = dict(
        question="q",
        needs=["need"],
        coverage_stage="packed",
        coverage_sufficient=True,
        inspections=[[dict(need_index=0, status="supported", evidence=[dict(chunk_id="a")])]],
    )
    messages = [
        ToolMessage(
            content=json.dumps(
                dict(
                    controlled_trace=dict(trace, coverage_sufficient=flag),
                    generation_parents=[],
                    results=[],
                )
            ),
            tool_call_id=str(flag),
        )
        for flag in (True, False)
    ]
    monkeypatch.setattr(
        context,
        "pack_generation_context",
        lambda *a, **k: dict(context="evidence", citations=[dict(chunk_id="a")]),
    )
    with pytest.raises(context.IncompleteControlledEvidence):
        pack_agent_messages(messages, "Answer", question="q")


def test_agent_core_bundle_is_and_and_packing_loss_refuses(monkeypatch):
    from app.modules.chat.rag.agent import context

    trace = {
        "question": "Question",
        "requirements": [{"requirement_id": "r1", "anchors": ["Question"]}],
        "coverage_stage": "packed",
        "coverage_sufficient": True,
        "core_contract": {
            "requirements": [
                {
                    "requirement_id": "r1",
                    "bundles": [["a", "b"]],
                    "selected_bundle": ["a", "b"],
                    "covered": True,
                }
            ],
            "selected_core_child_ids": ["a", "b"],
            "uncovered_requirements": [],
        },
        "inspections": [
            [
                {
                    "need_index": 0,
                    "requirement_id": "r1",
                    "status": "complete",
                    "evidence_role": "answer_bearing",
                    "evidence": [{"chunk_id": "a"}, {"chunk_id": "b"}],
                }
            ]
        ],
    }
    tool = ToolMessage(
        content=json.dumps(
            {
                "controlled_trace": trace,
                "generation_parents": [],
                "results": [],
            }
        ),
        tool_call_id="one",
    )
    monkeypatch.setattr(
        context,
        "pack_generation_context",
        lambda *a, **k: {"context": "evidence", "citations": [{"chunk_id": "a"}]},
    )
    with pytest.raises(context.IncompleteControlledEvidence):
        pack_agent_messages([tool], "Answer", question="Question")
