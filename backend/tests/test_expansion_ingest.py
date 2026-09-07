import hashlib
import json
from pathlib import Path

import pytest

from scripts.ingest_expansion_batch import validate_files, validate_target


@pytest.mark.parametrize(
    "host", ["db", "localhost", "127.0.0.1", "policy-expansion-db-batch01.evil"]
)
def test_rejects_non_expansion_database(host):
    with pytest.raises(ValueError):
        validate_target(f"postgresql+asyncpg://appuser:secret@{host}:5432/testdb")


def test_accepts_expansion_database():
    validate_target("postgresql+asyncpg://appuser:secret@policy-expansion-db-batch01:5432/testdb")


def test_validates_entire_batch(tmp_path):
    content = b"%PDF-test"
    (tmp_path / "valid.pdf").write_bytes(content)
    manifest = {
        "documents": [{"filename": "valid.pdf", "sha256": hashlib.sha256(content).hexdigest()}]
    }
    validate_files(manifest, tmp_path)
    manifest["documents"].append({"filename": "missing.pdf", "sha256": "0" * 64})
    with pytest.raises(FileNotFoundError):
        validate_files(manifest, tmp_path)


def test_rejects_checksum_mismatch(tmp_path):
    (tmp_path / "file.pdf").write_bytes(b"%PDF-test")
    with pytest.raises(ValueError, match="Checksum"):
        validate_files({"documents": [{"filename": "file.pdf", "sha256": "0" * 64}]}, tmp_path)


def test_rejects_traversal(tmp_path):
    with pytest.raises(ValueError, match="filename"):
        validate_files({"documents": [{"filename": "../outside.pdf"}]}, tmp_path)


@pytest.mark.parametrize("suffix", ["/other", "/testdb?host=db"])
def test_rejects_database_override(suffix):
    with pytest.raises(ValueError):
        validate_target(
            f"postgresql+asyncpg://appuser:secret@policy-expansion-db-batch01:5432{suffix}"
        )


def test_rejects_non_pdf(tmp_path):
    (tmp_path / "file.pdf").write_bytes(b"<html>download error</html>")
    with pytest.raises(ValueError, match="Not a PDF"):
        validate_files({"documents": [{"filename": "file.pdf", "sha256": "0" * 64}]}, tmp_path)


def test_batch_membership_is_five_distinct_new_sources():
    root = Path(__file__).parents[1]
    batch = json.loads(
        (root / "evaluation/corpora/expansion-batch01.json").read_text(encoding="utf-8")
    )
    old = json.loads((root / batch["baseline_manifest"]).read_text(encoding="utf-8"))
    hashes = {d["sha256"] for d in batch["documents"]}
    assert len(hashes) == len(batch["documents"]) == 5
    assert not hashes & {d["sha256"] for d in old["documents"]}
    assert sum(d["pages"] for d in batch["documents"]) == 151
