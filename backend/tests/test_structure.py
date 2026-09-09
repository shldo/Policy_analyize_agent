from app.modules.documents.structure import heading, logical_lines, parse_structure


def test_article_hierarchy():
    root = parse_structure(
        [
            {
                "page": 1,
                "text": (
                    "Article 5 — Risk Management\nIntro\n5.1 Identification\nBody\n"
                    "5.2 Exceptions\nExemptions\nArticle 6 — Monitoring\nMonitor"
                ),
            }
        ]
    )
    assert len(root.children) == 2
    assert [n.number for n in root.children[0].children] == ["5.1", "5.2"]
    assert root.children[0].children[1].path[-1] == "5.2 Exceptions"


def test_layout_and_fallback():
    assert heading("Risk management", {"bold": True}) == (4, None)
    assert (
        heading(
            "Agentic AI is the next evolution of AI",
            {
                "bold": True,
                "block_heading": False,
            },
        )
        is None
    )
    assert heading("This is a sentence.", {"large": True}) is None
    assert heading("Article 5 ................ 10") is None
    root = parse_structure([{"page": 1, "text": "ordinary prose without headings"}])
    assert not root.children
    assert root.pages[0]["text"] == "ordinary prose without headings"


def test_numbered_list_and_footnotes_stay_body():
    for text in (
        "1. Collect the data",
        "2) Review the results",
        "3 Adapted from GovTech",
        "Section 5 requires agencies to report",
        "1.2 Agencies must report annually",
    ):
        assert heading(text) is None
    assert heading("3 Governance", {"footnote": True, "bold": True}) is None
    assert heading("3 Governance", {"font_size": 8, "bold": False}) is None
    root = parse_structure(
        [
            {
                "page": 1,
                "text": (
                    "Article 5 — Data\n1. Collect the data\n"
                    "2. Review the results\n3 Adapted from GovTech"
                ),
            }
        ]
    )
    assert len(root.children) == 1
    assert "3 Adapted from GovTech" in root.children[0].pages[0]["text"]


def test_multiline_heading_joins_without_swallowing_body_or_next_section():
    texts = [
        "Article 5 — Risk",
        "Management and",
        "Accountability",
        "Agencies must assess risk.",
        "Article 6 — Reporting",
    ]
    hints = {
        t: {"bold": True, "font_size": 18, "block_id": 1, "line_index": i}
        for i, t in enumerate(texts)
    }
    hints[texts[3]]["bold"] = False
    page = {"page": 1, "text": "\n".join(texts), "layout_lines": hints}
    assert logical_lines(page)[0][0] == "Article 5 — Risk Management and Accountability"
    root = parse_structure([page])
    assert len(root.children) == 2
    assert "Agencies must assess risk." in root.children[0].pages[0]["text"]


def test_unnumbered_subhead_stays_under_numbered_subsection():
    root = parse_structure(
        [
            {
                "page": 1,
                "text": "2.1.2 Controls\nAgent limits\nBounded actions\n2.1.3 Monitoring\nLogs",
                "layout_lines": {"Agent limits": {"bold": True, "heading_level": 1}},
            }
        ]
    )
    assert root.children[0].children[0].path == ["2.1.2 Controls", "Agent limits"]
    assert root.children[1].number == "2.1.3"


def test_layout_whitespace_difference_does_not_promote_footnote():
    root = parse_structure(
        [
            {
                "page": 1,
                "text": "Article 5 — Risks\n24  Source reference",
                "layout_lines": {"24 Source reference": {"footnote": True}},
            }
        ]
    )
    assert len(root.children) == 1
    assert "24  Source reference" in root.children[0].pages[0]["text"]
