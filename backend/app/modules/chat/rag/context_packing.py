"""Whole-block packing using the configured model tokenizer, never byte counts."""

from collections import Counter
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings, resolve_backend_path


@lru_cache(maxsize=2)
def _tokenizer(path: str):
    from tokenizers import Tokenizer

    if not Path(path).is_file():
        raise FileNotFoundError(path)
    tokenizer = Tokenizer.from_file(path)
    tokenizer.no_truncation()
    tokenizer.no_padding()
    return tokenizer


def generation_tokens(text: str) -> int:
    path = get_settings().rag_tokenizer_path
    return len(
        _tokenizer(str(resolve_backend_path(path))).encode(text, add_special_tokens=False).ids
    )


def available_context_tokens(overhead: str = "", *, count: Callable = generation_tokens) -> int:
    s = get_settings()
    return max(
        0,
        min(
            s.rag_max_context_tokens,
            s.rag_context_window_tokens
            - s.rag_reserved_output_tokens
            - s.rag_prompt_safety_tokens
            - count(overhead),
        ),
    )


def child_citation(child: dict) -> dict:
    return {
        "document_id": child.get("document_id"),
        "chunk_id": child.get("chunk_id"),
        "section_id": child.get("section_id"),
        "section_title": child.get("section_title"),
        "title": child.get("doc_title") or child.get("file", "Document"),
        "page": child.get("page_start") or child.get("page"),
        "page_end": child.get("page_end") or child.get("page_start") or child.get("page"),
        "quote": child.get("text", ""),
    }


def render_parent(parent: dict, numbers: dict) -> str:
    evidence = "\n\n".join(
        f"[{numbers[c.get('chunk_id')]}] Child evidence, pages "
        f"{c.get('page_start')}–{c.get('page_end')}:\n{c['text']}"
        for c in parent["supporting_children"]
    )
    return (
        f"Document: {parent['file']}\nSection: {parent.get('section_title') or ''}\n"
        f"Generation context (not independently retrieved evidence):\n"
        f"{parent['text'] or '(Supporting evidence below; no additional expansion.)'}\n\n"
        f"Cite only the supporting child evidence below:\n{evidence}"
    )


def pack_generation_context(
    parents: list[dict],
    *,
    budget: int,
    count: Callable = generation_tokens,
    citation_numbers: dict | None = None,
) -> dict:
    s = get_settings()
    blocks, packed, citations = [], [], []
    numbers = dict(citation_numbers or {})
    per_document: Counter = Counter()
    seen = set()
    for parent in sorted(parents, key=lambda p: p["parent_score"], reverse=True):
        key = parent.get("context_id") or parent.get("section_id")
        if key in seen or len(packed) >= s.parent_context_k:
            continue
        if per_document[parent["document_id"]] >= s.max_parents_per_document:
            continue
        proposed = dict(numbers)
        for child in parent["supporting_children"]:
            proposed.setdefault(child.get("chunk_id"), max(proposed.values(), default=0) + 1)
        # Reserve exact child evidence across parents before spending tokens on expansion.
        smaller = dict(parent, text="")
        block = render_parent(smaller, proposed)
        if count("\n\n---\n\n".join([*blocks, block])) > budget:
            continue
        numbers = proposed
        blocks.append(block)
        packed.append(parent)
        seen.add(key)
        per_document[parent["document_id"]] += 1
        citations.extend(child_citation(c) for c in parent["supporting_children"])
    expanded = []
    for index, parent in enumerate(packed):
        # Only remove exact duplicate evidence spans. Never fuzzy-dedupe obligations.
        extra = parent["text"]
        for child in parent["supporting_children"]:
            extra = extra.replace(child["text"], "\n[Supporting Child text shown below.]\n")
        candidate = dict(parent, text=extra)
        proposed_blocks = list(blocks)
        proposed_blocks[index] = render_parent(candidate, numbers)
        if count("\n\n---\n\n".join(proposed_blocks)) <= budget:
            blocks = proposed_blocks
            expanded.append(candidate)
        else:
            expanded.append(dict(parent, text=""))
    packed = expanded
    context = "\n\n---\n\n".join(blocks)
    return {
        "context": context,
        "generation_parents": packed,
        "citations": citations,
        "packed_token_count": count(context),
        "truncated": len(packed) < len(parents),
    }
