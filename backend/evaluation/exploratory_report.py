"""Render saved exploratory observations without making any model calls."""

import argparse
import json
from collections import Counter
from pathlib import Path


def summarize(rows):
    scored = [r for r in rows if r.get("reranked_scores") is not None]
    stages = {}
    for name in ("candidate_scores", "reranked_scores", "gated_scores", "packed_scores"):
        available = [r[name] for r in scored if r.get(name) is not None]
        stages[name] = {
            "denominator": len(available),
            "averages": {
                k: sum(r[k] for r in available) / len(available)
                for k in (available[0] if available else {})
            },
        }
    return {
        "count": len(rows),
        "status": dict(Counter(r["status"] for r in rows)),
        "generation": dict(Counter(r["generation"]["status"] for r in rows)),
        "stages": stages,
        "unscored_ids": [r["question_id"] for r in rows if r.get("reranked_scores") is None],
        "citation_invalid_ids": [
            r["question_id"]
            for r in rows
            if r["generation"].get("citation_syntax", {}).get("invalid_markers")
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    report = json.loads((args.folder / "report.json").read_text(encoding="utf-8"))
    rows = [
        json.loads((args.folder / f"{key}.json").read_text(encoding="utf-8"))
        for key in report["selected_ids"]
        if (args.folder / f"{key}.json").exists()
    ]
    summary = summarize(rows)
    (args.folder / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    text = f"# {len(rows)} 题探索性回答审阅\n\n"
    text += "非正式成绩。参考答案仍是 draft；引用编号有效不代表引用支持结论。\n\n"
    text += f"运行状态：{report['status']}；"
    text += f"语料未变：{report.get('corpus_unchanged', '待完成检查')}。\n\n"
    for row in rows:
        text += f"## {row['question_id']} — {row['category']}\n\n"
        text += f"Question: {row['question']}\n\n状态：{row['status']} / "
        text += f"{row['generation']['status']}；映射：{row['mapping_status']}\n\n"
        text += f"参考答案（待审）：{row['reference_answer']}\n\n### 实际回答\n\n"
        text += f"{row['generation'].get('answer', '未产生回答')}\n\n"
        text += "### 实际引用证据\n\n"
        for i, citation in enumerate(row.get("packed", {}).get("citations", []), 1):
            text += f"[{i}] {citation.get('title')}，页 {citation.get('page')}–"
            text += f"{citation.get('page_end')}；Child `{citation.get('chunk_id')}`\n\n"
            text += f"{citation.get('quote')}\n\n"
        text += "语义审核：待审核，不由程序自动通过。完整中间产物见同目录逐题 JSON。\n\n"
    (args.folder / "answers_review.md").write_text(text, encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
