"""Whole-block packing using the configured model tokenizer, never byte counts."""

from collections import Counter
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings, resolve_backend_path

ORIGINAL_PACKING_POLICY = "original"
PER_DOCUMENT_BACKFILL_PACKING_POLICY = "per_document_backfill_v1"
PACKING_POLICIES = (ORIGINAL_PACKING_POLICY, PER_DOCUMENT_BACKFILL_PACKING_POLICY)


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
    preserve_order: bool = False,
    packing_policy: str = ORIGINAL_PACKING_POLICY,
) -> dict:
    if packing_policy not in PACKING_POLICIES:
        raise ValueError(f"Unknown packing policy: {packing_policy}")
    s = get_settings()
    blocks, packed, citations = [], [], []
    numbers = dict(citation_numbers or {})
    per_document: Counter = Counter()
    seen = set()
    packing_trace = []
    deferred = []
    ordered_parents = (
        parents
        if preserve_order
        else sorted(parents, key=lambda p: p["parent_score"], reverse=True)
    )

    def record(parent: dict, reason: str, *, selected: bool) -> None:
        packing_trace.append(
            {
                "context_id": parent.get("context_id") or parent.get("section_id"),
                "document_id": parent.get("document_id"),
                "supporting_child_ids": [
                    child.get("chunk_id") for child in parent.get("supporting_children", [])
                ],
                "selected": selected,
                "reason": reason,
            }
        )

    def try_select(parent: dict, reason: str) -> bool:
        nonlocal blocks, numbers
        proposed = dict(numbers)
        for child in parent["supporting_children"]:
            proposed.setdefault(child.get("chunk_id"), max(proposed.values(), default=0) + 1)
        # Reserve exact child evidence across parents before spending tokens on expansion.
        smaller = dict(parent, text="")
        block = render_parent(smaller, proposed)
        if count("\n\n---\n\n".join([*blocks, block])) > budget:
            record(parent, "token_budget", selected=False)
            return False
        numbers = proposed
        blocks.append(block)
        packed.append(parent)
        key = parent.get("context_id") or parent.get("section_id")
        seen.add(key)
        per_document[parent["document_id"]] += 1
        citations.extend(child_citation(c) for c in parent["supporting_children"])
        record(parent, reason, selected=True)
        return True

    for parent in ordered_parents:
        key = parent.get("context_id") or parent.get("section_id")
        if key in seen:
            record(parent, "duplicate_parent", selected=False)
            continue
        if len(packed) >= s.parent_context_k:
            record(parent, "global_parent_limit", selected=False)
            continue
        if per_document[parent["document_id"]] >= s.max_parents_per_document:
            record(parent, "per_document_deferred", selected=False)
            if packing_policy == PER_DOCUMENT_BACKFILL_PACKING_POLICY:
                deferred.append(parent)
            continue
        try_select(parent, "selected_initial")

    if packing_policy == PER_DOCUMENT_BACKFILL_PACKING_POLICY:
        for parent in deferred:
            key = parent.get("context_id") or parent.get("section_id")
            if key in seen:
                record(parent, "duplicate_parent", selected=False)
                continue
            if len(packed) >= s.parent_context_k:
                record(parent, "global_parent_limit", selected=False)
                continue
            # The per-document limit is a soft first-pass quota for this policy.
            try_select(parent, "selected_backfill")

    expanded = []
    expansion_trace = []
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
            expansion_text = extra.replace("\n[Supporting Child text shown below.]\n", "").strip()
            expansion_trace.append(
                {
                    "context_id": parent.get("context_id") or parent.get("section_id"),
                    "expanded": bool(expansion_text),
                    "reason": "expanded_parent" if expansion_text else "child_only_parent",
                }
            )
        else:
            expanded.append(dict(parent, text=""))
            expansion_trace.append(
                {
                    "context_id": parent.get("context_id") or parent.get("section_id"),
                    "expanded": False,
                    "reason": "child_only_parent",
                }
            )
    packed = expanded
    context = "\n\n---\n\n".join(blocks)
    return {
        "context": context,
        "generation_parents": packed,
        "citations": citations,
        "packed_token_count": count(context),
        "truncated": len(packed) < len(parents),
        "packing_policy": packing_policy,
        "packing_trace": packing_trace,
        "parent_expansion_trace": expansion_trace,
        "expanded_parent_count": sum(item["expanded"] for item in expansion_trace),
        "child_only_parent_count": sum(not item["expanded"] for item in expansion_trace),
    }
