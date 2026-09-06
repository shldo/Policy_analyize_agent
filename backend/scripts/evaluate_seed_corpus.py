"""Small development-only retrieval comparison; no LLM generation or web search."""
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

# Labels are manually reviewed evidence spans. This small development set is
# versioned because overlapping chunks can contain the same answer.
LABEL_VERSION = "v3"
CASES = [
    ("AU01", "How often must agencies review their AI transparency statements?", [
        ("20b225ff-f607-4607-9f95-593e2d430d12", "reviewed and updated annually", "Australia_Responsible_AI_Government_v2.pdf", 10),
        ("ddb8cae3-4b72-475e-9cce-af7ca45b2efc", "at least once a year", "Australia_AI_Transparency_Standard_v2.pdf", 4),
        ("2853d499-4844-4f19-bb7b-c7e52ce8f4d4", "at least once a year", "Australia_AI_Transparency_Standard_v2.pdf", 4),
    ]),
    ("AU02", "Who must agencies notify when publishing or changing an AI transparency statement, and how?", [
        ("20b225ff-f607-4607-9f95-593e2d430d12", "notify the DTA", "Australia_Responsible_AI_Government_v2.pdf", 10),
        ("2853d499-4844-4f19-bb7b-c7e52ce8f4d4", "send the DTA a link", "Australia_AI_Transparency_Standard_v2.pdf", 5),
    ]),
    ("AU03", "Within what period must agencies develop a strategic position on AI adoption?", [
        ("20b225ff-f607-4607-9f95-593e2d430d12", "within 6 months", "Australia_Responsible_AI_Government_v2.pdf", 10),
        ("443fef01-b409-4109-8df8-6a5509a742cc", "within 6 months", "Australia_Responsible_AI_Government_v2.pdf", 10),
    ]),
    ("AU04", "How frequently must agencies share their AI use case register with the DTA?", [
        ("443fef01-b409-4109-8df8-6a5509a742cc", "every 6 months", "Australia_Responsible_AI_Government_v2.pdf", 11),
        ("2658730a-006d-46ee-946c-fdc0a5ac6fc2", "every 6 months", "Australia_Responsible_AI_Government_v2.pdf", 11),
    ]),
    ("AU05", "When must mandatory responsible AI training be implemented, and which staff does it cover?", [
        ("072b16bc-e451-4627-944e-82eefc48dd28", "mandatory training for all staff", "Australia_Responsible_AI_Government_v2.pdf", 13),
    ]),
    ("TR01", "According to the staff training guidance, how long does the AI fundamentals module take?", [
        ("f8542e0f-f7bf-41dd-aaab-7edb19c7094b", "20 to 30 minutes", "Australia_AI_Staff_Training_v2.pdf", 5),
    ]),
    ("TS01", "Does the transparency standard require agencies to list individual AI use cases publicly?", [
        ("2853d499-4844-4f19-bb7b-c7e52ce8f4d4", "not required to list individual use cases", "Australia_AI_Transparency_Standard_v2.pdf", 5),
    ]),
    ("TS02", "What two classification dimensions must agencies list in their AI transparency statements?", [
        ("9ef7ed5c-7e13-4ff2-93a0-38f235505302", "both the usage patterns and domains", "Australia_AI_Transparency_Standard_v2.pdf", 7),
    ]),
    ("TECH01", "When does Criterion 22 require watermarking, and what must it provide?", [
        ("eded4eb6-f9d0-4c97-b806-9b5949379ddf", "may directly impact a user", "Australia_AI_Technical_Standard_2025.pdf", 43),
        ("70b0c220-6dc5-477c-a4bd-fa639d369eff", "may directly impact a user", "Australia_AI_Technical_Standard_2025.pdf", 43),
    ]),
    ("TECH02", "Which version management practice is required under Statement 7?", [
        ("4c7f00d8-6cee-4e41-9fbf-a8e603d353b5", "end-to-end development lifecycle", "Australia_AI_Technical_Standard_2025.pdf", 15),
        ("959ef8c3-624e-4cbc-be65-9b5d39fdd7d9", "end-to-end development lifecycle", "Australia_AI_Technical_Standard_2025.pdf", 15),
        ("48029500-fe00-4122-ac94-945b38e98d3f", "end-to-end development lifecycle", "Australia_AI_Technical_Standard_2025.pdf", 41),
        ("9cf1194d-95a2-46c8-bb3d-5bfcfdc3f0f9", "end-to-end development lifecycle", "Australia_AI_Technical_Standard_2025.pdf", 41),
    ]),
    ("SG01", "Which protocols does the framework name for agent-to-tool and agent-to-agent communication?", [
        ("ffa72801-931f-48f6-882f-b19cfc704dc7", "Model Context Protocol (MCP)", "Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf", 7),
        ("dd2e70ca-b2c5-419c-a0b6-b7005eb17dc8", "Model Context Protocol (MCP)", "Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf", 7),
    ]),
    ("SG02", "Why should organisations prefer deterministic limits over prompt-only limits for agents?", [
        ("dda82648-b86e-455d-bc5d-19735e045471", "prefer deterministic rather than non-deterministic limits", "Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf", 19),
        ("f2ceef44-ff2c-411a-b473-4e0c016a04c2", "prefer deterministic rather than non-deterministic limits", "Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf", 19),
    ]),
    ("SG03", "What three design patterns does the framework list for multi-agent systems?", [
        ("dd2e70ca-b2c5-419c-a0b6-b7005eb17dc8", "Three simple design patterns for multi-agent systems", "Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf", 8),
        ("a310c127-811b-4acc-ae1c-5e61477046e1", "Three simple design patterns for multi-agent systems", "Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf", 8),
    ]),
]


