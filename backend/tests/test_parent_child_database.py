"""Opt-in transaction/FK integration tests against an isolated migrated database."""

import os
from uuid import uuid4

import pytest

from app.core.database import get_connection

pytestmark = pytest.mark.skipif(not os.getenv("PARENT_CHILD_DB_TEST"), reason="isolated DB opt-in")


def test_additive_migration_and_cross_document_fk():
    import psycopg

    with get_connection() as conn:
        doc = conn.execute("SELECT id FROM documents LIMIT 1").fetchone()["id"]
        # Exercise nullable transition even after the isolated corpus was reprocessed.
        conn.execute(
            "UPDATE document_chunks SET section_id=NULL, child_index=NULL "
            "WHERE id=(SELECT id FROM document_chunks WHERE document_id=%s LIMIT 1)",
            (doc,),
        )
        assert (
            conn.execute(
                "SELECT count(*) AS n FROM document_chunks WHERE section_id IS NULL"
            ).fetchone()["n"]
            > 0
        )
        sid = str(uuid4())
        conn.execute(
            """INSERT INTO document_sections
            (id,document_id,section_level,section_title,text,page_start,page_end,
             token_count,sequence_index) VALUES (%s,%s,1,'Test','Evidence',1,1,2,999999)""",
            (sid, doc),
        )
        conn.execute("SAVEPOINT fk_check")
        other = conn.execute("SELECT id FROM documents WHERE id<>%s LIMIT 1", (doc,)).fetchone()[
            "id"
        ]
        with pytest.raises(psycopg.errors.ForeignKeyViolation):
            conn.execute(
                "UPDATE document_chunks SET section_id=%s WHERE id="
                "(SELECT id FROM document_chunks WHERE document_id=%s LIMIT 1)",
                (sid, other),
            )
        conn.execute("ROLLBACK TO SAVEPOINT fk_check")
        conn.rollback()
