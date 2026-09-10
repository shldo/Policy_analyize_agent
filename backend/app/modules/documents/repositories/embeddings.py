"""Chunk text + per-model vector storage and similarity search.

Chunk TEXT lives once in `document_chunks` (model-independent). VECTORS live in
one table PER embedding model — the active model's table is resolved from
embedding config. Consequences:
  - Switching model = read a different table. Each model keeps its own vectors,
    so switching back is instant and needs no re-embed.
  - A new model's table is created on demand (ensure_vector_table).
  - The default local model maps to the pre-existing `chunk_embeddings` table
    (LEGACY_VECTOR_TABLE) so existing data is reused, not re-embedded.

Re-embedding a model reuses existing chunks (no re-chunk), so it never disturbs
other models' vectors.
"""

import json
from uuid import uuid4

from app.core.database import get_connection
from app.modules.embedding import service as embedding
from app.modules.embedding.settings import LEGACY_VECTOR_TABLE


def _active_table_dim() -> tuple[str, int]:
    return embedding.active_vector_table(), embedding.active_dimension()


def _table_exists(connection, table: str) -> bool:
    row = connection.execute("SELECT to_regclass(%s) AS t", (f"public.{table}",)).fetchone()
    return bool(row and row["t"])


# pgvector's hnsw index caps the `vector` type at 2000 dims and `halfvec` at
# 4000. So: <=2000 -> vector; 2001..4000 -> halfvec (16-bit, indexable, retrieval
# quality effectively unchanged); >4000 -> halfvec column but NO ANN index (falls
# back to an exact brute-force scan — fine for small corpora, rare in practice
# since most models let you request <=4000 dims). The `<=>` cosine operator and
# the literal format are identical across types; only the type name / index ops
# class differ.
HNSW_VECTOR_DIM_LIMIT = 2000
HNSW_HALFVEC_DIM_LIMIT = 4000


def _vector_type(dim: int) -> str:
    return "halfvec" if dim > HNSW_VECTOR_DIM_LIMIT else "vector"


def _hnsw_ops(dim: int) -> str:
    return "halfvec_cosine_ops" if dim > HNSW_VECTOR_DIM_LIMIT else "vector_cosine_ops"


def ensure_vector_table(connection, table: str, dim: int) -> None:
    """Create a model's vector table + HNSW index if missing (idempotent).

    The legacy table already exists in the base schema (with its own index), so
    it is left untouched to avoid a duplicate index.
    """
    if table == LEGACY_VECTOR_TABLE:
        return
    connection.execute(
        f'''
        CREATE TABLE IF NOT EXISTS "{table}" (
            chunk_id uuid PRIMARY KEY REFERENCES document_chunks (id) ON DELETE CASCADE,
            embedding {_vector_type(dim)}({dim}) NOT NULL,
            embedding_model text NOT NULL
        )
        '''
    )
    if dim <= HNSW_HALFVEC_DIM_LIMIT:
        connection.execute(
            f'CREATE INDEX IF NOT EXISTS "{table}_hnsw" '
            f'ON "{table}" USING hnsw (embedding {_hnsw_ops(dim)})'
        )
    # dim > 4000: no ANN index (exceeds halfvec hnsw limit) -> exact brute-force scan.


