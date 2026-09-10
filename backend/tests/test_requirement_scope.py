"""Lossless question scope is context, never evidence or a completeness certificate."""

from app.modules.documents.controlled_retrieval import decompose_requirements


def test_shared_enumeration_scope_is_retained_on_each_requirement():
    question = "Which controls for overseas contractors: review and logging?"
    plan = decompose_requirements(
        {
            "question_type": "enumeration",
            "requirements": [
                {"anchors": ["review"]},
                {"anchors": ["logging?"]},
            ],
        },
        question,
    )
    for requirement in plan["requirements"]:
        assert requirement["question_scope"] == question
        assert "coverage_sufficient" not in requirement


def test_comparison_focus_uses_bound_subject_and_dimension_not_opener():
    question = "Compare Alpha and Beta on cost and speed."
    plan = decompose_requirements(
        {
            "question_type": "comparison",
            "comparison_subjects": ["Alpha", "Beta"],
            "requirements": [
                {"anchors": ["Compare"], "subject_anchors": [s], "dimension_anchors": [d]}
                for s in ("Alpha", "Beta")
                for d in ("cost", "speed.")
            ],
        },
        question,
    )
    assert [r["anchors"] for r in plan["requirements"]] == [
        ["Alpha", "cost"],
        ["Alpha", "speed."],
        ["Beta", "cost"],
        ["Beta", "speed."],
    ]
    assert all(r["question_scope"] == question for r in plan["requirements"])


def test_fragmented_scenario_roles_do_not_erase_original_condition():
    question = "For a vendor handling sensitive customer data, what safeguards apply?"
    plan = decompose_requirements(
        {
            "question_type": "simple",
            "requirements": [
                {
                    "anchors": ["safeguards"],
                    "object_anchors": ["vendor"],
                    "condition_anchors": ["sensitive", "customer"],
                }
            ],
        },
        question,
    )
    assert "sensitive customer data" in plan["requirements"][0]["question_scope"]


def test_scope_cannot_be_overridden_by_model():
    question = "Which controls apply only to external suppliers?"
    plan = decompose_requirements(
        {
            "requirements": [
                {"anchors": ["controls"], "question_scope": "All suppliers, without exceptions"}
            ]
        },
        question,
    )
    assert plan["requirements"][0]["question_scope"] == question
