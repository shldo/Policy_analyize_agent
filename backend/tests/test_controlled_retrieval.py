import pytest

from app.modules.documents.controlled_retrieval import (
    evidence_spans,
    resolve_span_inspection,
    run_controlled,
    validate_inspection,
)


def test_spans_resolve_to_original_and_query_cannot_be_invented():
    child = {"chunk_id": "c", "text": "Must act. May defer.\nExcept emergencies."}
    spans = evidence_spans([child])
    assert all(s["quote"] in child["text"] for s in spans.values())
    value = {
        "items": [
            {
                "need_index": 0,
                "status": "partial",
                "span_ids": ["0:0"],
                "query": "judicial precedent invented",
            }
        ]
    }
    result = resolve_span_inspection(value, spans, "What actions and exceptions?", ["exceptions"])
    assert result["items"][0]["evidence"] == [{"chunk_id": "c", "quote": "Must act."}]
    assert result["items"][0]["query"] == "What actions and exceptions?\nFocus: exceptions"
    value["items"][0]["span_ids"] = ["invented"]
    with pytest.raises(ValueError):
        resolve_span_inspection(value, spans, "q", ["need"])


def item(index, status, child=None, query=""):
    return dict(
        need_index=index,
        status=status,
        query=query,
        evidence=[] if child is None else [dict(chunk_id=child, quote=child)],
    )


def test_gap_retrieval_preserves_first_support_and_stops():
    calls = []
    a, b = dict(chunk_id="a", text="a"), dict(chunk_id="b", text="b")

    def retrieve(q, original):
        calls.append(q)
        return [a] if q == original else [b]

    def inspect(q, needs, children):
        return {
            "items": [
                item(0, "supported", "a"),
                item(1, "supported", "b")
                if len(children) == 2
                else item(1, "missing", query="gap"),
            ]
        }

    result, trace = run_controlled(
        "q", plan=lambda q: {"needs": ["one", "two"]}, retrieve=retrieve, inspect=inspect, limit=2
    )
    assert calls == ["q", "gap"]
    assert [c["chunk_id"] for c in result] == ["a", "b"]
    assert trace["stop_reason"] == "coverage_sufficient"
    assert trace["uncovered_needs"] == []


def test_inspection_rejects_invented_quote():
    with pytest.raises(ValueError):
        validate_inspection(
            {"items": [item(0, "supported", "invented")]},
            ["need"],
            [{"chunk_id": "real", "text": "real"}],
        )


def test_no_gain_does_not_loop():
    child = dict(chunk_id="a", text="a")
    _, trace = run_controlled(
        "q",
        plan=lambda q: {"needs": ["need"]},
        retrieve=lambda q, original: [child],
        inspect=lambda *args: {"items": [item(0, "missing", query="gap")]},
    )
    assert trace["queries"] == ["q", "gap"]
    assert trace["stop_reason"] == "no_new_evidence"


def test_invalid_plan_falls_back_to_first_retrieval():
    result, trace = run_controlled(
        "q",
        plan=lambda q: {"needs": []},
        retrieve=lambda *args: [dict(chunk_id="a", text="a")],
        inspect=lambda *args: None,
    )
    assert result[0]["chunk_id"] == "a"
    assert trace["stop_reason"] == "inspection_or_retrieval_error"


def test_deadline_stops_before_inspection():
    ticks = iter([0, 91])
    result, trace = run_controlled(
        "q",
        plan=lambda q: {"needs": ["need"]},
        retrieve=lambda *a: [dict(chunk_id="a", text="a")],
        inspect=lambda *a: pytest.fail("must not inspect after deadline"),
        clock=lambda: next(ticks),
    )
    assert result and trace["stop_reason"] == "time_budget"


def test_selected_budget_cannot_claim_complete_coverage():
    children = [dict(chunk_id=c, text=c) for c in ["a", "b"]]
    _, trace = run_controlled(
        "q",
        plan=lambda q: {"needs": ["one", "two"]},
        retrieve=lambda *a: children,
        inspect=lambda *a: {"items": [item(0, "supported", "a"), item(1, "supported", "b")]},
        limit=1,
    )
    assert trace["stop_reason"] == "selection_budget"
    assert trace["uncovered_needs"] == [1]
