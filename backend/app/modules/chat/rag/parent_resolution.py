"""Resolve only already-approved children; never retrieve or gate parents here."""

from app.core.config import get_settings
from app.core.database import get_connection


def load_sections(section_ids: list[str]) -> dict[str, dict]:
    if not section_ids:
        return {}
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM document_sections WHERE id = ANY(%s::uuid[])", (section_ids,)
        ).fetchall()
    return {str(r["id"]): dict(r) for r in rows}


def resolve_generation_parents(children: list[dict], *, loader=load_sections) -> list[dict]:
    sections = loader(list({c["section_id"] for c in children if c.get("section_id")}))
    groups: dict[str, dict] = {}
    for child in children:
        sid = child.get("section_id")
        section = sections.get(sid)
        if section and str(section["document_id"]) != str(child["document_id"]):
            raise ValueError("Cross-document parent resolution rejected")
        # Legacy NULL section, missing parent, or oversized imported parent: keep
        # exact child text as the safe smaller expansion; never slice policy prose.
        expanded = section and section["token_count"] <= get_settings().parent_target_max_tokens
        key = sid if expanded else f"child:{child.get('chunk_id')}"
        score = child.get("reranker_score")
        score = float(score) if score is not None else -float(child.get("distance", 1))
        if key not in groups:
            groups[key] = {
                "section_id": sid,
                "context_id": key,
                "document_id": child.get("document_id"),
                "section_title": section.get("section_title")
                if expanded
                else child.get("section_title"),
                "text": section["text"] if expanded else child["text"],
                "file": child.get("doc_title") or child.get("file", "Document"),
                "page_start": section["page_start"] if expanded else child.get("page_start"),
                "page_end": section["page_end"] if expanded else child.get("page_end"),
                "parent_score": score,
                "supporting_child_ids": [],
                "supporting_children": [],
            }
        group = groups[key]
        group["parent_score"] = max(group["parent_score"], score)
        if child.get("chunk_id") not in group["supporting_child_ids"]:
            group["supporting_child_ids"].append(child.get("chunk_id"))
            group["supporting_children"].append(child)
    return sorted(groups.values(), key=lambda p: p["parent_score"], reverse=True)
