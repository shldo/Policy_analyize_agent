from app.modules.chat.rag.agent.tools import _document_citation


def test_document_citation_preserves_chunk_page_range():
    citation = _document_citation(
        {
            "document_id": "doc",
            "doc_title": "Policy",
            "chunk_id": "chunk",
            "page_start": 4,
            "page_end": 6,
            "text": "evidence",
        }
    )
    assert citation["page"] == 4
    assert citation["page_end"] == 6


def test_single_page_citation_uses_same_end_page():
    citation = _document_citation({"page": 7, "text": "evidence"})
    assert citation["page"] == 7
    assert citation["page_end"] == 7
