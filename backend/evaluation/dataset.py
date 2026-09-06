"""Portable evidence groups and strict, versioned dataset validation."""

import hashlib
import json
import re
import unicodedata
from pathlib import Path


def normalize(text):
    return " ".join(unicodedata.normalize("NFKC", text).split())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def load_dataset(path):
    path = Path(path)
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    cases = [
        json.loads(line)
        for line in (path / "questions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    validate(manifest, cases)
    return manifest, cases


def validate(manifest, cases):
    if manifest["schema_version"] != 1 or not cases:
        raise ValueError("Unsupported schema or empty dataset")
    documents = manifest["documents"]
    if not documents or len({d["sha256"] for d in documents}) != len(documents):
        raise ValueError("Missing or duplicate documents")
    hashes = {d["sha256"] for d in documents}
    for doc in documents:
        if not re.fullmatch(r"[0-9a-f]{64}", doc["sha256"]):
            raise ValueError("Invalid document hash")
        if Path(doc["filename"]).name != doc["filename"] or "\\" in doc["filename"]:
            raise ValueError("Document filename must be a basename")
    ids, questions, groups, anchor_splits = set(), set(), {}, {}
    for case in cases:
        key = case["question_id"]
        if key in ids or normalize(case["question"]).casefold() in questions:
            raise ValueError("Duplicate question ID or question")
        ids.add(key)
        questions.add(normalize(case["question"]).casefold())
        if case["split"] not in {"development", "test"}:
            raise ValueError("Unknown split")
        if type(case["answerable"]) is not bool:
            raise ValueError("answerable must be boolean")
        if case["review_status"] not in {"draft", "reviewed"}:
            raise ValueError("Unknown review status")
        for field in ("question", "category", "rationale", "reference_answer", "leakage_group"):
            if not isinstance(case[field], str) or not case[field].strip():
                raise ValueError(f"Missing {field}: {key}")
        if case["language"] != "en" or case["corpus_version"] != manifest["corpus_version"]:
            raise ValueError("Language or corpus version mismatch")
        group = case["leakage_group"]
        if group in groups and groups[group] != case["split"]:
            raise ValueError(f"Cross-split evidence topic: {group}")
        groups[group] = case["split"]
        if case["review_status"] == "reviewed" and not case.get("reviewed_by"):
            raise ValueError("Reviewed questions need a reviewer")
        evidence = case["evidence_groups"]
        if case["answerable"] != bool(evidence):
            raise ValueError("Answerability/evidence mismatch")
        if not case["answerable"] and not case.get("absence_review"):
            raise ValueError("Unanswerable question needs absence review instructions")
        group_ids = set()
        for item in evidence:
            if item["id"] in group_ids or not item["alternatives"] or not item["answer_point"]:
                raise ValueError("Invalid evidence group")
            group_ids.add(item["id"])
            for anchor in item["alternatives"]:
                start, end = anchor["page_start"], anchor["page_end"]
                if (
                    anchor["document_sha256"] not in hashes
                    or type(start) is not int
                    or type(end) is not int
                    or not 1 <= start <= end
                    or not normalize(anchor["quote"])
                ):
                    raise ValueError(f"Invalid anchor: {key}")
                identity = (anchor["document_sha256"], normalize(anchor["quote"]))
                if identity in anchor_splits and anchor_splits[identity] != case["split"]:
                    raise ValueError("Exact evidence anchor crosses splits")
                anchor_splits[identity] = case["split"]
    return {"questions": len(cases), "documents": len(documents)}


def resolve_groups(case, chunks):
    """OR within a group, AND across groups; never bind labels to ingestion UUIDs."""
    resolved = []
    for group in case["evidence_groups"]:
        matches = set()
        for anchor in group["alternatives"]:
            for chunk in chunks:
                if (
                    chunk["sha256"] == anchor["document_sha256"]
                    and chunk["page_start"] <= anchor["page_end"]
                    and chunk["page_end"] >= anchor["page_start"]
                    and normalize(anchor["quote"]) in normalize(chunk["text"])
                ):
                    matches.add(str(chunk["id"]))
        if not matches:
            raise ValueError(f"Unresolved evidence: {case['question_id']}/{group['id']}")
        resolved.append(matches)
    return resolved


def score_groups(ids, groups, k=5):
    """Known required-evidence coverage; not exhaustive relevant-chunk Recall."""
    if k < 1 or not groups or any(not group for group in groups):
        raise ValueError("Positive k and nonempty evidence groups required")
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate retrieved IDs")
    top = set(ids[:k])
    covered = sum(bool(top & group) for group in groups)
    first = next(
        (i for i, key in enumerate(ids[:10], 1) if any(key in group for group in groups)), None
    )
    return {
        f"hit_at_{k}": int(covered > 0),
        f"evidence_group_coverage_at_{k}": covered / len(groups),
        f"all_evidence_at_{k}": int(covered == len(groups)),
        "rr_at_10": 1 / first if first else 0,
    }


def verify_sources(manifest, cases, directory):
    """Validate physical PDF pages; semantic review is a separate human action."""
    import pymupdf

    pages = {}
    for doc in manifest["documents"]:
        path = Path(directory) / doc["filename"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != doc["sha256"]:
            raise ValueError(f"Source hash changed: {doc['filename']}")
        with pymupdf.open(path) as pdf:
            pages[doc["sha256"]] = [page.get_text() for page in pdf]
    count = 0
    for case in cases:
        for group in case["evidence_groups"]:
            for anchor in group["alternatives"]:
                source = pages[anchor["document_sha256"]]
                if anchor["page_end"] > len(source):
                    raise ValueError(f"Page out of bounds: {case['question_id']}")
                text = " ".join(source[anchor["page_start"] - 1 : anchor["page_end"]])
                if normalize(anchor["quote"]) not in normalize(text):
                    raise ValueError(f"Source anchor not found: {case['question_id']}: {anchor}")
                count += 1
    return count
