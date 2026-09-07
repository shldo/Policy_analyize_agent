"""Validate sources by default; retrieval execution requires an explicit --run."""

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from evaluation.dataset import (
    answerability,
    digest,
    is_answerable,
    load_dataset,
    resolve_groups,
    score_groups,
    verify_sources,
)


def snapshot():
    from psycopg import sql

    from app.core.database import get_connection
    from app.modules.embedding import service as embedding

    table = embedding.active_vector_table()
    with get_connection() as conn:
        rows = conn.execute(
            sql.SQL("""
            SELECT c.id, c.text, c.page_start, c.page_end, c.metadata_json,
                   d.sha256, d.original_filename,
                   e.embedding::text AS vector, e.embedding_model
            FROM document_chunks c JOIN documents d ON d.id=c.document_id
            LEFT JOIN {} e ON e.chunk_id=c.id
            WHERE d.approved=true AND d.access_level='public' ORDER BY c.id
        """).format(sql.Identifier(table))
        ).fetchall()
        docs = conn.execute("""
            SELECT sha256, original_filename, status
            FROM documents WHERE approved=true AND access_level='public' ORDER BY sha256
        """).fetchall()
    return [dict(r) for r in rows], [dict(r) for r in docs]


def check_pool(manifest, pool, documents):
    expected = {d["sha256"] for d in manifest["documents"]}
    if {d["sha256"] for d in documents} != expected or len(documents) != len(expected):
        raise ValueError("Corpus membership changed; publish/review a new corpus version")
    if (
        not pool
        or {r["sha256"] for r in pool} != expected
        or any(r["vector"] is None for r in pool)
    ):
        raise ValueError("Missing chunks or active-model vectors")
    if any(d["status"] != "ready" for d in documents):
        raise ValueError("Corpus contains documents that are not ready")


