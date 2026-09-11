"""Pack document parents once across tool calls; keep live web results unchanged."""

import json
import logging

from langchain_core.messages import SystemMessage, ToolMessage

from app.core.config import get_settings
from app.modules.chat.rag.context_packing import available_context_tokens, pack_generation_context
from app.modules.documents.controlled_retrieval import uncovered_facets

logger = logging.getLogger(__name__)


class IncompleteControlledEvidence(ValueError):
    """Document coverage was not established for the actual final context."""


def pack_agent_messages(
    messages: list,
    system_prompt: str,
    *,
    question: str = "",
    metadata: dict | None = None,
) -> list:
    if get_settings().rag_allow_partial_answers:
        from app.modules.chat.rag.prompts import PARTIAL_ANSWER_INSTRUCTION

        system_prompt += "\n" + PARTIAL_ANSWER_INSTRUCTION
    parents, numbers, compact = {}, {}, []
    traces = []
    document_search = False
    for message in messages:
        if not isinstance(message, ToolMessage):
            compact.append(message)
            continue
        try:
            payload = json.loads(message.content)
        except (ValueError, TypeError):
            compact.append(message)
            continue
        if isinstance(payload, dict):
            document_search |= message.name in ("search_internal_documents", "search_full_corpus")
            if payload.get("controlled_trace") is not None:
                traces.append(payload.pop("controlled_trace"))
        if not isinstance(payload, dict) or "generation_parents" not in payload:
            compact.append(message)
            continue
        for result in payload.get("results", []):
            if result.get("chunk_id") and result.get("number"):
                numbers[result["chunk_id"]] = result["number"]
        for parent in payload.pop("generation_parents"):
            key = parent["context_id"]
            if key not in parents:
                parents[key] = dict(
                    parent,
                    supporting_children=list(parent["supporting_children"]),
                    supporting_child_ids=list(parent["supporting_child_ids"]),
                )
            else:
                old = parents[key]
                old["parent_score"] = max(old["parent_score"], parent["parent_score"])
                for child in parent["supporting_children"]:
                    if child["chunk_id"] not in old["supporting_child_ids"]:
                        old["supporting_child_ids"].append(child["chunk_id"])
                        old["supporting_children"].append(child)
        payload["results"] = []
        payload["context_location"] = "Use only packed child evidence in the final system context."
        compact.append(message.model_copy(update={"content": json.dumps(payload)}))
    coverage_notice = (
        "Final document coverage is partial or unverified; do not claim complete support."
    )
    loss_notice = (
        "Final packing omitted some document evidence. Earlier tool coverage claims "
        "do not certify this final context. Cite only retained Child evidence and "
        "explicitly acknowledge unsupported parts."
    )
    overhead = (
        system_prompt
        + coverage_notice
        + loss_notice
        + "\n".join(
            str(m.content) + json.dumps(getattr(m, "tool_calls", []), ensure_ascii=False)
            for m in compact
        )
    )
    controlled = bool(traces) or (document_search and get_settings().controlled_retrieval_enabled)
    scoped = [t for t in traces if t.get("question") == question]
    final_trace = scoped[-1] if scoped else {}
    ordered = list(parents.values())
    if controlled:
        required_ids = {
            child_id
            for child_id in final_trace.get("core_contract", {}).get("selected_core_child_ids", [])
        }
        if not required_ids:
            required_ids = {
                e["chunk_id"]
                for i in (final_trace.get("inspections") or [[]])[-1]
                for e in i.get("evidence", [])
            }
        ordered.sort(key=lambda p: -len(required_ids.intersection(p["supporting_child_ids"])))
    packed = pack_generation_context(
        ordered,
        budget=available_context_tokens(overhead),
        citation_numbers=numbers,
        packing_policy=get_settings().rag_packing_policy,
        **({"preserve_order": True} if controlled else {}),
    )
    input_ids = {c["chunk_id"] for p in ordered for c in p["supporting_children"]}
    final_ids = {c["chunk_id"] for c in packed["citations"]}
    lost_ids = input_ids - final_ids
    logger.info(
        "agent_final_pack policy=%s input_children=%d packed_children=%d lost_children=%d",
        get_settings().rag_packing_policy,
        len(input_ids),
        len(final_ids),
        len(lost_ids),
    )
    if lost_ids:
        system_prompt += "\n" + loss_notice
    if controlled:
        packed_ids = {c["chunk_id"] for c in packed["citations"]}
        # A successful subquery is not proof of coverage for the original user question.
        incomplete = (
            final_trace.get("coverage_sufficient") is not True
            or final_trace.get("coverage_stage") != "packed"
            or uncovered_facets(final_trace, packed_ids)
        )
        if incomplete and not get_settings().rag_allow_partial_answers:
            raise IncompleteControlledEvidence(
                "The final packed evidence does not establish complete coverage "
                "of the user question."
            )
    context = packed["context"]
    has_packed_context = bool(context.strip())
    if get_settings().rag_allow_partial_answers and controlled and incomplete:
        system_prompt += "\n" + coverage_notice
    if parents and not context:
        context = "Document evidence could not fit the token budget. Do not assert document facts."
    coverage_status = "not_assessed" if has_packed_context else "no_context"
    coverage_sufficient = False
    if controlled:
        coverage_status = (
            "complete" if not incomplete else ("partial" if has_packed_context else "no_context")
        )
        coverage_sufficient = coverage_status == "complete"
    if metadata is not None:
        metadata.update(
            {
                "generation_allowed": has_packed_context,
                "coverage_status": coverage_status,
                "coverage_sufficient": coverage_sufficient,
                "final_packed_child_ids": sorted(final_ids),
                "lost_child_ids": sorted(lost_ids),
            }
        )
    return [SystemMessage(content=system_prompt + "\n\n" + context), *compact]
