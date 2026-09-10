"""Local English BM25 and rank fusion; PostgreSQL remains the source of truth.

The bounded process-local FTS5 cache indexes an already-authorized corpus snapshot.
Its key includes every Child ID and body, so imports/reprocess/deletes cannot leave
stale results. Restarting simply rebuilds it on the next request. No sidecar service
or durable copy of restricted documents is needed.
"""

import hashlib
import json
import logging
import re
import sqlite3
from collections import OrderedDict
from threading import RLock

logger = logging.getLogger(__name__)

# Keep policy modality and negation (must/should/may/not) searchable.
_STOP_WORDS = frozenset(
    "a an and are as at be by for from in is it of on or that the this to was were "
    "what which who with".split()
)


def bm25_query(question: str) -> str:
    """Treat input as literal OR terms, never user-supplied FTS operators."""
    terms = dict.fromkeys(re.findall(r"[^\W_]+", question.casefold()))
    return " OR ".join(f'"{term}"' for term in terms if term not in _STOP_WORDS)


class BM25Index:
    """Small, thread-safe cache of genuine FTS5 BM25 inverted indexes.

    BM25 statistics are computed over the permitted search scope, not dense Top-K.
    Fetching that scope from PostgreSQL on each request favors consistency over
    large-corpus throughput. Replace this boundary with a persistent search service
    when that measured transfer becomes a bottleneck.
    """

    def __init__(self, max_snapshots: int = 2):
        if max_snapshots < 1:
            raise ValueError("max_snapshots must be positive")
        self._max_snapshots = max_snapshots
        self._indexes: OrderedDict[str, sqlite3.Connection] = OrderedDict()
        self._lock = RLock()

    def search(self, question: str, children: list[dict], limit: int) -> list[tuple[str, float]]:
        query = bm25_query(question)
        if limit <= 0 or not children or not query:
            return []
        bodies = sorted((str(c["chunk_id"]), c["text"]) for c in children)
        key = hashlib.sha256(json.dumps(bodies, ensure_ascii=False).encode()).hexdigest()
        with self._lock:
            connection = self._indexes.get(key)
            if connection is None:
                connection = sqlite3.connect(":memory:", check_same_thread=False)
                try:
                    connection.execute(
                        "CREATE VIRTUAL TABLE children USING fts5("
                        "chunk_id UNINDEXED, body, tokenize='porter unicode61')"
                    )
                    connection.executemany(
                        "INSERT INTO children(chunk_id, body) VALUES (?, ?)", bodies
                    )
                    connection.commit()
                except Exception:
                    connection.close()
                    raise
                self._indexes[key] = connection
                while len(self._indexes) > self._max_snapshots:
                    self._indexes.popitem(last=False)[1].close()
                logger.info("BM25 index built children=%d snapshot=%s", len(bodies), key[:12])
            self._indexes.move_to_end(key)
            # SQLite returns NEGATIVE BM25: ascending is best. Expose positive
            # relevance for diagnostics only; RRF uses rank, not these magnitudes.
            rows = connection.execute(
                "SELECT chunk_id, bm25(children) AS score FROM children "
                "WHERE children MATCH ? ORDER BY score, chunk_id LIMIT ?",
                (query, limit),
            ).fetchall()
            return [(chunk_id, -float(score)) for chunk_id, score in rows]

    def close(self) -> None:
        with self._lock:
            for connection in self._indexes.values():
                connection.close()
            self._indexes.clear()


def reciprocal_rank_fusion(
    rankings: dict[str, list[dict]], *, rank_constant: int = 60
) -> list[dict]:
    """Equal-weight RRF, one-based ranks, one contribution per source/Child.

    Never overwrite cosine distance or reranker_score with an RRF score. Original
    evidence thresholds continue to operate in their original score spaces.
    """
    if rank_constant < 1:
        raise ValueError("rank_constant must be positive")
    merged: dict[str, dict] = {}
    for source, children in rankings.items():
        seen = set()
        for child in children:
            key = child["chunk_id"]
            if key in seen:
                continue
            seen.add(key)
            rank = len(seen)
            if key not in merged:
                merged[key] = dict(child, retrieval_sources=[], retrieval_ranks={}, rrf_score=0.0)
            item = merged[key]
            item["retrieval_sources"].append(source)
            item["retrieval_ranks"][source] = rank
            item["rrf_score"] += 1.0 / (rank_constant + rank)
            if source == "bm25":
                for field in ("bm25_score", "lexical_score"):
                    if field in child:
                        item[field] = child[field]
    return sorted(merged.values(), key=lambda c: (-c["rrf_score"], str(c["chunk_id"])))


bm25_index = BM25Index()
