import json
from types import SimpleNamespace

from evaluation import verify_restore


def test_fingerprint_quotes_identifiers_and_only_reads(monkeypatch):
    calls = []

    def query(container, sql):
        calls.append(sql)
        if "pg_tables" in sql:
            return 'documents\nodd"name'
        return json.dumps({"rows": 2, "content_md5": "abc"})

    monkeypatch.setattr(verify_restore, "query", query)
    assert verify_restore.fingerprint("isolated")["documents"]["rows"] == 2
    assert 'public."odd""name"' in calls[2]
    assert all(sql.strip().startswith("SELECT") for sql in calls)


def test_query_uses_argument_list_and_fails_on_sql_errors(monkeypatch):
    def run(args, **kwargs):
        assert isinstance(args, list)
        assert "ON_ERROR_STOP=1" in args
        assert kwargs["check"] is True
        return SimpleNamespace(stdout="  value\n")

    monkeypatch.setattr(verify_restore.subprocess, "run", run)
    assert verify_restore.query("isolated", "SELECT 1") == "value"
