from app.core.config import Settings
from app.modules.documents.parent_child import build_parent_children, embedding_input


def count(text):
    return len(text.split())


def test_small_sections_not_merged_and_overlap_local():
    sections, children, stats = build_parent_children(
        [
            {
                "page": 1,
                "text": "Article 5 — Risks\n"
                + "risk. " * 700
                + "\nArticle 6 — Exceptions\n"
                + "exempt. " * 200,
            }
        ],
        document_id="doc",
        title="Policy",
        settings=Settings(),
        count=count,
    )
    assert len(sections) == 2
    assert len({c["section_id"] for c in children}) == 2
    assert all(not ("risk." in c["text"] and "exempt." in c["text"]) for c in children)
    assert stats["max_child_tokens"] <= 320
    assert [c["child_index"] for c in children if c["section_id"] == sections[0]["id"]] == [0, 1, 2]
    for c in children:
        assert count(embedding_input(c, None, settings=Settings(), count=count)) < 512


def test_long_article_uses_subsections_and_fallback():
    settings = Settings(parent_target_max_tokens=200)
    sections, children, _ = build_parent_children(
        [
            {
                "page": 1,
                "text": "Article 5 — Risks\n5.1 Identification\n"
                + "one. " * 150
                + "\n5.2 Exceptions\n"
                + "two. " * 150,
            }
        ],
        document_id="doc",
        title="Policy",
        settings=settings,
        count=count,
    )
    assert not sections[0]["metadata_json"]["generation_parent"]
    assert len({c["section_id"] for c in children}) == 2
    _, children, stats = build_parent_children(
        [{"page": 1, "text": "ordinary. " * 500}],
        document_id="plain",
        title="Plain",
        settings=settings,
        count=count,
    )
    assert children and not stats["structure_detected"]


def test_long_unstructured_parent_preserves_child_page_provenance():
    _, children, _ = build_parent_children(
        [
            {"page": 1, "text": "firstpage. " * 100},
            {"page": 2, "text": "secondpage. " * 100},
            {"page": 3, "text": "thirdpage. " * 100},
        ],
        document_id="pages",
        title="Policy",
        count=count,
        settings=Settings(
            parent_target_max_tokens=250, child_target_tokens=64, child_overlap_tokens=0
        ),
    )
    for child in children:
        if "secondpage." in child["text"]:
            assert child["page_start"] <= 2 <= child["page_end"]
        if "firstpage." not in child["text"] and "secondpage." in child["text"]:
            assert child["page_start"] == 2


def test_specific_evidence_path_kept_under_larger_generation_parent():
    from app.modules.documents.parent_child import evidence_section
    from app.modules.documents.structure import parse_structure

    tree = parse_structure(
        [
            {
                "page": 1,
                "text": (
                    "Article 5 — Risk\n5.1 Controls\nBounded actions\n5.2 Exceptions\nExempt cases"
                ),
            }
        ]
    )
    article = tree.children[0]
    assert evidence_section(article, "Exempt cases").path[-1] == "5.2 Exceptions"
    assert (
        evidence_section(article, "5.1 Controls\nBounded actions\n5.2 Exceptions").title
        == article.title
    )