def score(ids: list[str], gold: set[str]) -> dict:
    if not gold:
        raise ValueError("Gold evidence cannot be empty")
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate retrieved IDs")
    rank = next((i for i, key in enumerate(ids, 1) if key in gold), None)
    return {
        "hit_at_5": int(rank is not None and rank <= 5),
        "hit_at_20": int(rank is not None and rank <= 20),
        "rr_at_10": 1 / rank if rank is not None and rank <= 10 else 0,
        "first_label_rank": rank,
    }


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def main() -> None:
    from app.core.database import get_connection
    from app.modules.documents.repositories.embeddings import embedding_repository
    from app.modules.documents.reranker import RERANKER_MODEL_NAME, rerank_chunks
    from app.modules.embedding import service as embedding

    def snapshot():
        # Freeze the actual public retrieval pool, including contextual headers and vectors.
        from psycopg import sql
        with get_connection() as conn:
            rows = conn.execute(sql.SQL("""
                SELECT c.id,c.text,c.page_start,c.page_end,c.metadata_json,
                       d.sha256,d.original_filename,e.embedding::text AS vector
                FROM document_chunks c JOIN documents d ON d.id=c.document_id
                JOIN {} e ON e.chunk_id=c.id
                WHERE d.approved=true AND d.access_level='public' ORDER BY c.id
            """).format(sql.Identifier(embedding.active_vector_table()))).fetchall()
        return [dict(row) for row in rows]

    pool = snapshot()
    lookup = {str(row["id"]): row for row in pool}
    for case_id, _, evidence in CASES:
        for chunk_id, quote, filename, physical_page in evidence:
            row = lookup.get(chunk_id)
            if (
                row is None
                or quote not in row["text"]
                or filename != row["original_filename"]
                or not row["page_start"] <= physical_page <= row["page_end"]
            ):
                raise ValueError(f"Stale or invalid evidence label: {case_id}/{chunk_id}")
    results = []
    for case_id, question, evidence in CASES:
        gold = {chunk_id for chunk_id, _, _, _ in evidence}
        start = perf_counter()
        vector = embedding.vector_literal(embedding.embed_query(question))
        dense = embedding_repository.retrieve_all(vector, limit=20)
        dense_seconds = perf_counter() - start
        start = perf_counter()
        ranked = rerank_chunks(question, dense, limit=20)  # fail closed; no fallback
        rerank_seconds = perf_counter() - start
        dense_ids = [str(row["chunk_id"]) for row in dense]
        ranked_ids = [str(row["chunk_id"]) for row in ranked]
        if set(dense_ids) != set(ranked_ids):
            raise ValueError("Reranker changed candidate membership")
        item = {
            "id": case_id, "question": question,
            "evidence": [
                {"chunk_id": chunk_id, "quote": quote, "filename": filename, "physical_page": page}
                for chunk_id, quote, filename, page in evidence
            ],
            "dense": score(dense_ids, gold),
            "rerank": score(ranked_ids, gold),
            "dense_ids": dense_ids, "rerank_ids": ranked_ids,
            "dense_seconds": dense_seconds, "rerank_seconds": rerank_seconds,
        }
        results.append(item)
        print({"id": case_id, "dense": item["dense"], "rerank": item["rerank"]}, flush=True)
    if fingerprint(pool) != fingerprint(snapshot()):
        raise RuntimeError("Corpus changed during evaluation; discard this run")
    report = {
        "created_at": datetime.now(UTC).isoformat(), "split": "development_draft",
        "label_version": LABEL_VERSION,
        "limitations": "13 authored questions; manually reviewed known-equivalent spans; no held-out test; cold start included in timings",
        "corpus_sha256": fingerprint(pool), "cases_sha256": fingerprint(CASES),
        "chunks": len(pool), "documents": len({r['sha256'] for r in pool}),
        "embedding_model": embedding.active_model_id(),
        "chunk_token_budget": embedding.active_config().chunk_token_budget,
        "reranker_model": RERANKER_MODEL_NAME, "results": results,
        "averages": {mode: {metric: sum(r[mode][metric] for r in results) / len(results)
            for metric in ("hit_at_5", "hit_at_20", "rr_at_10")}
            for mode in ("dense", "rerank")},
    }
    path = Path("data/evaluation") / (datetime.now(UTC).strftime("seed_%Y%m%dT%H%M%S%fZ.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print({"report": str(path), "averages": report["averages"]}, flush=True)


if __name__ == "__main__":
    main()
