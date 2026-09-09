"""Read-only PDF typography hints. Never substitute or discard extracted text."""

from collections import Counter


def pdf_layout_hints(document) -> list[dict]:
    blocks_by_page = [page.get_text("dict")["blocks"] for page in document]
    sizes: Counter = Counter()
    for blocks in blocks_by_page:
        for block in blocks:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    sizes[round(span["size"], 1)] += len(span["text"].strip())
    body = sizes.most_common(1)[0][0] if sizes else 12
    large_sizes = sorted((size for size in sizes if size >= body * 1.12), reverse=True)
    edge_occurrences: Counter = Counter()
    for page, blocks in zip(document, blocks_by_page, strict=True):
        edge_values = set()
        for block in blocks:
            for line in block.get("lines", []):
                y = line["bbox"][1] / page.rect.height
                value = " ".join("".join(s["text"] for s in line["spans"]).split())
                if value and (y < 0.08 or y > 0.92):
                    edge_values.add(value)
        edge_occurrences.update(edge_values)
    results = []
    for page, blocks in zip(document, blocks_by_page, strict=True):
        hints = {}
        for block_index, block in enumerate(blocks):
            lines = block.get("lines", [])
            block_spans = [s for line in lines for s in line["spans"] if s["text"].strip()]
            block_text = " ".join(s["text"] for s in block_spans)
            all_bold = bool(block_spans) and all(s.get("flags", 0) & 16 for s in block_spans)
            for line_index, line in enumerate(lines):
                spans = [s for s in line["spans"] if s["text"].strip()]
                value = "".join(s["text"] for s in line["spans"]).strip()
                weight = sum(len(s["text"].strip()) for s in spans) or 1
                bold_ratio = (
                    sum(len(s["text"].strip()) for s in spans if s.get("flags", 0) & 16) / weight
                )
                size = sum(s["size"] * len(s["text"].strip()) for s in spans) / weight
                strong = bold_ratio >= 0.85 or size >= body * 1.12
                hints[value] = {
                    "block_id": block_index,
                    "line_index": line_index,
                    "font_size": size,
                    "body_font_size": body,
                    "bold": bold_ratio >= 0.85,
                    "large": size >= body * 1.12,
                    "block_heading": (
                        strong
                        and len(value.split()) <= 20
                        and not (all_bold and len(block_text.split()) > 22)
                    ),
                    "heading_level": min(6, 1 + sum(s > size + 0.2 for s in large_sizes)),
                    "margin": (
                        line["bbox"][1] < page.rect.height * 0.035
                        or (
                            edge_occurrences[" ".join(value.split())] >= 3
                            and (
                                line["bbox"][1] < page.rect.height * 0.08
                                or line["bbox"][1] > page.rect.height * 0.92
                            )
                        )
                    ),
                    "footnote": size < body * 0.87 and line["bbox"][1] > page.rect.height * 0.65,
                }
        results.append(hints)
    return results
