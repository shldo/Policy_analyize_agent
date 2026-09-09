from types import SimpleNamespace

from app.modules.documents.layout import pdf_layout_hints


def test_dominant_body_font_and_small_bottom_footnote():
    class Page:
        rect = SimpleNamespace(height=1000)

        def get_text(self, mode):
            return {
                "blocks": [
                    {
                        "lines": [
                            {
                                "bbox": [0, y, 100, y + 20],
                                "spans": [{"text": text, "size": size, "flags": flags}],
                            }
                        ]
                    }
                    for text, size, flags, y in [
                        ("Normal body text " * 30, 12, 0, 200),
                        ("Risk controls", 18, 16, 100),
                        ("18 Source reference", 8, 0, 900),
                    ]
                ]
            }

    hints = pdf_layout_hints([Page()])[0]
    assert hints["Risk controls"]["block_heading"]
    assert hints["18 Source reference"]["footnote"]
    assert hints["Risk controls"]["body_font_size"] == 12


def test_repeated_edge_caption_is_not_a_section_heading():
    class Page:
        rect = SimpleNamespace(height=1000)

        def get_text(self, mode):
            return {
                "blocks": [
                    {
                        "lines": [
                            {
                                "bbox": [0, 50, 100, 60],
                                "spans": [
                                    {"text": "Running header", "size": 12, "flags": 16},
                                ],
                            }
                        ]
                    }
                ]
            }

    assert all(h["Running header"]["margin"] for h in pdf_layout_hints([Page()] * 3))
