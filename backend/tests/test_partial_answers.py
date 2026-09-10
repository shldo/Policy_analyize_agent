import json

import pytest
from langchain_core.messages import ToolMessage

from app.core.config import get_settings
from app.modules.chat.rag import parent_pipeline as pipeline
from app.modules.chat.rag.graph.nodes import route_after_evidence_check


@pytest.fixture(autouse=True)
def partial_policy(monkeypatch):
    monkeypatch.setattr(get_settings(), "rag_allow_partial_answers", True)


@pytest.fixture
def packed_setup(monkeypatch):
    children = [dict(chunk_id="a", text="Must train staff.", distance=0.9, reranker_score=-8)]
    monkeypatch.setattr(pipeline, "resolve_generation_parents", lambda c: c)
    monkeypatch.setattr(pipeline, "available_context_tokens", lambda _: 1000)
    monkeypatch.setattr(
        pipeline,
        "pack_generation_context",
        lambda c, **kw: dict(
            context="Must train staff." if c else "",
            citations=[{"chunk_id": "a"}] if c else [],
            generation_parents=[],
            packed_token_count=10,
        ),
    )
    return children


def test_bm25_distance_is_not_a_veto_and_unknown_is_not_complete(packed_setup):
    result = pipeline.prepare_child_context("When and who?", packed_setup)
    assert result["generation_allowed"]
    assert not result["coverage_sufficient"] and not result["evidence_sufficient"]
    assert result["coverage_status"] == "not_assessed"
    assert route_after_evidence_check(dict(result, question="q")) == "generate_answer"


def test_no_context_still_blocks(packed_setup):
    result = pipeline.prepare_child_context("q", [])
    assert not result["generation_allowed"]
    assert route_after_evidence_check(dict(result, question="q")) == "insufficient_evidence"


@pytest.mark.parametrize("missing", [[], [1]])
def test_partial_allowed_without_claiming_complete(monkeypatch, packed_setup, missing):
    monkeypatch.setattr(pipeline, "uncovered_facets", lambda *a: missing)
    trace = dict(inspections=[[{}]], stop_reason="round_limit")
    result = pipeline.prepare_child_context("q", packed_setup, controlled_trace=trace)
    assert result["generation_allowed"]
    assert result["coverage_sufficient"] == (not missing)
    assert result["controlled_trace"]["coverage_sufficient"] == (not missing)
    assert "coverage_sufficient" not in trace


def test_inspector_error_does_not_certify_coverage(monkeypatch, packed_setup):
    monkeypatch.setattr(pipeline, "uncovered_facets", lambda *a: [])
    result = pipeline.prepare_child_context(
        "q",
        packed_setup,
        controlled_trace=dict(inspections=[[{}]], stop_reason="inspection_or_retrieval_error"),
    )
    assert result["generation_allowed"] and not result["coverage_sufficient"]
    assert result["coverage_status"] == "not_assessed"


def test_agent_partial_pack_not_refusal(monkeypatch):
    from app.modules.chat.rag.agent import context

    monkeypatch.setattr(
        context,
        "pack_generation_context",
        lambda *a, **kw: dict(context="Evidence", citations=[{"chunk_id": "a"}]),
    )
    message = ToolMessage(
        content=json.dumps(
            dict(
                controlled_trace=dict(
                    question="q", coverage_sufficient=False, needs=["one", "two"]
                ),
                generation_parents=[],
                results=[],
            )
        ),
        tool_call_id="one",
    )
    output = context.pack_agent_messages([message], "Answer", question="q")
    assert "partial or unverified" in output[0].content
    assert "Evidence gaps" in output[0].content


def test_all_personas_have_partial_answer_instructions():
    from app.modules.chat.rag.agent.prompts import get_agent_system_prompt
    from app.modules.chat.rag.prompts import get_system_prompt

    for mode in ("researcher", "policymaker", "student"):
        assert "Do not refuse the entire question" in get_system_prompt(mode)
        assert "generation_allowed" in get_agent_system_prompt(mode)
