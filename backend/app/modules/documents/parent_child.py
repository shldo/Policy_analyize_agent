"""Structure-selected generation parents and independently split retrieval children."""

import logging
from collections.abc import Callable
from uuid import NAMESPACE_URL, uuid5

from app.core.config import Settings
from app.modules.documents.chunker import DocumentChunker
from app.modules.documents.structure import Section, parse_structure

logger = logging.getLogger(__name__)


def evidence_section(node: Section, text: str) -> Section:
    """Keep the most specific section path when a larger ancestor supplies context."""
    normalized = " ".join(text.split())
    for child in node.children:
        child_text = " ".join(" ".join(p["text"] for p in child.all_pages()).split())
        if normalized in child_text:
            return evidence_section(child, text)
    return node


def structure_prefix(title: str, path: list[str], count: Callable, budget: int) -> str:
    parts = []
    for part in [title, *path]:
        if count("\n".join([*parts, part])) <= budget:
            parts.append(part)
        else:
            logger.warning("structure_prefix_component_omitted tokens=%d", count(part))
    return "\n".join(parts)


def build_parent_children(
    pages: list[dict],
    *,
    document_id: str,
    title: str,
    settings: Settings,
    count: Callable[[str], int],
) -> tuple[list[dict], list[dict], dict]:
    root = parse_structure(pages)
    splitter = DocumentChunker(count)
    sections: list[dict] = []
    children: list[dict] = []
    s = settings

    def create(node: Section, parent_id: str | None, content: list[dict], generation: bool) -> dict:
        text = "\n\n".join(p["text"] for p in content)
        sequence = len(sections)
        section_id = str(uuid5(NAMESPACE_URL, f"{document_id}:structure-v2:{sequence}:{text}"))
        row = {
            "id": section_id,
            "parent_section_id": parent_id,
            "section_level": node.level,
            "section_number": node.number,
            "section_title": node.title,
            "section_path": node.path,
            "text": text,
            "page_start": min((p["page"] for p in content), default=1),
            "page_end": max((p["page"] for p in content), default=1),
            "token_count": count(text),
            "sequence_index": sequence,
            "metadata_json": {"generation_parent": generation, "structure_version": 2},
        }
        sections.append(row)
        if generation and text.strip():
            prefix = structure_prefix(title, node.path, count, s.structure_prefix_max_tokens)
            reserve = s.contextual_header_reserve_tokens if s.use_llm_contextual_header else 0
            effective = min(
                s.child_max_tokens,
                s.child_target_tokens,
                s.embedding_max_input_tokens
                - max(count(prefix), s.structure_prefix_max_tokens)
                - reserve
                - s.embedding_special_tokens
                - s.embedding_safety_margin,
            )
            if effective < 64:
                raise ValueError("Embedding input budget leaves fewer than 64 child tokens.")
            # A new splitter invocation for EVERY parent is the overlap boundary.
            pieces = splitter.chunk(
                content, max_tokens=effective, overlap=min(s.child_overlap_tokens, effective // 2)
            )
            for i, chunk in enumerate(pieces):
                if count(chunk["text"]) > effective:
                    raise ValueError("Child split exceeded its effective token budget.")
                specific = evidence_section(node, chunk["text"])
                child_prefix = structure_prefix(
                    title, specific.path, count, s.structure_prefix_max_tokens
                )
                chunk.update(
                    section_id=section_id,
                    child_index=i,
                    chunk_index=len(children),
                    section_title=specific.title,
                )
                chunk["metadata_json"] = {
                    "structure_prefix": child_prefix,
                    "section_path": specific.path,
                    "structure_version": 2,
                    "effective_child_budget": effective,
                }
                children.append(chunk)
        return row

    def visit(node: Section, parent_id: str | None, covered: bool = False) -> None:
        content = node.all_pages()
        size = count("\n\n".join(p["text"] for p in content))
        fits = size <= s.parent_target_max_tokens
        row = create(node, parent_id, content, not covered and fits)
        if covered or fits:
            for child in node.children:
                visit(child, row["id"], covered=True)
            return
        # Long nodes yield complete lower-level sections. Intro/long leaf prose is
        # partitioned locally; never combine adjacent unrelated sections.
        own_pages = node.pages
        if "\n".join(p["text"] for p in own_pages).strip() == node.title:
            own_pages = []
        for i, piece in enumerate(
            splitter.chunk(
                own_pages,
                max_tokens=s.parent_target_max_tokens,
                overlap=0,
                include_source_items=True,
            )
        ):
            part = Section(
                f"{node.title} — passage {i + 1}",
                node.level + 1,
                path=node.path + [f"Passage {i + 1}"],
            )
            create(part, row["id"], piece["source_items"], True)
        for child in node.children:
            visit(child, row["id"])

    # The artificial root never merges independent top-level sections.
    if root.pages:
        visit(
            Section("Document introduction", 1, pages=root.pages, path=["Document introduction"]),
            None,
        )
    for node in root.children:
        visit(node, None)
    parents = [r for r in sections if r["metadata_json"]["generation_parent"]]
    stats = {
        "section_count": len(sections),
        "generation_parent_count": len(parents),
        "children_count": len(children),
        "structure_detected": bool(root.children),
        "avg_parent_tokens": sum(r["token_count"] for r in parents) / max(1, len(parents)),
        "max_parent_tokens": max((r["token_count"] for r in parents), default=0),
        "avg_child_tokens": sum(c["token_count"] for c in children) / max(1, len(children)),
        "max_child_tokens": max((c["token_count"] for c in children), default=0),
        "children_per_parent": {
            r["id"]: sum(c["section_id"] == r["id"] for c in children) for r in parents
        },
    }
    return sections, children, stats


def embedding_input(chunk: dict, header: str | None, *, settings: Settings, count: Callable) -> str:
    prefix = (chunk.get("metadata_json") or {}).get("structure_prefix", "")
    text = "\n\n".join(p for p in [prefix, header, chunk["text"]] if p)
    limit = (
        settings.embedding_max_input_tokens
        - settings.embedding_special_tokens
        - settings.embedding_safety_margin
    )
    if count(text) > limit:
        logger.warning("embedding_input_rejected tokens=%d limit=%d", count(text), limit)
        raise ValueError(
            "Embedding input exceeds model budget; full reprocess with smaller children."
        )
    return text
