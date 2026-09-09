"""Offline source-to-structure audit, no DB writes, no embedding or LLM calls."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import get_settings
from app.modules.documents.extraction import extract_document
from app.modules.documents.parent_child import build_parent_children
from app.modules.embedding.service import count_input_tokens
from evaluation.dataset import load_dataset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("evaluation/datasets/policy-v4"))
    parser.add_argument("--sources", type=Path, default=Path("data/source_documents"))
    parser.add_argument("--output", type=Path, default=Path("data/evaluation/structure"))
    args = parser.parse_args()
    manifest, _ = load_dataset(args.dataset)
    report = []
    for document in manifest["documents"]:
        pages = extract_document(args.sources / document["filename"])
        sections, children, stats = build_parent_children(
            pages,
            document_id=document["sha256"],
            title=document["filename"],
            settings=get_settings(),
            count=count_input_tokens,
        )
        parents = [s for s in sections if s["metadata_json"]["generation_parent"]]
        counts = stats["children_per_parent"]
        item = {
            "file": document["filename"],
            "stats": stats,
            "single_child_parent_ratio": sum(n == 1 for n in counts.values()) / max(1, len(counts)),
            "tiny_parent_ratio": sum(s["token_count"] < 100 for s in parents)
            / max(1, len(parents)),
            "sections": sections,
            "children": children,
        }
        report.append(item)
        print(
            json.dumps(
                {k: v for k, v in item.items() if k not in {"sections", "children", "stats"}}
            )
            + f" parents={len(parents)} children={len(children)}",
            flush=True,
        )
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / f"audit_{datetime.now(UTC):%Y%m%dT%H%M%S}.json"
    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(path)


if __name__ == "__main__":
    main()
