"""Validate batch01, then ingest only into its dedicated isolated database.

Run from backend: python -m scripts.ingest_expansion_batch [--run]
Default is file validation only; --run incurs configured metadata/header API usage.
"""

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

MANIFEST = Path("evaluation/corpora/expansion-batch01.json")
EXPANSION_HOST = "policy-expansion-db-batch01"


def validate_target(url):
    parsed = urlsplit(url)
    if (
        parsed.scheme != "postgresql+asyncpg"
        or parsed.hostname != EXPANSION_HOST
        or parsed.path != "/testdb"
        or parsed.port != 5432
        or parsed.query
    ):
        raise ValueError("Only the dedicated batch01 database is allowed")


def validate_files(manifest, root):
    seen = set()
    for item in manifest["documents"]:
        name = item["filename"]
        if Path(name).name != name or name in seen or "\\" in name:
            raise ValueError("Invalid or repeated filename")
        seen.add(name)
        content = (root / name).read_bytes()
        if not content.startswith(b"%PDF-"):
            raise ValueError(f"Not a PDF: {name}")
        if hashlib.sha256(content).hexdigest() != item["sha256"]:
            raise ValueError(f"Checksum mismatch: {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    root = Path(manifest["source_directory"])
    validate_files(manifest, root)
    if not args.run:
        print(json.dumps({"validated_files": len(manifest["documents"]), "writes": False}))
        return
    validate_target(os.environ.get("DATABASE_URL", ""))

    from starlette.datastructures import UploadFile

    from app.core.config import get_settings
    from app.core.database import get_connection
    from app.modules.documents.service import document_repository, process_document, save_upload

    validate_target(get_settings().database_url)
    baseline = json.loads(Path(manifest["baseline_manifest"]).read_text(encoding="utf-8"))
    required = {d["sha256"] for d in baseline["documents"]}
    allowed = required | {d["sha256"] for d in manifest["documents"]}
    with get_connection() as connection:
        rows = connection.execute("SELECT sha256, status FROM documents").fetchall()
    present = {row["sha256"] for row in rows}
    if not required <= present or not present <= allowed:
        raise ValueError("Database corpus is not the expected baseline plus this batch")
    if any(row["status"] != "ready" for row in rows):
        raise ValueError("Non-ready document requires review before resuming")
    for item in manifest["documents"]:
        existing = document_repository.find_by_checksum(item["sha256"])
        if existing:
            print(json.dumps({"file": item["filename"], "status": "already_ready"}), flush=True)
            continue
        with (root / item["filename"]).open("rb") as handle:
            saved = asyncio.run(
                save_upload(
                    UploadFile(file=handle, filename=item["filename"]),
                    source_url=item["source_url"],
                    imported_via="expansion_batch01",
                )
            )
        print(json.dumps({"file": item["filename"], "status": "processing"}), flush=True)
        process_document(saved["id"])
        record = document_repository.get_record(saved["id"])
        if record["status"] != "ready":
            raise RuntimeError("Document did not reach ready status")
        print(json.dumps({"file": item["filename"], "status": "ready"}), flush=True)


if __name__ == "__main__":
    main()
