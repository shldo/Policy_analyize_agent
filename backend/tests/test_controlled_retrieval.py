import pytest

from app.modules.documents.controlled_retrieval import (
    build_evidence_set,
    decompose_requirements,
    evidence_spans,
    fuse_coverage,
    optimize_gap_queries,
    question_span_catalog,
    resolve_span_inspection,
    run_controlled,
    uncovered_facets,
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


def test_final_inspection_supersedes_stale_first_bundle():
    children = [dict(chunk_id=c, text=c) for c in ("old", "new", "condition")]
    first = [item(0, "supported", "old"), item(1, "missing")]
    final = [item(0, "supported", "new"), item(1, "supported", "condition")]
    selected, missing = fuse_coverage(children[:1], children, first, final, 2)
    assert [c["chunk_id"] for c in selected] == ["new", "condition"]
    assert missing == []


def test_fusion_prefers_marginal_facets_over_duplicate_relevance():
    children = [dict(chunk_id=c, text=c) for c in ("a", "b", "shared")]
    final = [
        item(0, "supported", "a"),
        item(1, "supported", "shared"),
        item(2, "supported", "shared"),
    ]
    selected, missing = fuse_coverage(children, children, final, final, 1)
    assert selected[0]["chunk_id"] == "shared"
    assert missing == [0]


@pytest.mark.parametrize(
    "direct,complete,status",
    [(False, True, "background"), (True, False, "partial"), (True, True, "supported")],
)
def test_complete_support_requires_direct_and_complete(direct, complete, status):
    needs = [{"anchor": "media", "facet": "condition"}]
    result = resolve_span_inspection(
        {
            "items": [
                dict(
                    need_index=0,
                    status="supported",
                    direct_support=direct,
                    complete_support=complete,
                    span_ids=["0:0"],
                )
            ]
        },
        evidence_spans([dict(chunk_id="a", text="General transparency.")]),
        "media",
        needs,
    )
    assert result["items"][0]["status"] == status
    trace = dict(needs=needs, inspections=[result["items"]])
    assert uncovered_facets(trace, {"a"}) == ([] if status == "supported" else [0])


def test_decomposition_is_anchored_and_closed():
    plan = {"requirements": [{"anchor": "media provisions", "facets": ["mechanism", "condition"]}]}
    needs = decompose_requirements(plan, "What media provisions apply?")["needs"]
    assert [n["need_index"] for n in needs] == [0, 1]
    assert needs[0]["anchor"] == needs[1]["anchor"]
    with pytest.raises(ValueError):
        decompose_requirements(plan, "Unrelated question")
    plan["requirements"][0]["facets"] = ["invented law"]
    with pytest.raises(ValueError):
        decompose_requirements(plan, "What media provisions apply?")


def test_multi_child_requirement_cannot_be_certified_by_one_child():
    entry = item(0, "supported", "a")
    entry["evidence"].append(dict(chunk_id="b", quote="b"))
    trace = dict(needs=["mechanism"], inspections=[[entry]])
    assert uncovered_facets(trace, {"a"}) == [0]
    assert uncovered_facets(trace, {"a", "b"}) == []


def test_v4_planner_binds_enumeration_and_comparison_without_fabrication():
    question = "Which reports, audits, and notices are required?"
    plan = {
        "question_type": "enumeration",
        "requirements": [
            {"requirement_id": "r1", "anchors": ["reports"]},
            {"requirement_id": "r2", "anchors": ["audits"]},
            {"requirement_id": "r3", "anchors": ["notices"]},
        ],
    }
    assert [
        r["requirement_id"] for r in decompose_requirements(plan, question)["requirements"]
    ] == [
        "r1",
        "r2",
        "r3",
    ]
    with pytest.raises(ValueError):
        decompose_requirements(
            {
                "question_type": "enumeration",
                "requirements": [
                    {"requirement_id": "r1", "anchors": [question]},
                    {"requirement_id": "r2", "anchors": [question]},
                ],
            },
            question,
        )
    with pytest.raises(ValueError):
        decompose_requirements(
            {"requirements": [{"requirement_id": "r1", "anchors": ["invented"]}]},
            question,
        )
    comparison = decompose_requirements(
        {
            "question_type": "comparison",
            "comparison_subjects": ["Alpha", "Beta"],
            "requirements": [
                {
                    "requirement_id": "r1",
                    "anchors": ["Alpha"],
                    "subject_anchors": ["Alpha"],
                    "dimension_anchors": ["cost"],
                },
                {
                    "requirement_id": "r2",
                    "anchors": ["Beta"],
                    "subject_anchors": ["Beta"],
                    "dimension_anchors": ["cost"],
                },
            ],
        },
        "Compare Alpha and Beta on cost?",
    )
    assert comparison["comparison_subjects"] == ["Alpha", "Beta"]


def test_v5_planner_normalizes_optional_fields_without_faking_requirements():
    question = "When must agencies implement training?"
    normalized = decompose_requirements(
        {
            "question_type": "MIXED",
            "requirements": [
                {
                    "requirement_id": "r1",
                    "anchors": ["when", "must", "agencies", "implement", "training"],
                    "subject_anchors": "agencies",
                    "dimension_anchors": ["when"],
                    "modality": "MUST",
                    "modality_anchor": "must",
                    "metadata": {"timeframe": ["invented"]},
                }
            ],
        },
        question,
    )["requirements"][0]
    assert normalized["anchors"] == ["When", "must", "agencies", "implement", "training"]
    assert normalized["subject_anchors"] == ["agencies"]
    assert normalized["dimension_anchors"] == ["When"]
    assert normalized["modality"] == "must"
    assert normalized["modality_anchor"] == ["must"]
    assert "metadata" not in normalized

    optional_noise = decompose_requirements(
        {
            "question_type": "simple",
            "requirements": [
                {
                    "requirement_id": "r1",
                    "anchors": ["training"],
                    "dimension_anchors": ["not in question"],
                    "modality": "expected",
                    "modality_anchor": "expected",
                }
            ],
        },
        question,
    )["requirements"][0]
    assert optional_noise["modality"] == "neutral"
    assert "dimension_anchors" not in optional_noise
    assert "modality_anchor" not in optional_noise

    with pytest.raises(ValueError):
        decompose_requirements(
            {
                "question_type": "comparison",
                "comparison_subjects": ["Alpha"],
                "requirements": [{"requirement_id": "r1", "anchors": ["Alpha"]}],
            },
            "Compare Alpha and Beta?",
        )

    with pytest.raises(ValueError):
        decompose_requirements(
            {
                "question_type": "enumeration",
                "requirements": [
                    {"requirement_id": "r1", "anchors": [question]},
                    {"requirement_id": "r2", "anchors": [question]},
                ],
            },
            question,
        )


def test_v4_query_optimizer_rejects_unbound_terms_and_limits_gap_queries():
    children = [{"chunk_id": "a", "text": "Reporting is mandatory.", "section_title": "Controls"}]
    requirements = [
        {"requirement_id": "r1", "anchors": ["reporting"]},
        {"requirement_id": "r2", "anchors": ["mandatory"]},
        {"requirement_id": "r3", "anchors": ["Controls"]},
    ]
    inspection = [
        {
            "requirement_id": "r1",
            "status": "missing",
            "gap_terms": [{"source_type": "span", "span_id": "0:0", "term": "Reporting"}],
        },
        {
            "requirement_id": "r2",
            "status": "missing",
            "gap_terms": [{"source_type": "span", "span_id": "0:0", "term": "new entity"}],
        },
        {"requirement_id": "r3", "status": "missing", "gap_terms": []},
    ]
    selected, trace = optimize_gap_queries("What reporting?", requirements, inspection, children)
    assert len(selected) == 2
    assert selected[0][1]["sources"][0]["source"] == "span"
    assert selected[1][1]["fallback"] is True
    assert "new entity" not in selected[1][0]
    assert trace[1]["errors"]


def test_v4_validator_accepts_negative_answer_and_normalizes_empty_background():
    children = [{"chunk_id": "a", "text": "No filing is required."}]
    requirements = [{"requirement_id": "r1", "anchors": ["filing"]}]
    complete = validate_inspection(
        {
            "items": [
                {
                    "requirement_id": "r1",
                    "status": "complete",
                    "evidence_role": "answer_bearing",
                    "modality_conclusion": "negative",
                    "core_bundles": [["0:0"]],
                }
            ]
        },
        requirements,
        children,
    )
    assert complete[0]["status"] == "complete"
    assert complete[0]["modality_conclusion"] == "negative"
    normalized = validate_inspection(
        {
            "items": [
                {"requirement_id": "r1", "status": "background", "evidence_role": "background"}
            ]
        },
        requirements,
        children,
    )
    assert normalized[0]["status"] == "missing"
    assert "background_without_spans" in normalized[0]["normalizations"]
    with pytest.raises(ValueError):
        validate_inspection(
            {
                "items": [
                    {
                        "requirement_id": "r1",
                        "status": "complete",
                        "core_bundles": [["invented"]],
                    }
                ]
            },
            requirements,
            children,
        )


def test_v4_builder_implements_or_and_shared_child_without_stale_or_supporting_pressure():
    children = [
        {"chunk_id": "old", "text": "old"},
        {"chunk_id": "a", "text": "a"},
        {"chunk_id": "b", "text": "b"},
        {"chunk_id": "c", "text": "c"},
        {"chunk_id": "shared", "text": "shared"},
    ]
    requirements = [
        {"requirement_id": "r1", "anchors": ["one"]},
        {"requirement_id": "r2", "anchors": ["two"]},
    ]
    inspection = validate_inspection(
        {
            "items": [
                {
                    "requirement_id": "r1",
                    "status": "complete",
                    "core_bundles": [["1:0"], ["2:0", "3:0"]],
                    "supporting_span_ids": ["0:0"],
                },
                {"requirement_id": "r2", "status": "complete", "core_bundles": [["4:0"]]},
            ]
        },
        requirements,
        children,
    )
    selected, contract = build_evidence_set(children, inspection, limit=2)
    assert [child["chunk_id"] for child in selected] == ["a", "shared"]
    assert contract["uncovered_requirements"] == []
    assert contract["requirements"][0]["selected_bundle"] == ["a"]
    assert "old" not in contract["selected_core_child_ids"]

    and_only, and_contract = build_evidence_set(
        children,
        [
            {
                "requirement_id": "r1",
                "status": "complete",
                "core_bundles": [
                    [
                        {"span_id": "2:0", "chunk_id": "b", "quote": "b"},
                        {"span_id": "3:0", "chunk_id": "c", "quote": "c"},
                    ]
                ],
            }
        ],
        limit=1,
    )
    assert [child["chunk_id"] for child in and_only] == ["old"]
    assert and_contract["selected_core_child_ids"] == []
    assert and_contract["uncovered_requirements"] == ["r1"]


def test_v4_run_keeps_requirement_bound_gap_and_final_core_contract():
    question = "Which reports and audits are required?"
    report = {"chunk_id": "report", "text": "Reports are required."}
    audit = {"chunk_id": "audit", "text": "Audits are required."}
    calls = []

    def retrieve(query, original):
        calls.append(query)
        return [report] if query == original else [audit]

    def inspect(query, requirements, children):
        del query
        if len(children) == 1:
            return {
                "items": [
                    {
                        "requirement_id": "r1",
                        "status": "complete",
                        "core_bundles": [["0:0"]],
                    },
                    {
                        "requirement_id": "r2",
                        "status": "missing",
                        "gap_terms": [{"source_type": "anchor", "term": "audits"}],
                    },
                ]
            }
        return {
            "items": [
                {"requirement_id": "r1", "status": "complete", "core_bundles": [["0:0"]]},
                {"requirement_id": "r2", "status": "complete", "core_bundles": [["1:0"]]},
            ]
        }

    selected, trace = run_controlled(
        question,
        plan=lambda _: {
            "question_type": "enumeration",
            "requirements": [
                {"requirement_id": "r1", "anchors": ["reports"]},
                {"requirement_id": "r2", "anchors": ["audits"]},
            ],
        },
        retrieve=retrieve,
        inspect=inspect,
        limit=2,
    )
    assert calls[0] == question
    assert len(calls) == 2
    assert "audits" in calls[1]
    assert [child["chunk_id"] for child in selected] == ["report", "audit"]
    assert trace["core_contract"]["uncovered_requirements"] == []
    assert trace["query_trace"][0]["sources"][0]["source"] == "question_anchor"


def test_builder_keeps_valid_or_alternatives_and_all_and_members():
    children = [
        {"chunk_id": "a", "text": "a"},
        {"chunk_id": "b", "text": "b"},
        {"chunk_id": "c", "text": "c"},
    ]
    inspection = [
        {
            "requirement_id": "r1",
            "status": "complete",
            "evidence_role": "answer_bearing",
            "core_bundles": [
                [{"span_id": "0:0", "chunk_id": "a", "quote": "a"}],
                [{"span_id": "1:0", "chunk_id": "b", "quote": "b"}],
            ],
        },
        {
            "requirement_id": "r2",
            "status": "complete",
            "evidence_role": "answer_bearing",
            "core_bundles": [[{"span_id": "2:0", "chunk_id": "c", "quote": "c"}]],
        },
    ]
    selected, contract = build_evidence_set(children, inspection, limit=2)
    selected_ids = {child["chunk_id"] for child in selected}
    r1 = contract["requirements"][0]
    assert r1["selected_bundle"] in (["a"], ["b"])
    assert set(r1["selected_bundle"]) <= selected_ids
    assert contract["requirements"][1]["selected_bundle"] == ["c"]
    assert contract["uncovered_requirements"] == []


def test_builder_rejects_invalid_final_inspection_identity_and_status():
    children = [{"chunk_id": "a", "text": "a"}]
    selected, contract = build_evidence_set(
        children,
        [
            {
                "requirement_id": "r9",
                "status": "complete",
                "evidence_role": "answer_bearing",
                "core_bundles": [[{"span_id": "0:0", "chunk_id": "a", "quote": "a"}]],
            }
        ],
    )
    assert selected
    assert contract["selected_core_child_ids"] == []
    assert contract["uncovered_requirements"] == ["r1"]

    selected, contract = build_evidence_set(
        children,
        [
            {
                "requirement_id": "r1",
                "status": "partial",
                "evidence_role": "answer_bearing",
                "core_bundles": [[{"span_id": "0:0", "chunk_id": "a", "quote": "a"}]],
            }
        ],
    )
    assert selected
    assert contract["selected_core_child_ids"] == []
    assert contract["uncovered_requirements"] == ["r1"]


def test_comparison_requires_each_side_to_be_bound():
    with pytest.raises(ValueError, match="(?i)comparison"):
        decompose_requirements(
            {
                "question_type": "comparison",
                "comparison_subjects": ["Alpha", "Beta"],
                "requirements": [
                    {
                        "requirement_id": "r1",
                        "anchors": ["Alpha"],
                        "subject_anchors": ["Alpha"],
                        "dimension_anchors": ["cost"],
                    }
                ],
            },
            "Compare Alpha and Beta on cost?",
        )


def test_comparison_allows_multiple_requirements_per_subject_and_dimension():
    question = "Compare Alpha and Beta on cost and speed?"
    normalized = decompose_requirements(
        {
            "question_type": "comparison",
            "comparison_subjects": ["Alpha", "Beta"],
            "requirements": [
                {
                    "requirement_id": "r1",
                    "anchors": ["Alpha", "cost"],
                    "subject_anchors": ["Alpha"],
                    "dimension_anchors": ["cost"],
                },
                {
                    "requirement_id": "r2",
                    "anchors": ["Alpha", "speed"],
                    "subject_anchors": ["Alpha"],
                    "dimension_anchors": ["speed"],
                },
                {
                    "requirement_id": "r3",
                    "anchors": ["Beta", "cost"],
                    "subject_anchors": ["Beta"],
                    "dimension_anchors": ["cost"],
                },
                {
                    "requirement_id": "r4",
                    "anchors": ["Beta", "speed"],
                    "subject_anchors": ["Beta"],
                    "dimension_anchors": ["speed"],
                },
            ],
        },
        question,
    )
    assert [item["requirement_id"] for item in normalized["requirements"]] == [
        "r1",
        "r2",
        "r3",
        "r4",
    ]


def test_comparison_recovers_unique_subject_from_exact_anchor_and_records_source():
    question = "Compare Alpha and Beta on cost and speed?"
    normalized = decompose_requirements(
        {
            "question_type": "comparison",
            "comparison_subjects": ["Alpha", "Beta"],
            "requirements": [
                {
                    "requirement_id": "r1",
                    "anchors": ["Alpha", "cost"],
                    "dimension_anchors": ["cost"],
                },
                {
                    "requirement_id": "r2",
                    "anchors": ["Alpha", "speed"],
                    "dimension_anchors": ["speed"],
                },
                {
                    "requirement_id": "r3",
                    "anchors": ["Beta", "cost"],
                    "dimension_anchors": ["cost"],
                },
                {
                    "requirement_id": "r4",
                    "anchors": ["Beta", "speed"],
                    "dimension_anchors": ["speed"],
                },
            ],
        },
        question,
    )
    assert [item["subject_anchors"] for item in normalized["requirements"]] == [
        ["Alpha"],
        ["Alpha"],
        ["Beta"],
        ["Beta"],
    ]
    assert all(
        item["binding_sources"]["subject_anchors"] == "unique_comparison_anchor"
        for item in normalized["requirements"]
    )


def test_comparison_requires_a_bound_dimension_for_each_requirement():
    with pytest.raises(ValueError, match="(?i)dimension"):
        decompose_requirements(
            {
                "question_type": "comparison",
                "comparison_subjects": ["Alpha", "Beta"],
                "requirements": [
                    {
                        "requirement_id": "r1",
                        "anchors": ["Alpha"],
                        "subject_anchors": ["Alpha"],
                    },
                    {
                        "requirement_id": "r2",
                        "anchors": ["Beta"],
                        "subject_anchors": ["Beta"],
                        "dimension_anchors": ["cost"],
                    },
                ],
            },
            "Compare Alpha and Beta on cost?",
        )


def test_comparison_rejects_missing_requested_dimension_for_one_side():
    with pytest.raises(ValueError, match="(?i)dimension"):
        decompose_requirements(
            {
                "question_type": "comparison",
                "comparison_subjects": ["Alpha", "Beta"],
                "requirements": [
                    {
                        "requirement_id": "r1",
                        "anchors": ["Alpha", "cost"],
                        "subject_anchors": ["Alpha"],
                        "dimension_anchors": ["cost"],
                    },
                    {
                        "requirement_id": "r2",
                        "anchors": ["Alpha", "speed"],
                        "subject_anchors": ["Alpha"],
                        "dimension_anchors": ["speed"],
                    },
                    {
                        "requirement_id": "r3",
                        "anchors": ["Beta", "cost"],
                        "subject_anchors": ["Beta"],
                        "dimension_anchors": ["cost"],
                    },
                ],
            },
            "Compare Alpha and Beta on cost and speed?",
        )


def test_enumeration_requires_independent_decomposition():
    with pytest.raises(ValueError, match="(?i)enumeration"):
        decompose_requirements(
            {
                "question_type": "enumeration",
                "requirements": [{"requirement_id": "r1", "anchors": ["reports"]}],
            },
            "Which reports, audits, and notices are required?",
        )


def test_single_requirement_can_retain_multiple_scenario_conditions():
    normalized = decompose_requirements(
        {
            "question_type": "enumeration",
            "requirements": [
                {
                    "requirement_id": "r1",
                    "anchors": ["safeguards"],
                    "condition_anchors": ["external vendor", "sensitive customer data"],
                }
            ],
        },
        "For an external vendor handling sensitive customer data, what safeguards apply?",
    )
    assert normalized["requirements"][0]["condition_anchors"] == [
        "external vendor",
        "sensitive customer data",
    ]


def test_yes_no_requires_a_content_bearing_proposition_anchor():
    with pytest.raises(ValueError, match="(?i)yes/no|proposition"):
        decompose_requirements(
            {
                "question_type": "yes_no",
                "requirements": [
                    {
                        "requirement_id": "r1",
                        "anchors": ["Does"],
                        "modality": "yes_no",
                        "modality_anchor": ["Does"],
                    }
                ],
            },
            "Does the policy require agencies to publish a transparency statement?",
        )
    normalized = decompose_requirements(
        {
            "question_type": "yes_no",
            "requirements": [
                {
                    "requirement_id": "r1",
                    "anchors": ["policy", "require", "agencies", "publish", "statement"],
                    "modality": "yes_no",
                    "modality_anchor": ["Does"],
                }
            ],
        },
        "Does the policy require agencies to publish a transparency statement?",
    )
    assert normalized["requirements"][0]["modality"] == "yes_no"


def test_exception_requirement_requires_an_explicit_related_object_or_scope():
    with pytest.raises(ValueError, match="(?i)exception.*(object|scope|condition)"):
        decompose_requirements(
            {
                "question_type": "yes_no",
                "requirements": [
                    {
                        "requirement_id": "r1",
                        "anchors": ["exception"],
                        "modality": "exception",
                        "modality_anchor": ["exception"],
                    }
                ],
            },
            "What exception applies to watermarking?",
        )
    normalized = decompose_requirements(
        {
            "question_type": "yes_no",
            "requirements": [
                {
                    "requirement_id": "r1",
                    "anchors": ["exception", "watermarking"],
                    "object_anchors": ["watermarking"],
                    "condition_anchors": ["team logo"],
                    "modality": "exception",
                    "modality_anchor": ["exception"],
                }
            ],
        },
        "What exception applies to watermarking for a team logo?",
    )
    assert normalized["requirements"][0]["object_anchors"] == ["watermarking"]


def test_exception_can_reference_the_previous_requirement_object():
    normalized = decompose_requirements(
        {
            "question_type": "yes_no",
            "requirements": [
                {
                    "requirement_id": "r1",
                    "anchors": ["watermarking"],
                    "modality": "required",
                    "modality_anchor": ["required"],
                },
                {
                    "requirement_id": "r2",
                    "anchors": ["exception"],
                    "modality": "exception",
                    "modality_anchor": ["exception"],
                },
            ],
        },
        "Is watermarking required, and what exception applies?",
    )
    assert normalized["requirements"][0]["object_anchors"] == ["watermarking"]
    assert normalized["requirements"][1]["object_anchors"] == ["watermarking"]
    assert (
        normalized["requirements"][1]["binding_sources"]["object_anchors"]
        == "previous_requirement_object"
    )


def test_complementary_bundles_cannot_be_treated_as_or_alternatives():
    children = [
        {"chunk_id": "subject", "text": "subject"},
        {"chunk_id": "condition", "text": "condition"},
    ]
    selected, contract = build_evidence_set(
        children,
        [
            {
                "requirement_id": "r1",
                "status": "complete",
                "evidence_role": "answer_bearing",
                "bundle_relation": "complementary",
                "core_bundles": [
                    [{"span_id": "0:0", "chunk_id": "subject", "quote": "subject"}],
                    [{"span_id": "1:0", "chunk_id": "condition", "quote": "condition"}],
                ],
            }
        ],
    )
    assert selected
    assert contract["selected_core_child_ids"] == []
    assert contract["uncovered_requirements"] == ["r1"]
    with pytest.raises(ValueError, match="Complementary"):
        validate_inspection(
            {
                "items": [
                    {
                        "requirement_id": "r1",
                        "status": "complete",
                        "evidence_role": "answer_bearing",
                        "bundle_relation": "complementary",
                        "core_bundles": [["0:0"], ["1:0"]],
                    }
                ]
            },
            [{"requirement_id": "r1", "anchors": ["subject"]}],
            children,
        )


def test_raw_inspection_adapter_preserves_bundle_relation_and_fails_closed():
    children = [
        {"chunk_id": "subject", "text": "subject"},
        {"chunk_id": "condition", "text": "condition"},
    ]
    spans = evidence_spans(children)
    requirements = [{"requirement_id": "r1", "anchors": ["subject"]}]
    resolved = resolve_span_inspection(
        {
            "items": [
                {
                    "requirement_id": "r1",
                    "status": "complete",
                    "evidence_role": "answer_bearing",
                    "bundle_relation": "complementary",
                    "core_bundles": [["0:0", "1:0"]],
                }
            ]
        },
        spans,
        "subject",
        requirements,
    )
    assert resolved["items"][0]["bundle_relation"] == "complementary"
    checked = validate_inspection(resolved, requirements, children)
    assert checked[0]["bundle_relation"] == "complementary"
    _selected, contract = build_evidence_set(children, checked)
    assert contract["uncovered_requirements"] == []
    with pytest.raises(ValueError, match="Complementary"):
        resolve_span_inspection(
            {
                "items": [
                    {
                        "requirement_id": "r1",
                        "status": "complete",
                        "bundle_relation": "complementary",
                        "core_bundles": [["0:0"], ["1:0"]],
                    }
                ]
            },
            spans,
            "subject",
            requirements,
        )


def test_same_child_different_spans_can_cover_distinct_requirements():
    children = [{"chunk_id": "shared", "text": "Subject. Condition."}]
    selected, contract = build_evidence_set(
        children,
        [
            {
                "requirement_id": "r1",
                "status": "complete",
                "evidence_role": "answer_bearing",
                "core_bundles": [[{"span_id": "0:0", "chunk_id": "shared", "quote": "Subject."}]],
            },
            {
                "requirement_id": "r2",
                "status": "complete",
                "evidence_role": "answer_bearing",
                "core_bundles": [[{"span_id": "0:1", "chunk_id": "shared", "quote": "Condition."}]],
            },
        ],
        limit=1,
    )
    assert [child["chunk_id"] for child in selected] == ["shared"]
    assert contract["uncovered_requirements"] == []


def test_general_clause_marked_partial_cannot_cover_scenario_requirement():
    children = [{"chunk_id": "general", "text": "Organisations should manage AI risks."}]
    requirements = [
        {
            "requirement_id": "r1",
            "anchors": ["sensitive customer data"],
            "condition_anchors": ["sensitive customer data"],
        }
    ]
    inspection = validate_inspection(
        {
            "items": [
                {
                    "requirement_id": "r1",
                    "status": "partial",
                    "evidence_role": "answer_bearing",
                    "core_bundles": [["0:0"]],
                    "evidence": [{"span_id": "0:0"}],
                }
            ]
        },
        requirements,
        children,
    )
    _selected, contract = build_evidence_set(children, inspection)
    assert inspection[0]["status"] == "partial"
    assert contract["uncovered_requirements"] == ["r1"]


def test_v6_planner_restores_program_ids_from_original_question_spans():
    question = "Compare Alpha and Beta on cost"

    def span(text):
        matches = [item for item in question_span_catalog(question) if item["text"] == text]
        assert len(matches) == 1
        return {"start_id": matches[0]["span_id"], "end_id": matches[0]["span_id"]}

    normalized = decompose_requirements(
        {
            "question_type": "comparison",
            "comparison_subject_spans": [span("Alpha"), span("Beta")],
            "requirements": [
                {
                    "anchor_spans": [span("Alpha")],
                    "subject_spans": [span("Alpha")],
                    "dimension_spans": [span("cost")],
                },
                {
                    "anchor_spans": [span("Beta")],
                    "subject_spans": [span("Beta")],
                    "dimension_spans": [span("cost")],
                },
            ],
        },
        question,
    )
    assert [item["requirement_id"] for item in normalized["requirements"]] == ["r1", "r2"]
    assert normalized["comparison_subjects"] == ["Alpha", "Beta"]
    assert normalized["requirements"][0]["anchors"] == ["Alpha", "cost"]
    assert normalized["requirements"][1]["dimension_anchors"] == ["cost"]


def test_v6_planner_rejects_out_of_range_original_question_span():
    with pytest.raises(ValueError, match="anchor"):
        decompose_requirements(
            {
                "requirements": [
                    {"anchor_spans": [{"start_id": "q999", "end_id": "q999"}]},
                ]
            },
            "Short question",
        )


def test_v6_planner_rejects_arbitrary_character_offsets_in_span_contract():
    with pytest.raises(ValueError, match="anchor"):
        decompose_requirements(
            {
                "requirements": [
                    {"anchor_spans": [{"start": 0, "end": 5}]},
                ]
            },
            "Short question",
        )


def test_final_gate_accepts_any_authenticated_or_bundle_that_survives_packing():
    trace = {
        "requirements": [{"requirement_id": "r1", "anchors": ["need"]}],
        "inspections": [
            [
                {
                    "requirement_id": "r1",
                    "status": "complete",
                    "evidence_role": "answer_bearing",
                    "bundle_relation": "alternative",
                    "core_bundles": [
                        [{"chunk_id": "a", "quote": "a"}],
                        [{"chunk_id": "b", "quote": "b"}],
                    ],
                }
            ]
        ],
        "core_contract": {
            "requirements": [
                {
                    "requirement_id": "r1",
                    "bundles": [["a"], ["b"]],
                    "selected_bundle": ["a"],
                }
            ]
        },
    }
    assert uncovered_facets(trace, {"b"}) == []
    assert uncovered_facets(trace, {"a"}) == []
    assert uncovered_facets(trace, set()) == ["r1"]


def test_final_gate_requires_all_members_of_an_authenticated_and_bundle():
    trace = {
        "requirements": [{"requirement_id": "r1", "anchors": ["need"]}],
        "inspections": [
            [
                {
                    "requirement_id": "r1",
                    "status": "complete",
                    "evidence_role": "answer_bearing",
                    "bundle_relation": "alternative",
                    "core_bundles": [
                        [
                            {"chunk_id": "a", "quote": "a"},
                            {"chunk_id": "b", "quote": "b"},
                        ]
                    ],
                }
            ]
        ],
        "core_contract": {"requirements": [{"requirement_id": "r1", "bundles": [["a", "b"]]}]},
    }
    assert uncovered_facets(trace, {"a"}) == ["r1"]
    assert uncovered_facets(trace, {"a", "b"}) == []