def retrieval_cases(cases, split, allow_draft=False):
    """Gate only scored cases; unresolved candidates remain explicitly excluded."""
    selected = [c for c in cases if c["split"] == split]
    scored = [c for c in selected if is_answerable(c)]
    if not scored:
        raise ValueError("No answerable cases for retrieval scoring")
    if any(c["review_status"] != "reviewed" for c in scored) and not allow_draft:
        raise ValueError("Draft labels: human review required, or explicitly use --allow-draft")
    return selected, scored


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset", type=Path, default=Path(__file__).parent / "datasets/policy-v4"
    )
    parser.add_argument("--sources", type=Path, default=Path("data/source_documents"))
    parser.add_argument("--output", type=Path, default=Path("data/evaluation"))
    parser.add_argument("--database", action="store_true", help="Validate current database anchors")
    parser.add_argument("--run", action="store_true", help="Consume selected split for retrieval")
    parser.add_argument("--split", choices=["development", "test"], default="development")
    parser.add_argument(
        "--allow-draft", action="store_true", help="Exploratory run, not final scores"
    )
    parser.add_argument("--code-version", help="Host git commit SHA for an executed benchmark")
    parser.add_argument(
        "--compare-hybrid", action="store_true", help="Development-only BM25/RRF ablation"
    )
    args = parser.parse_args()
    if args.compare_hybrid and (not args.run or args.split != "development"):
        parser.error("--compare-hybrid requires --run --split development")
    manifest, cases = load_dataset(args.dataset)
    anchors = verify_sources(manifest, cases, args.sources)
    report = {
        "created_at": datetime.now(UTC).isoformat(),
        "dataset_version": manifest["dataset_version"],
        "corpus_version": manifest["corpus_version"],
        "dataset_sha256": digest({"manifest": manifest, "cases": cases}),
        "mode": "validation",
        "split_counts": dict(Counter(c["split"] for c in cases)),
        "answerability_counts": dict(Counter(answerability(c) for c in cases)),
        "source_anchors_verified": anchors,
        "semantic_review": "not implied by text-anchor validation",
        "test_rankings_observed": False,
    }
    if args.database or args.run:
        pool, documents = snapshot()
        check_pool(manifest, pool, documents)
        resolved = {c["question_id"]: resolve_groups(c, pool) for c in cases if is_answerable(c)}
        report.update(
            {
                "chunks": len(pool),
                "corpus_snapshot_sha256": digest([pool, documents]),
                "resolved_answerable_questions": len(resolved),
            }
        )
    if args.run:
        if not args.code_version:
            parser.error("--code-version is required to record reproducibility")
        selected, scored = retrieval_cases(cases, args.split, args.allow_draft)
        from app.modules.documents.repositories.embeddings import embedding_repository
        from app.modules.documents.reranker import RERANKER_MODEL_NAME, rerank_chunks
        from app.modules.embedding import service as embedding

        config = {
            "embedding_model": embedding.active_model_id(),
            "dimension": embedding.active_dimension(),
            "vector_table": embedding.active_vector_table(),
            "reranker": RERANKER_MODEL_NAME,
            "reranker_path": "controlled local cross-encoder; not runtime provider selection",
            "candidate_k": 20,
            "final_k": 5,
        }
        if args.compare_hybrid:
            from evaluation.hybrid import (
                BM25_B,
                BM25_K1,
                RRF_CONSTANT,
                BM25Index,
                reciprocal_rank_fusion,
            )

            lexical_index = BM25Index(pool)
            config["hybrid"] = {
                "bm25_k1": BM25_K1,
                "bm25_b": BM25_B,
                "rrf_constant": RRF_CONSTANT,
                "branch_k": 20,
                "fused_k": 20,
                "tokenizer": "NFKC lowercase ASCII alphanumeric; no stopwords or stemming",
                "scope": "same frozen public approved chunk pool; in-memory evaluation only",
            }
        if {r["embedding_model"] for r in pool} != {config["embedding_model"]}:
            raise ValueError("Stored embedding model does not match query model")
        report.update(
            {
                "mode": "retrieval",
                "split": args.split,
                "exploratory": any(c["review_status"] != "reviewed" for c in scored),
                "scored_count": len(scored),
                "scoring_scope": "answerable retrieval only; no generation or refusal scoring",
                "test_rankings_observed": args.split == "test",
                "code_version": args.code_version,
                "config": config,
                "timing_note": "Includes cold start; not a latency benchmark",
                "unanswerable_not_scored": [
                    c["question_id"]
                    for c in selected
                    if answerability(c) == "unanswerable_confirmed"
                ],
                "unresolved_not_scored": [
                    c["question_id"] for c in selected if answerability(c) == "unresolved_candidate"
                ],
                "limitations": manifest["limitations"],
                "results": [],
            }
        )
        for case in scored:
            start = perf_counter()
            vector = embedding.vector_literal(embedding.embed_query(case["question"]))
            dense = embedding_repository.retrieve_all(vector, limit=20)
            dense_seconds = perf_counter() - start
            start = perf_counter()
            ranked = rerank_chunks(case["question"], dense, limit=20)
            rerank_seconds = perf_counter() - start
            dense_ids = [str(r["chunk_id"]) for r in dense]
            ranked_ids = [str(r["chunk_id"]) for r in ranked]
            if set(dense_ids) != set(ranked_ids):
                raise ValueError("Reranker changed candidate membership")
            mode_ids = {"dense": dense_ids, "rerank": ranked_ids}
            extra = {}
            if args.compare_hybrid:
                start = perf_counter()
                lexical = lexical_index.search(case["question"], limit=20)
                fused = reciprocal_rank_fusion([dense, lexical], limit=20)
                extra["hybrid_seconds"] = perf_counter() - start
                start = perf_counter()
                hybrid_ranked = rerank_chunks(case["question"], fused, limit=20)
                extra["hybrid_rerank_seconds"] = perf_counter() - start
                for name, rows in (
                    ("bm25", lexical),
                    ("hybrid", fused),
                    ("hybrid_rerank", hybrid_ranked),
                ):
                    mode_ids[name] = [str(row["chunk_id"]) for row in rows]
                    extra[name + "_ids"] = mode_ids[name]
                if set(mode_ids["hybrid"]) != set(mode_ids["hybrid_rerank"]):
                    raise ValueError("Hybrid reranker changed candidate membership")
            scores = {}
            for mode, ids in mode_ids.items():
                scores[mode] = {}
                for k in (5, 10, 20):
                    scores[mode].update(score_groups(ids, resolved[case["question_id"]], k))
            report["results"].append(
                {
                    "question_id": case["question_id"],
                    "category": case["category"],
                    "dense_ids": dense_ids,
                    "rerank_ids": ranked_ids,
                    "dense_seconds": dense_seconds,
                    "rerank_seconds": rerank_seconds,
                    **extra,
                    "scores": scores,
                }
            )
            print(
                f"Completed {case['question_id']} ({len(report['results'])}/{len(scored)})",
                flush=True,
            )
        if not report["results"]:
            raise ValueError("No answerable cases for retrieval scoring")
        if digest(list(snapshot())) != report["corpus_snapshot_sha256"]:
            raise ValueError("Corpus changed during run; results discarded")
        if embedding.active_model_id() != config["embedding_model"]:
            raise ValueError("Embedding configuration changed during run")
        report["averages"] = {
            mode: {
                metric: sum(r["scores"][mode][metric] for r in report["results"])
                / len(report["results"])
                for metric in report["results"][0]["scores"][mode]
            }
            for mode in report["results"][0]["scores"]
        }
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / (datetime.now(UTC).strftime("benchmark_%Y%m%dT%H%M%S%fZ.json"))
    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False, default=str)
    print(
        json.dumps(
            {
                "report": str(path),
                **{k: v for k, v in report.items() if k not in {"results", "limitations"}},
            },
            default=str,
        )
    )


if __name__ == "__main__":
    main()