class EmbeddingRepository:
    """Persistence and similarity search for document chunks and embeddings."""

    def require_structure_schema(self) -> None:
        with get_connection() as connection:
            if not _table_exists(connection, "document_sections"):
                raise ValueError("Apply migration 019 before structure-aware full reprocessing.")

    def structure_status(self, document_id: str) -> dict:
        with get_connection() as connection:
            row = connection.execute(
                """SELECT count(*) AS total,
                    count(*) FILTER (WHERE to_jsonb(c)->>'section_id' IS NOT NULL) AS structured
                    FROM document_chunks c WHERE document_id=%s""",
                (document_id,),
            ).fetchone()
            schema_ready = _table_exists(connection, "document_sections")
        return {
            "schema_ready": schema_ready,
            "children": row["total"],
            "structured_children": row["structured"],
            "requires_full_reprocess": row["total"] == 0 or row["structured"] < row["total"],
            "reembed_creates_sections": False,
        }

    def replace_document_chunks(
        self,
        document_id: str,
        chunks: list[dict],
        embeddings: list[str],
        *,
        language: str | None,
        sections: list[dict] | None = None,
    ) -> None:
        """Full (re)ingest: replace chunk text and write the active model's vectors.

        Deleting document_chunks cascades away this doc's rows in EVERY model's
        vector table, which is correct here — the content was re-chunked so old
        vectors (of any model) no longer match.
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Each chunk must have exactly one embedding.")
        table, dim = _active_table_dim()
        model_id = embedding.active_model_id()
        with get_connection() as connection:
            connection.execute("DELETE FROM document_chunks WHERE document_id = %s", (document_id,))
            if _table_exists(connection, "document_sections"):
                connection.execute(
                    "DELETE FROM document_sections WHERE document_id = %s", (document_id,)
                )
            if sections:
                for section in sections:
                    connection.execute(
                        """INSERT INTO document_sections (
                            id, document_id, parent_section_id, section_level, section_number,
                            section_title, section_path, text, page_start, page_end,
                            token_count, sequence_index, metadata_json
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s::jsonb)""",
                        (
                            section["id"],
                            document_id,
                            section["parent_section_id"],
                            section["section_level"],
                            section["section_number"],
                            section["section_title"],
                            json.dumps(section["section_path"]),
                            section["text"],
                            section["page_start"],
                            section["page_end"],
                            section["token_count"],
                            section["sequence_index"],
                            json.dumps(section["metadata_json"]),
                        ),
                    )
            ensure_vector_table(connection, table, dim)
            for chunk, embedding_literal in zip(chunks, embeddings, strict=True):
                chunk_id = str(uuid4())
                connection.execute(
                    """
                    INSERT INTO document_chunks (
                        id, document_id, chunk_index, page_start, page_end,
                        section_title, language, text, token_count, metadata_json
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    (
                        chunk_id,
                        document_id,
                        chunk["chunk_index"],
                        chunk["page_start"],
                        chunk["page_end"],
                        chunk["section_title"],
                        chunk.get("language", language),
                        chunk["text"],
                        chunk["token_count"],
                        json.dumps(chunk.get("metadata_json") or {}),
                    ),
                )
                connection.execute(
                    f'INSERT INTO "{table}" (chunk_id, embedding, embedding_model) '
                    f"VALUES (%s, %s::{_vector_type(dim)}, %s)",
                    (chunk_id, embedding_literal, model_id),
                )
                if chunk.get("section_id"):
                    connection.execute(
                        "UPDATE document_chunks SET section_id=%s, child_index=%s WHERE id=%s",
                        (chunk["section_id"], chunk["child_index"], chunk_id),
                    )
            connection.commit()

    def chunks_for_reembed(self, document_id: str) -> list[dict]:
        """Existing chunks (id + text + stored context header) for re-embedding."""
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, text, metadata_json
                FROM document_chunks WHERE document_id = %s ORDER BY chunk_index
                """,
                (document_id,),
            ).fetchall()
        return [
            {
                "chunk_id": str(row["id"]),
                "text": row["text"],
                "context_header": (row["metadata_json"] or {}).get("context_header"),
                "metadata_json": row["metadata_json"] or {},
            }
            for row in rows
        ]

    def store_vectors(self, chunk_ids: list[str], embeddings: list[str]) -> None:
        """Write vectors for existing chunks into the active model's table.

        Used by re-embed: does not touch document_chunks, so other models' tables
        are untouched. Replaces any existing rows for these chunks in this table.
        """
        if not chunk_ids:
            return
        table, dim = _active_table_dim()
        model_id = embedding.active_model_id()
        with get_connection() as connection:
            ensure_vector_table(connection, table, dim)
            connection.execute(
                f'DELETE FROM "{table}" WHERE chunk_id = ANY(%s::uuid[])', (chunk_ids,)
            )
            for chunk_id, embedding_literal in zip(chunk_ids, embeddings, strict=True):
                connection.execute(
                    f'INSERT INTO "{table}" (chunk_id, embedding, embedding_model) '
                    f"VALUES (%s, %s::{_vector_type(dim)}, %s)",
                    (chunk_id, embedding_literal, model_id),
                )
            connection.commit()

    def list_for_document(self, document_id: str, limit: int | None = None) -> list[dict]:
        table, _ = _active_table_dim()
        limit_sql = "LIMIT %s" if limit is not None else ""
        values: list[object] = [document_id]
        if limit is not None:
            values.append(limit)
        with get_connection() as connection:
            has_table = _table_exists(connection, table)
            join_sql = f'LEFT JOIN "{table}" e ON e.chunk_id = c.id' if has_table else ""
            model_col = "e.embedding_model" if has_table else "NULL AS embedding_model"
            rows = connection.execute(
                f"""
                SELECT c.*, {model_col}
                FROM document_chunks c
                {join_sql}
                WHERE c.document_id = %s ORDER BY c.chunk_index {limit_sql}
                """,
                tuple(values),
            ).fetchall()
        return [dict(row) for row in rows]

    def has_embeddings(self, document_ids: list[str]) -> bool:
        """True when the ACTIVE model has at least one vector for these documents."""
        if not document_ids:
            return False
        table, _ = _active_table_dim()
        with get_connection() as connection:
            if not _table_exists(connection, table):
                return False
            row = connection.execute(
                f"""
                SELECT EXISTS(
                    SELECT 1 FROM "{table}" e
                    JOIN document_chunks c ON c.id = e.chunk_id
                    WHERE c.document_id = ANY(%s::uuid[])
                ) AS exists
                """,
                (document_ids,),
            ).fetchone()
        return bool(row["exists"]) if row else False

    def retrieve_all(
        self, query_vector: str, *, limit: int, include_restricted: bool = False
    ) -> list[dict]:
        """Corpus-wide nearest-neighbour search, not scoped to a document_ids set.

        Used by the agent's search_full_corpus tool. Restricted documents are
        excluded unless include_restricted (mirrors the visibility rule in
        documents.repositories.documents._filters).
        """
        table, dim = _active_table_dim()
        cast = _vector_type(dim)
        visibility_sql = (
            "" if include_restricted else "WHERE d.approved = true AND d.access_level = 'public'"
        )
        with get_connection() as connection:
            if not _table_exists(connection, table):
                return []
            rows = connection.execute(
                f"""
                SELECT c.id AS chunk_id, c.document_id,
                    d.original_filename AS file,
                    COALESCE(dm.title, d.original_filename) AS doc_title,
                    c.page_start, c.page_end,
                    c.text, c.token_count, c.language, c.section_title,
                    to_jsonb(c)->>'section_id' AS section_id,
                    c.metadata_json->'section_path' AS section_path,
                    e.embedding <=> %s::{cast} AS distance
                FROM "{table}" e
                JOIN document_chunks c ON c.id = e.chunk_id
                JOIN documents d ON d.id = c.document_id
                LEFT JOIN document_metadata dm ON dm.document_id = d.id
                {visibility_sql}
                ORDER BY e.embedding <=> %s::{cast} LIMIT %s
                """,
                (query_vector, query_vector, limit),
            ).fetchall()
        return [
            {
                **dict(row),
                "chunk_id": str(row["chunk_id"]),
                "document_id": str(row["document_id"]),
                "page": row["page_start"],
                "distance": float(row["distance"]),
            }
            for row in rows
        ]

    def retrieve(self, query_vector: str, document_ids: list[str], *, limit: int) -> list[dict]:
        if not document_ids:
            return []
        table, dim = _active_table_dim()
        cast = _vector_type(dim)
        with get_connection() as connection:
            if not _table_exists(connection, table):
                return []  # active model not embedded yet -> caller falls back to pages
            rows = connection.execute(
                f"""
                SELECT c.id AS chunk_id, c.document_id,
                    d.original_filename AS file,
                    COALESCE(dm.title, d.original_filename) AS doc_title,
                    c.page_start, c.page_end,
                    c.text, c.token_count, c.language, c.section_title,
                    to_jsonb(c)->>'section_id' AS section_id,
                    c.metadata_json->'section_path' AS section_path,
                    e.embedding <=> %s::{cast} AS distance
                FROM "{table}" e
                JOIN document_chunks c ON c.id = e.chunk_id
                JOIN documents d ON d.id = c.document_id
                LEFT JOIN document_metadata dm ON dm.document_id = d.id
                WHERE c.document_id = ANY(%s::uuid[])
                ORDER BY e.embedding <=> %s::{cast} LIMIT %s
                """,
                (query_vector, document_ids, query_vector, limit),
            ).fetchall()
        return [
            {
                **dict(row),
                "chunk_id": str(row["chunk_id"]),
                "document_id": str(row["document_id"]),
                "page": row["page_start"],
                "distance": float(row["distance"]),
            }
            for row in rows
        ]

    def original_query_distances(self, query_vector: str, chunk_ids: list[str]) -> dict:
        table, dim = _active_table_dim()
        if not chunk_ids:
            return {}
        with get_connection() as connection:
            rows = connection.execute(
                f"SELECT chunk_id, embedding <=> %s::{_vector_type(dim)} AS distance "
                f'FROM "{table}" WHERE chunk_id = ANY(%s::uuid[])',
                (query_vector, chunk_ids),
            ).fetchall()
        return {str(r["chunk_id"]): float(r["distance"]) for r in rows}

    def retrieve_lexical(
        self,
        question: str,
        query_vector: str,
        document_ids: list[str] | None = None,
        *,
        limit: int,
        include_restricted: bool = False,
    ) -> list[dict]:
        """BM25 over authorized Child bodies, independently of ANN candidates.

        Keep this entry point for callers using the lexical branch. PostgreSQL
        supplies a fresh scope snapshot; the local inverted index is disposable.
        """
        from app.modules.documents.hybrid_search import bm25_index, bm25_query

        if limit <= 0 or document_ids == [] or not bm25_query(question):
            return []
        table, _ = _active_table_dim()
        filters = []
        values = []
        if document_ids is not None:
            filters.append("c.document_id = ANY(%s::uuid[])")
            values.append(document_ids)
        if not include_restricted:
            filters.append("d.approved = true AND d.access_level = 'public'")
        where = "WHERE " + " AND ".join(filters) if filters else ""
        with get_connection() as connection:
            if not _table_exists(connection, table):
                return []
            rows = connection.execute(
                f"""SELECT c.id AS chunk_id, c.document_id, d.original_filename AS file,
                    COALESCE(dm.title, d.original_filename) AS doc_title,
                    c.page_start, c.page_end, c.text, c.section_title,
                    to_jsonb(c)->>'section_id' AS section_id,
                    c.metadata_json->'section_path' AS section_path
                FROM "{table}" e
                JOIN document_chunks c ON c.id=e.chunk_id
                JOIN documents d ON d.id=c.document_id
                LEFT JOIN document_metadata dm ON dm.document_id=d.id
                {where}
                ORDER BY c.id""",
                tuple(values),
            ).fetchall()
        by_id = {str(row["chunk_id"]): row for row in rows}
        hits = bm25_index.search(question, rows, limit)
        distances = self.original_query_distances(query_vector, [key for key, _ in hits])
        return [
            dict(
                by_id[key],
                chunk_id=key,
                document_id=str(by_id[key]["document_id"]),
                page=by_id[key]["page_start"],
                distance=distances[key],
                bm25_score=score,
                lexical_score=score,  # Compatibility metadata; now explicitly BM25.
            )
            for key, score in hits
            if key in distances  # Reprocessing may remove a Child after the snapshot.
        ]

    def retrieve_many(
        self,
        query_vectors: list[str],
        document_ids: list[str],
        *,
        limit: int,
    ) -> list[list[dict]]:
        """Retrieve a per-query top-k in one PostgreSQL round trip.

        The outer result preserves the input query order. Each inner list is
        independently distance-ranked and filtered to the same selected documents.
        """
        if not query_vectors:
            return []
        if not document_ids:
            return [[] for _ in query_vectors]
        if limit <= 0:
            raise ValueError("Retrieval limit must be greater than zero.")

        table, dim = _active_table_dim()
        cast = _vector_type(dim)
        values_sql = ", ".join(
            f"({query_index}, %s::{cast})" for query_index in range(len(query_vectors))
        )
        with get_connection() as connection:
            if not _table_exists(connection, table):
                return [[] for _ in query_vectors]
            rows = connection.execute(
                f"""
                WITH query_vectors(query_index, embedding) AS (
                    VALUES {values_sql}
                )
                SELECT q.query_index, matched.*
                FROM query_vectors q
                CROSS JOIN LATERAL (
                    SELECT c.id AS chunk_id, c.document_id,
                        d.original_filename AS file,
                        COALESCE(dm.title, d.original_filename) AS doc_title,
                        c.page_start, c.page_end,
                        c.text, c.token_count, c.language, c.section_title,
                        to_jsonb(c)->>'section_id' AS section_id,
                        c.metadata_json->'section_path' AS section_path,
                        e.embedding <=> q.embedding AS distance
                    FROM "{table}" e
                    JOIN document_chunks c ON c.id = e.chunk_id
                    JOIN documents d ON d.id = c.document_id
                    LEFT JOIN document_metadata dm ON dm.document_id = d.id
                    WHERE c.document_id = ANY(%s::uuid[])
                    ORDER BY e.embedding <=> q.embedding
                    LIMIT %s
                ) matched
                ORDER BY q.query_index, matched.distance
                """,
                (*query_vectors, document_ids, limit),
            ).fetchall()

        grouped: list[list[dict]] = [[] for _ in query_vectors]
        for row in rows:
            item = dict(row)
            query_index = int(item.pop("query_index"))
            item["chunk_id"] = str(item["chunk_id"])
            item["document_id"] = str(item["document_id"])
            item["page"] = item["page_start"]
            item["distance"] = float(item["distance"])
            grouped[query_index].append(item)
        return grouped


embedding_repository = EmbeddingRepository()
