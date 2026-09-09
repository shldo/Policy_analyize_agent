"""Pack document parents once across tool calls; keep live web results unchanged."""

import json

from langchain_core.messages import SystemMessage, ToolMessage

from app.modules.chat.rag.context_packing import available_context_tokens, pack_generation_context


def pack_agent_messages(messages: list, system_prompt: str) -> list:
    parents, numbers, compact = {}, {}, []
    for message in messages:
        if not isinstance(message, ToolMessage):
            compact.append(message)
            continue
        try:
            payload = json.loads(message.content)
        except (ValueError, TypeError):
            compact.append(message)
            continue
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
    overhead = system_prompt + "\n".join(
        str(m.content) + json.dumps(getattr(m, "tool_calls", []), ensure_ascii=False)
        for m in compact
    )
    packed = pack_generation_context(
        list(parents.values()), budget=available_context_tokens(overhead), citation_numbers=numbers
    )
    context = packed["context"]
    if parents and not context:
        context = "Document evidence could not fit the token budget. Do not assert document facts."
    return [SystemMessage(content=system_prompt + "\n\n" + context), *compact]
