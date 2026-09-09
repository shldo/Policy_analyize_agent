"""Isolated A/B/C pilot, reusing reviewed questions and exact evidence-group scoring.

Default is read-only. Rebuild requires the exact current snapshot hash. Never
point this runner at the business DB: use a restored copy of the frozen corpus.
"""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from evaluation.dataset import digest, is_answerable, load_dataset, resolve_groups, score_groups
from evaluation.run import check_pool, snapshot


def section_snapshot():
    from app.core.database import get_connection

    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM document_sections ORDER BY id").fetchall()
    return digest([dict(row) for row in rows])


def rebuild(manifest, sources, variant):
    from app.core.config import get_settings
    from app.core.database import get_connection
    from app.modules.documents.extraction import extract_document
    from app.modules.documents.ingestion.contextual_header import build_contextual_headers
    from app.modules.documents.parent_child import build_parent_children, embedding_input
    from app.modules.documents.repositories.embeddings import embedding_repository
    from app.modules.embedding import service as embedding

    settings = get_settings().model_copy(update={"use_llm_contextual_header": variant == "C"})
    reports = []
    for source in manifest["documents"]:
        path = sources / source["filename"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("Source checksum mismatch")
        with get_connection() as conn:
            doc = conn.execute(
                """SELECT d.id, dm.title, dm.summary, dm.language
                FROM documents d LEFT JOIN document_metadata dm ON d.id=dm.document_id
                WHERE d.sha256=%s""",
                (source["sha256"],),
            ).fetchone()
        started = perf_counter()
        pages = extract_document(path)
        sections, children, stats = build_parent_children(
            pages,
            document_id=str(doc["id"]),
            title=doc["title"] or source["filename"],
            settings=settings,
            count=embedding.count_input_tokens,
        )
        header_start = perf_counter()
        headers = (
            build_contextual_headers(children, title=doc["title"], summary=doc["summary"])
            if variant == "C"
            else [None] * len(children)
        )
        stats["header_seconds"] = perf_counter() - header_start
        stats["header_requests"] = len(children) if variant == "C" else 0
        stats["headers_generated"] = sum(bool(h) for h in headers)
        inputs = []
        for child, header in zip(children, headers, strict=True):
            if header:
                child["metadata_json"]["context_header"] = header
            inputs.append(
                embedding_input(
                    child, header, settings=settings, count=embedding.count_input_tokens
                )
            )
        stats["embedding_input_tokens"] = sum(embedding.count_tokens(t) for t in inputs)
        vectors = [embedding.vector_literal(v) for v in embedding.embed_documents(inputs)]
        embedding_repository.replace_document_chunks(
            str(doc["id"]), children, vectors, language=doc["language"], sections=sections
        )
        stats["ingestion_seconds"] = perf_counter() - started
        reports.append({"filename": source["filename"], **stats})
        print(
            f"Indexed {source['filename']}: {len(sections)} sections, {len(children)} children",
            flush=True,
        )
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=["A", "B", "C"], required=True)
    parser.add_argument("--dataset", type=Path, default=Path("evaluation/datasets/policy-v4"))
    parser.add_argument("--sources", type=Path, default=Path("data/source_documents"))
    parser.add_argument("--output", type=Path, default=Path("data/evaluation/parent_child"))
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--expected-snapshot")
    parser.add_argument("--code-version", required=True)
    parser.add_argument("--candidate-k", type=int, default=30)
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Collect development answers for review; incurs configured API usage",
    )
    args = parser.parse_args()
    from app.modules.chat.rag.parent_pipeline import prepare_child_context
    from app.modules.documents.repositories.embeddings import embedding_repository
    from app.modules.documents.service import _rerank_or_dense
    from app.modules.embedding import service as embedding

    manifest, cases = load_dataset(args.dataset)
    pool, docs = snapshot()
    check_pool(manifest, pool, docs)
    before = digest([pool, docs])
    ingestion = []
    if args.rebuild:
        if args.variant == "A" or args.expected_snapshot != before:
            parser.error("Rebuild requires B/C and exact --expected-snapshot of isolated database")
        ingestion = rebuild(manifest, args.sources, args.variant)
        pool, docs = snapshot()
    fingerprint = digest([pool, docs])
    parent_fingerprint = section_snapshot()
    report = {
        "variant": args.variant,
        "code_version": args.code_version,
        "dataset_sha256": digest([manifest, cases]),
        "before_snapshot": before,
        "corpus_snapshot": fingerprint,
        "parent_snapshot": parent_fingerprint,
        "source_code_sha256": digest(
            {
                str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for folder in (Path("app"), Path("evaluation"))
                for path in sorted(folder.rglob("*.py"))
            }
        ),
        "chunks": len(pool),
        "ingestion": ingestion,
        "candidate_k": args.candidate_k,
        "results": [],
        "unmapped": [],
        "split": "development",
        "generation_semantic_scores": "requires human review",
        "latency_note": "Single pilot including cold start, not production p95",
        "thresholds": "unchanged",
        "scoring": "existing exact single-child anchor mapping",
    }
    selected = [c for c in cases if c["split"] == "development" and is_answerable(c)]
    for case in selected:
        if case["review_status"] != "reviewed":
            raise ValueError("Unreviewed development case")
        try:
            groups = resolve_groups(case, pool)
        except ValueError as exc:
            report["unmapped"].append({"question_id": case["question_id"], "reason": str(exc)})
            continue
        start = perf_counter()
        vector = embedding.vector_literal(embedding.embed_query(case["question"]))
        candidates = embedding_repository.retrieve_all(vector, limit=args.candidate_k)
        ranked = _rerank_or_dense(case["question"], candidates, args.candidate_k)
        if any("reranker_score" not in row for row in ranked):
            raise ValueError(
                "Benchmark requires successful cross-encoder; dense fallback not scored"
            )
        packed = prepare_child_context(case["question"], ranked[:8])
        generation = {"status": "not_run"}
        if args.generate and packed["evidence_sufficient"]:
            from app.modules.chat.rag.generation import generate_answer
            from evaluation.generation import citation_checks

            generation_started = perf_counter()
            answer, model = generate_answer(
                case["question"], packed["context"], citations=packed["citations"]
            )
            generation = {
                "status": "pending_human_review",
                "answer": answer,
                "model": model,
                "seconds": perf_counter() - generation_started,
                "citation_syntax": citation_checks(answer, len(packed["citations"])),
                "reference_answer": case["reference_answer"],
                "required_answer_points": case["required_answer_points"],
            }
        scores = {}
        for k in (5, 10, 20):
            scores.update(score_groups([c["chunk_id"] for c in ranked], groups, k))
        report["results"].append(
            {
                "question_id": case["question_id"],
                "scores": scores,
                "seconds": perf_counter() - start,
                "candidates": candidates,
                "ranked": ranked,
                "packed": packed,
                "generation": generation,
            }
        )
        print(f"Evaluated {args.variant}/{case['question_id']}", flush=True)
    report["scored_count"] = len(report["results"])
    report["eligible_count"] = len(selected)
    report["averages"] = {
        key: sum(r["scores"][key] for r in report["results"]) / len(report["results"])
        for key in (report["results"][0]["scores"] if report["results"] else {})
    }
    if digest(list(snapshot())) != fingerprint:
        raise ValueError("Corpus changed during evaluation")
    if section_snapshot() != parent_fingerprint:
        raise ValueError("Parent contexts changed during evaluation")
    args.output.mkdir(parents=True, exist_ok=True)
    output = args.output / f"{args.variant}_{datetime.now(UTC):%Y%m%dT%H%M%S}.json"
    with output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, default=str, indent=2)
    print(
        json.dumps(
            {
                "report": str(output),
                "snapshot": fingerprint,
                "averages": report["averages"],
                "unmapped": report["unmapped"],
            }
        )
    )


if __name__ == "__main__":
    main()
