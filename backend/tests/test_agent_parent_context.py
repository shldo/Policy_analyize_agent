import json

from langchain_core.messages import HumanMessage, ToolMessage

from app.modules.chat.rag.agent.context import pack_agent_messages


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
