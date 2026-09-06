"""Small development-only retrieval comparison; no LLM generation or web search."""
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

# Labels are known evidence, not exhaustive relevance judgments.
CASES = [
    ("AU01", "How often must agencies review their AI transparency statements?",
     "20b225ff-f607-4607-9f95-593e2d430d12", "reviewed and updated annually"),
    ("AU02", "Who must agencies notify when publishing or changing an AI transparency statement, and how?",
     "20b225ff-f607-4607-9f95-593e2d430d12", "emailing ai@dta.gov.au"),
    ("AU03", "Within what period must agencies develop a strategic position on AI adoption?",
     "20b225ff-f607-4607-9f95-593e2d430d12", "within 6 months"),
    ("AU04", "How frequently must agencies share their AI use case register with the DTA?",
     "2658730a-006d-46ee-946c-fdc0a5ac6fc2", "every 6 months"),
    ("AU05", "When must mandatory responsible AI training be implemented, and which staff does it cover?",
     "072b16bc-e451-4627-944e-82eefc48dd28", "within 12 months"),
    ("TR01", "According to the staff training guidance, how long does the AI fundamentals module take?",
     "f8542e0f-f7bf-41dd-aaab-7edb19c7094b", "20 to 30 minutes"),
    ("TS01", "Does the transparency standard require agencies to list individual AI use cases publicly?",
     "2853d499-4844-4f19-bb7b-c7e52ce8f4d4", "not required to list individual use cases"),
    ("TS02", "What two classification dimensions must agencies list in their AI transparency statements?",
     "9ef7ed5c-7e13-4ff2-93a0-38f235505302", "both the usage patterns and domains"),
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
    for case_id, _, chunk_id, quote in CASES:
        if chunk_id not in lookup or quote not in lookup[chunk_id]["text"]:
            raise ValueError(f"Stale or invalid evidence label: {case_id}")
    results = []
    for case_id, question, chunk_id, _ in CASES:
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
            "id": case_id, "question": question, "label": chunk_id,
            "dense": score(dense_ids, {chunk_id}),
            "rerank": score(ranked_ids, {chunk_id}),
            "dense_ids": dense_ids, "rerank_ids": ranked_ids,
            "dense_seconds": dense_seconds, "rerank_seconds": rerank_seconds,
        }
        results.append(item)
        print({"id": case_id, "dense": item["dense"], "rerank": item["rerank"]}, flush=True)
    if fingerprint(pool) != fingerprint(snapshot()):
        raise RuntimeError("Corpus changed during evaluation; discard this run")
    report = {
        "created_at": datetime.now(UTC).isoformat(), "split": "development_draft",
        "limitations": "8 authored questions; partial labels; no held-out test; cold start included in timings",
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
