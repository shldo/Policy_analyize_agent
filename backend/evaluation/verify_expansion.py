"""Audit isolated batch01 corpus integrity without running retrieval rankings."""

import json
from datetime import UTC, datetime
from pathlib import Path

from evaluation.dataset import digest, is_answerable, load_dataset, resolve_groups, verify_sources
from evaluation.run import check_pool, snapshot
from scripts.ingest_expansion_batch import MANIFEST, validate_files, validate_target

BASELINE_SNAPSHOT = "b7e675ee0c8846172070f1448e7d71046f0888b6c82f33affe1477ad62b57993"


def main():
    from app.core.config import get_settings
    from app.core.database import get_connection
    from app.modules.embedding import service as embedding

    validate_target(get_settings().database_url)
    batch = json.loads(MANIFEST.read_text(encoding="utf-8"))
    validate_files(batch, Path(batch["source_directory"]))
    manifest, cases = load_dataset(Path(batch["baseline_manifest"]).parent)
    anchors = verify_sources(manifest, cases, Path("data/source_documents"))
    pool, documents = snapshot()
    combined = {"documents": manifest["documents"] + batch["documents"]}
    check_pool(combined, pool, documents)
    baseline_hashes = {d["sha256"] for d in manifest["documents"]}
    old_pool = [r for r in pool if r["sha256"] in baseline_hashes]
    old_documents = [d for d in documents if d["sha256"] in baseline_hashes]
    old_digest = digest([old_pool, old_documents])
    if old_digest != BASELINE_SNAPSHOT:
        raise ValueError("Baseline chunks, vectors or document membership changed")
    for case in cases:
        if is_answerable(case):
            resolve_groups(case, pool)
    with get_connection() as connection:
        page_rows = connection.execute("""
            SELECT d.sha256, count(*) AS pages,
                   array_agg(p.page_number ORDER BY p.page_number)
                       FILTER (WHERE btrim(p.text) = '') AS empty_pages
            FROM document_pages p JOIN documents d ON p.document_id = d.id GROUP BY d.sha256
        """).fetchall()
    pages = {row["sha256"]: dict(row) for row in page_rows}
    for item in batch["documents"]:
        if pages[item["sha256"]]["pages"] != item["pages"]:
            raise ValueError(f"Page count mismatch: {item['filename']}")
    inventory = []
    for document in documents:
        chunks = [r for r in pool if r["sha256"] == document["sha256"]]
        inventory.append(
            {
                **document,
                **pages[document["sha256"]],
                "chunks": len(chunks),
                "vectors": sum(r["vector"] is not None for r in chunks),
                "context_headers": sum(
                    bool((r["metadata_json"] or {}).get("context_header")) for r in chunks
                ),
                "embedding_models": sorted({r["embedding_model"] for r in chunks}),
            }
        )
    report = {
        "created_at": datetime.now(UTC).isoformat(),
        "corpus_version": batch["corpus_version"],
        "status": "structural_validation_passed_not_quality_scoring",
        "corpus_snapshot_sha256": digest([pool, documents]),
        "baseline_snapshot_sha256": old_digest,
        "old_source_anchors_verified": anchors,
        "old_answerable_mappings_resolved": sum(is_answerable(c) for c in cases),
        "documents": len(documents),
        "chunks": len(pool),
        "dimension": embedding.active_dimension(),
        "embedding_model": embedding.active_model_id(),
        "inventory": inventory,
        "api_usage": None,
        "limitations": [
            "Ingestion metadata/header calls do not currently persist provider token usage",
            "Old anchors resolve; equivalent evidence and negative labels still need review",
            "No new quality scores or new test rankings were produced",
        ],
    }
    output = Path("data/evaluation")
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"expansion_audit_{datetime.now(UTC):%Y%m%dT%H%M%S%fZ}.json"
    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps({"report": str(path), "documents": len(documents), "chunks": len(pool)}))


if __name__ == "__main__":
    main()
