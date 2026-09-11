"""Build a reviewable, offline audit scaffold for saved answer generations.

This tool deliberately does not infer semantic correctness.  It records the
answer, citation identity mapping, atomic-claim candidates, and the fields a
reviewer must assess.  No model, database, benchmark runner, or runtime prompt
is invoked.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from evaluation.dataset import digest
except ModuleNotFoundError:  # Support direct `python evaluation/build_answer_audit.py`.
    from dataset import digest

_CITATION_MARKER = re.compile(r"\[(\d+)\]")
_KNOWN_ISSUES = {
    "DEV2-UN02": {
        "kind": "known_semantic_issue_pending_review",
        "detail": (
            "The saved answer attributes claims to the AI Technical Standard while "
            "citation [6] resolves to Child 3c867de1-2f08-4c34-9f39-de6d1591fa0f "
            "from the Policy for the Responsible Use of AI in Government."
        ),
        "child_id": "3c867de1-2f08-4c34-9f39-de6d1591fa0f",
        "citation_number": 6,
    }
}


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _directory_manifest(path: Path) -> str:
    digest = hashlib.sha256()
    for file_path in sorted(path.rglob("*.json")):
        digest.update(str(file_path.relative_to(path)).encode("utf-8"))
        digest.update(_sha256(file_path).encode("ascii"))
    return digest.hexdigest()


def _claim_units(answer: str) -> list[str]:
    return [unit.strip() for unit in re.split(r"(?<=[.!?])\s+|\n+", answer.strip()) if unit.strip()]


def _raw_chunks(source_row: dict[str, Any]) -> dict[str, dict[str, Any]]:
    packed = source_row.get("packed") or {}
    chunks = packed.get("raw_chunks") or packed.get("evidence") or []
    return {
        chunk.get("chunk_id"): chunk
        for chunk in chunks
        if isinstance(chunk, dict) and chunk.get("chunk_id")
    }


def _citation_records(source_row: dict[str, Any]) -> list[dict[str, Any]]:
    packed = source_row.get("packed") or {}
    raw_by_id = _raw_chunks(source_row)
    records: list[dict[str, Any]] = []
    for index, citation in enumerate(packed.get("citations") or [], start=1):
        citation = citation if isinstance(citation, dict) else {}
        child_id = citation.get("chunk_id")
        raw = raw_by_id.get(child_id, {})
        explicit_number = citation.get("number")
        number = explicit_number if isinstance(explicit_number, int) else index
        records.append(
            {
                "number": number,
                "child_id": child_id,
                "document_id": citation.get("document_id") or raw.get("document_id"),
                "title": (
                    citation.get("title")
                    or citation.get("doc_title")
                    or raw.get("doc_title")
                    or raw.get("file")
                ),
                "page": citation.get("page") or citation.get("page_start") or raw.get("page"),
                "page_end": citation.get("page_end") or raw.get("page_end"),
                "quote": citation.get("quote") or raw.get("text"),
                "identity_status": "resolved"
                if child_id or citation.get("source_url")
                else "unresolved",
                "source_url": citation.get("source_url"),
            }
        )
    return records


def _audit_case(source_row: dict[str, Any], generation_row: dict[str, Any]) -> dict[str, Any]:
    question_id = source_row.get("question_id") or generation_row.get("question_id")
    generation = generation_row.get("generation") or {}
    answer = str(generation.get("answer") or "")
    citations = _citation_records(source_row)
    inputs = {
        "question": source_row.get("question"),
        "context": (source_row.get("packed") or {}).get("context"),
        "citations": (source_row.get("packed") or {}).get("citations") or [],
    }
    expected_inputs_sha256 = digest(inputs)
    recorded_inputs_sha256 = generation_row.get("inputs_sha256")
    by_number = {citation["number"]: citation for citation in citations}
    cited_numbers = sorted({int(value) for value in _CITATION_MARKER.findall(answer)})
    unresolved_numbers = [number for number in cited_numbers if number not in by_number]

    claims = []
    for unit in _claim_units(answer):
        numbers = sorted({int(value) for value in _CITATION_MARKER.findall(unit)})
        claims.append(
            {
                "text": unit,
                "citation_numbers": numbers,
                "semantic_label": "pending",
                "support_label": "pending",
                "review_required": True,
            }
        )

    return {
        "question_id": question_id,
        "question": source_row.get("question"),
        "answer": answer,
        "answer_status": generation.get("status", "unknown"),
        "input_integrity": {
            "recorded_inputs_sha256": recorded_inputs_sha256,
            "expected_inputs_sha256": expected_inputs_sha256,
            "match": recorded_inputs_sha256 == expected_inputs_sha256,
            "database_snapshot_checked": False,
        },
        "runtime_citation_validation": generation.get("citation_validation") or {},
        "citation_numbers_used": cited_numbers,
        "citation_identity": {
            "records": citations,
            "unresolved_numbers": unresolved_numbers,
            "status": "resolved" if not unresolved_numbers else "unresolved",
            "convention": "explicit citation number, otherwise saved array order",
        },
        "atomic_claims": claims,
        "required_answer_points": source_row.get("required_answer_points") or [],
        "required_point_assessment": "pending",
        "actor_scope_conditions": {"status": "pending", "items": []},
        "review": {
            "status": "pending",
            "method": "offline_scaffold_only",
            "semantic_support_checked": False,
            "human_signoff": False,
        },
        "known_issue": _KNOWN_ISSUES.get(question_id),
    }


def build_audit(source_dir: Path, generation_dir: Path, output_dir: Path) -> dict[str, Any]:
    source_files = {
        path.stem: path for path in source_dir.glob("*.json") if path.name != "report.json"
    }
    generation_files = {
        path.stem: path for path in generation_dir.glob("*.json") if path.name != "report.json"
    }
    generation_report_path = generation_dir / "report.json"
    generation_report = (
        _read_json(generation_report_path) if generation_report_path.exists() else {}
    )

    cases: list[dict[str, Any]] = []
    missing_source: list[str] = []
    for question_id in sorted(generation_files):
        source_path = source_files.get(question_id)
        if source_path is None:
            missing_source.append(question_id)
            continue
        cases.append(
            _audit_case(_read_json(source_path), _read_json(generation_files[question_id]))
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    existing_outputs = [output_dir / name for name in ("audit.json", "INDEX.md")]
    if any(path.exists() for path in existing_outputs):
        raise FileExistsError(
            f"Refusing to overwrite an existing audit output: {output_dir}. "
            "Choose a new timestamped directory."
        )
    input_matches = sum(case["input_integrity"]["match"] for case in cases)
    audit = {
        "schema_version": "answer-audit-v1",
        "created_at": datetime.now(UTC).isoformat(),
        "status": "pending_manual_review",
        "review_method": "offline_identity_and_claim_scaffold; no semantic_auto_labeling",
        "source": {
            "path": str(source_dir.resolve()),
            "manifest_sha256": _directory_manifest(source_dir),
            "corpus_unchanged": None,
            "database_snapshot_status": "not_checked",
            "input_snapshot_status": "verified" if input_matches == len(cases) else "mismatch",
        },
        "generation": {
            "path": str(generation_dir.resolve()),
            "report_sha256": _sha256(generation_report_path)
            if generation_report_path.exists()
            else None,
            "model": generation_report.get("generation_target"),
            "prompt_version": generation_report.get("prompt_version"),
            "retrieval_calls": generation_report.get("retrieval_calls"),
            "outer_retries": generation_report.get("outer_retries"),
        },
        "counts": {
            "source_cases": len(source_files),
            "generation_cases": len(generation_files),
            "audited_cases": len(cases),
            "missing_source": len(missing_source),
            "registered_historical_issue_cases": sum(
                case["known_issue"] is not None for case in cases
            ),
            "input_hash_matches": input_matches,
            "input_hash_mismatches": len(cases) - input_matches,
            "unresolved_citation_cases": sum(
                case["citation_identity"]["status"] != "resolved" for case in cases
            ),
        },
        "missing_source_question_ids": missing_source,
        "cases": cases,
    }
    (output_dir / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Saved answer audit",
        "",
        "This is an offline review scaffold. Semantic labels remain pending.",
        "",
        f"- Cases: {len(cases)}",
        f"- Registered historical issues: {audit['counts']['registered_historical_issue_cases']}",
        f"- Input hash matches: {audit['counts']['input_hash_matches']}/{len(cases)}",
        "- Database snapshot: not checked by this tool",
        f"- Citation identity unresolved cases: {audit['counts']['unresolved_citation_cases']}",
        f"- Model: `{audit['generation']['model']}`",
        f"- Prompt: `{audit['generation']['prompt_version']}`",
        "",
        "| Question | Answer status | Citation identity | Semantic review | Known issue |",
        "|---|---|---|---|---|",
    ]
    for case in cases:
        lines.append(
            "| {question_id} | {answer_status} | {identity} | pending | {known} |".format(
                question_id=case["question_id"],
                answer_status=case["answer_status"],
                identity=case["citation_identity"]["status"],
                known="yes" if case["known_issue"] else "no",
            )
        )
    (output_dir / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--generation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit = build_audit(args.source, args.generation, args.output)
    print(json.dumps(audit["counts"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
