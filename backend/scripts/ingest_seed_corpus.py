"""Import a bounded local English corpus; reruns skip ready checksums.

Run from backend: python -m scripts.ingest_seed_corpus
Downloads are intentionally separate. Existing files are never overwritten.
"""
import asyncio
import hashlib
from pathlib import Path

from starlette.datastructures import UploadFile

from app.modules.documents.service import (
    document_repository,
    process_document,
    save_upload,
)

SOURCES = [
    (
        "Australia_AI_Transparency_Standard_v2.pdf",
        "bcd3a3cac366fce0d5b0f003ebaee7d66e5062020e204ed500d21d7ad1d99af1",
        "https://www.digital.gov.au/sites/default/files/documents/2025-12/Standard%20for%20AI%20transparency%20statements%202.0_0.pdf",
    ),
    (
        "Australia_AI_Staff_Training_v2.pdf",
        "7d81ab99a6d9239613ddee0370d034772335b75a3199c2316d5f568080d637c7",
        "https://www.digital.gov.au/sites/default/files/documents/2025-12/Guidance%20for%20staff%20training%20on%20AI%202.0.pdf",
    ),
    (
        "Australia_AI_Technical_Standard_2025.pdf",
        "fe44df0eb40e1d438125f5f46293fb2bd01a84abdec2fdaadf066abc0fcd2c24",
        "https://www.digital.gov.au/sites/default/files/documents/2025-08/Australian%20Government%20AI%20technical%20standard.pdf",
    ),
    (
        "Singapore_Model_AI_Governance_Framework_Agentic_AI.pdf",
        "2636e19ff1c86e862394d2fc900592e97b83c04cc35e3c8443108114b7f1dfba",
        None,  # Supplied project PDF; official byte/version match still pending.
    ),
]


def main() -> None:
    root = Path("data/source_documents")
    # Validate the entire batch before creating any records or spending API tokens.
    for name, checksum, _ in SOURCES:
        content = (root / name).read_bytes()
        if not content.startswith(b"%PDF-"):
            raise ValueError(f"Not a PDF: {name}")
        if hashlib.sha256(content).hexdigest() != checksum:
            raise ValueError(f"Checksum mismatch: {name}")
    for name, checksum, url in SOURCES:
        existing = document_repository.find_by_checksum(checksum)
        if existing:
            record = document_repository.get_record(str(existing["id"]))
            if record["status"] == "ready":
                print({"file": name, "status": "already_ready"}, flush=True)
                continue
            raise RuntimeError(f"Existing non-ready document requires review: {name}")
        with (root / name).open("rb") as handle:
            saved = asyncio.run(save_upload(
                UploadFile(file=handle, filename=name), source_url=url,
            ))
        print({"file": name, "id": saved["id"], "status": "processing"}, flush=True)
        process_document(saved["id"])
        print({"file": name, "id": saved["id"], "status": "ready"}, flush=True)


if __name__ == "__main__":
    main()
