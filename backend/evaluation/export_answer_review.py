"""Export saved model-assisted reviews for independent human signoff; no API calls."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report = json.loads((args.source / "report.json").read_text(encoding="utf-8"))
    index = [
        "# C 全量答案审核包",
        "",
        "50 份模型辅助初审，不是人工签核。逐题复核答案与实际引用 Child；judge 标签仅为候选意见。",
        "",
        "|题目|机器结构校验|候选结论|人工签核|",
        "|---|---|---|---|",
    ]
    for item in sorted(report["results"], key=lambda r: r["question_id"]):
        key = item["question_id"]
        row = json.loads((args.source / f"{key}.json").read_text(encoding="utf-8"))
        source = row["inputs"]
        lines = [
            f"# {key}",
            "",
            "人工签核：pending。审核者/日期：待填写。",
            "",
            "## 问题",
            "",
            source["question"],
            "",
            "## 原始答案（未修改）",
            "",
            source["answer"],
            "",
            "## Reference（不是 generation 输入）",
            "",
            str(source.get("reference_answer", "")),
            "",
            "## 实际 Child 引用（Parent 不自动获得引用资格）",
            "",
        ]
        for c in source["child_citations"]:
            lines += [
                f"### [{c['number']}] {c.get('title', '')}",
                "",
                f"Child: `{c.get('chunk_id')}`; section: `{c.get('section_id')}`; "
                f"pages: {c.get('page')}–{c.get('page_end')}",
                "",
                c.get("quote", ""),
                "",
            ]
        lines += [
            "## 模型辅助初审（需独立核验）",
            "",
            "```json",
            json.dumps(row.get("review", {}), ensure_ascii=False, indent=2),
            "```",
            "",
            "结构校验：" + str(row.get("validation_errors", [])),
            "",
            "## 审核记录",
            "",
            "- 结论：pending",
            "- 原子断言/Child/支持标签/理由：待填写",
            "- 缺失要点与安全的部分回答分开记录。不得将未检索到等同全文不存在。",
            "",
        ]
        (args.output / f"{key}.md").write_text("\n".join(lines), encoding="utf-8")
        index.append(f"|[{key}]({key}.md)|{item['status']}|{item['verdict']}|pending|")
    (args.output / "INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(args.output / "INDEX.md")


if __name__ == "__main__":
    main()
