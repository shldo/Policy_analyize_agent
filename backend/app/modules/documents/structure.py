"""Deterministic section tree. Layout is supporting evidence, never replacement text."""

import re
from dataclasses import dataclass, field

_PROSE = re.compile(
    r"\b(must|shall|should|may|can|will|are|is|was|were|has|have|requires|"
    r"adapted from|available at|accessed|retrieved from|https?://)\b",
    re.I,
)
_NUMBER = re.compile(r"^(\d+(?:\.\d+)*)([.)]?)\s+(.+)$")


def _typographic(info: dict) -> bool:
    return bool(
        (info.get("bold") or info.get("large"))
        and info.get("block_heading", True)
        and not info.get("footnote")
        and not info.get("margin")
    )


@dataclass
class Section:
    title: str
    level: int
    number: str | None = None
    pages: list[dict] = field(default_factory=list)
    children: list["Section"] = field(default_factory=list)
    path: list[str] = field(default_factory=list)

    def all_pages(self) -> list[dict]:
        return self.pages + [p for child in self.children for p in child.all_pages()]


def heading(line: str, layout: dict | None = None) -> tuple[int, str | None] | None:
    text = line.strip()
    info = layout or {}
    if not text or len(text) > 150 or len(text.split()) > 22:
        return None
    # Contents entries and complete prose sentences are not section boundaries.
    if re.search(r"\.{3,}\s*\d+$", text) or text.endswith((".", ";", ",")):
        return None
    if info.get("footnote") or info.get("margin"):
        return None
    markdown = re.match(r"^(#{1,6})\s+\S", text)
    if markdown:
        return len(markdown[1]), None
    named = re.match(
        r"^(Part|Chapter|Article|Section|Subsection|Annex|Appendix)\s+([\dIVXLC]+|[A-Z])\b",
        text,
        re.I,
    )
    if named:
        if _PROSE.search(text[named.end() :]):
            return None
        levels = {
            "part": 1,
            "chapter": 2,
            "article": 3,
            "section": 3,
            "subsection": 4,
            "annex": 1,
            "appendix": 1,
        }
        return levels[named[1].lower()], named[2]
    numeric = _NUMBER.match(text)
    if numeric:
        if _PROSE.search(numeric[3]) or len(text.split()) > 16:
            return None
        # 1. / 1) are list markers unless typography independently supports a heading.
        if numeric[2] and not _typographic(info):
            return None
        if info and "font_size" in info and not _typographic(info):
            return None
        return 3 + numeric[1].count("."), numeric[1]
    # Unnumbered headings require multiple signals; ALL CAPS alone is insufficient.
    typography = _typographic(info)
    if typography and len(text.split()) <= 12 and not _PROSE.search(text):
        return max(4, info.get("heading_level", 4)), None
    if text.isupper() and len(text.split()) <= 8 and info.get("isolated", False):
        return 4, None
    return None


def logical_lines(page: dict) -> list[tuple[str, dict]]:
    """Join consecutive same-style title lines within one PDF block, not body prose."""
    lines = page.get("text", "").splitlines()
    layout = {" ".join(k.split()): v for k, v in page.get("layout_lines", {}).items()}
    result = []
    for i, line in enumerate(lines):
        info = dict(layout.get(" ".join(line.split()), {}))
        info["isolated"] = (i == 0 or not lines[i - 1].strip()) and (
            i + 1 == len(lines) or not lines[i + 1].strip()
        )
        if result and line.strip() and _typographic(info):
            previous, prior = result[-1]
            same_block = "block_id" in info and info["block_id"] == prior.get("block_id")
            consecutive = info.get("line_index", -2) == prior.get("last_line_index", -4) + 1
            same_font = abs(info.get("font_size", 0) - prior.get("font_size", 0)) < 0.5
            new_number = _NUMBER.match(line.strip()) or re.match(
                r"^(Article|Section|Chapter|Part|Annex|Appendix)\b", line.strip(), re.I
            )
            combined = previous + " " + line.strip()
            if (
                same_block
                and consecutive
                and same_font
                and _typographic(prior)
                and not new_number
                and len(combined.split()) <= 22
                and not _PROSE.search(combined)
            ):
                prior["last_line_index"] = info["line_index"]
                result[-1] = (combined, prior)
                continue
        info["last_line_index"] = info.get("line_index", -2)
        result.append((line.strip(), info))
    return result


def parse_structure(pages: list[dict]) -> Section:
    root = Section("Document", 0)
    stack = [root]
    for page in pages:
        buffer: list[str] = []

        def flush(buffer=buffer, page=page) -> None:
            if any(s.strip() for s in buffer):
                stack[-1].pages.append({**page, "text": "\n".join(buffer).strip()})
            buffer.clear()

        for line, info in logical_lines(page):
            detected = heading(line, info)
            if detected:
                flush()
                level, number = detected
                if number is None and not line.startswith("#"):
                    numbered_ancestor = next((n for n in reversed(stack) if n.number), None)
                    if numbered_ancestor is not None:
                        level = max(level, numbered_ancestor.level + 1)
                while len(stack) > 1 and stack[-1].level >= level:
                    stack.pop()
                node = Section(line.strip(), level, number, path=stack[-1].path + [line.strip()])
                stack[-1].children.append(node)
                stack.append(node)
            buffer.append(line)
        flush()
    return root
