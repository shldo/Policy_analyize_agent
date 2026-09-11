from __future__ import annotations

import json

import pytest

from evaluation.build_answer_audit import build_audit
from evaluation.dataset import digest


def _write_case(source_dir, generation_dir) -> None:
    source = {
        "question_id": "CASE01",
        "question": "What does the policy require?",
        "required_answer_points": ["state the requirement"],
        "packed": {
            "context": "The policy requires training.",
            "citations": [{"chunk_id": "child-1", "document_id": "doc-1"}],
            "raw_chunks": [
                {
                    "chunk_id": "child-1",
                    "document_id": "doc-1",
                    "doc_title": "Policy",
                    "page": 2,
                    "text": "The policy requires training.",
                }
            ],
        },
    }
    inputs = {
        "question": source["question"],
        "context": source["packed"]["context"],
        "citations": source["packed"]["citations"],
    }
    generation = {
        "question_id": "CASE01",
        "inputs_sha256": digest(inputs),
        "generation": {
            "status": "generated_pending_review",
            "answer": "The policy requires training [1].",
            "citation_validation": {"valid_identity": True},
        },
    }
    (source_dir / "CASE01.json").write_text(json.dumps(source), encoding="utf-8")
    (generation_dir / "CASE01.json").write_text(json.dumps(generation), encoding="utf-8")


def test_audit_distinguishes_input_match_from_database_snapshot(tmp_path) -> None:
    source_dir = tmp_path / "source"
    generation_dir = tmp_path / "generation"
    output_dir = tmp_path / "audit"
    source_dir.mkdir()
    generation_dir.mkdir()
    _write_case(source_dir, generation_dir)

    audit = build_audit(source_dir, generation_dir, output_dir)

    assert audit["source"]["corpus_unchanged"] is None
    assert audit["source"]["database_snapshot_status"] == "not_checked"
    assert audit["source"]["input_snapshot_status"] == "verified"
    assert audit["counts"]["input_hash_matches"] == 1
    assert audit["counts"]["registered_historical_issue_cases"] == 0


def test_audit_refuses_to_overwrite_existing_output(tmp_path) -> None:
    source_dir = tmp_path / "source"
    generation_dir = tmp_path / "generation"
    output_dir = tmp_path / "audit"
    source_dir.mkdir()
    generation_dir.mkdir()
    _write_case(source_dir, generation_dir)

    build_audit(source_dir, generation_dir, output_dir)

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        build_audit(source_dir, generation_dir, output_dir)
