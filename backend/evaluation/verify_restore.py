"""Read-only comparison of application table contents after an isolated restore."""

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def query(container, sql):
    result = subprocess.run(
        [
            "docker",
            "exec",
            container,
            "psql",
            "-X",
            "-U",
            "appuser",
            "-d",
            "testdb",
            "-At",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            sql,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return result.stdout.strip()


def fingerprint(container):
    names = query(
        container, "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
    ).splitlines()
    result = {}
    for name in names:
        table = '"' + name.replace('"', '""') + '"'
        sql = f"""SELECT json_build_object('rows', count(*), 'content_md5',
            md5(coalesce(string_agg(row_text, E'\\n' ORDER BY row_text COLLATE "C"), '')))
            FROM (SELECT row_to_json(t)::text AS row_text FROM public.{table} t) rows"""
        result[name] = json.loads(query(container, sql))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--restored", required=True)
    parser.add_argument("--backup-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.source == args.restored or not args.restored.startswith("policy-restore-check-"):
        parser.error("Expected a separate policy-restore-check container")
    source = fingerprint(args.source)
    restored = fingerprint(args.restored)
    changed = [
        name
        for name in sorted(source.keys() | restored.keys())
        if source.get(name) != restored.get(name)
    ]
    files = {}
    for path in sorted(args.backup_dir.rglob("*")):
        if path.is_file() and path.name != "restore_verification.json":
            with path.open("rb") as handle:
                files[path.relative_to(args.backup_dir).as_posix()] = hashlib.file_digest(
                    handle, "sha256"
                ).hexdigest()
    report = {
        "created_at": datetime.now(UTC).isoformat(),
        "status": "passed" if not changed else "mismatch",
        "source": args.source,
        "restored": args.restored,
        "table_count": len(source),
        "source_tables": source,
        "restored_tables": restored,
        "mismatched_tables": changed,
        "backup_file_sha256": files,
        "scope": (
            "public table rows/content; not application authentication, "
            "sequences or whole-app recovery"
        ),
    }
    with (args.backup_dir / "restore_verification.json").open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(
        json.dumps(
            {
                "status": report["status"],
                "tables": len(source),
                "mismatched_tables": changed,
                "backup_files": len(files),
            }
        )
    )
    if changed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
