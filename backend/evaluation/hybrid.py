"""Small frozen-corpus BM25/RRF baseline; not a production search index."""

import math
import re
import unicodedata
from collections import Counter

BM25_K1 = 1.2
BM25_B = 0.75
RRF_CONSTANT = 60


def tokenize(text):
    """English baseline: NFKC, lowercase, alphanumerics; no stemming/stopwords."""
    return re.findall(r"[a-z0-9]+", unicodedata.normalize("NFKC", text).lower())


class BM25Index:
    def __init__(self, chunks):
        self.rows = {str(c["id"]): {"chunk_id": str(c["id"]), "text": c["text"]} for c in chunks}
        if len(self.rows) != len(chunks) or not chunks:
            raise ValueError("Expected nonempty corpus with unique chunk IDs")
        self.terms = {key: Counter(tokenize(row["text"])) for key, row in self.rows.items()}
        self.lengths = {key: sum(terms.values()) for key, terms in self.terms.items()}
        self.avg_length = sum(self.lengths.values()) / len(chunks)
        self.df = Counter(term for terms in self.terms.values() for term in terms)

    def search(self, query, limit=20):
        if limit <= 0:
            raise ValueError("limit must be positive")
        query_terms = set(tokenize(query))
        if not query_terms or not self.avg_length:
            return []
        scores = []
        for key, terms in self.terms.items():
            score = 0.0
            for term in sorted(query_terms & terms.keys()):
                frequency = terms[term]
                idf = math.log(1 + (len(self.rows) - self.df[term] + 0.5) / (self.df[term] + 0.5))
                norm = BM25_K1 * (1 - BM25_B + BM25_B * self.lengths[key] / self.avg_length)
                score += idf * frequency * (BM25_K1 + 1) / (frequency + norm)
            if score > 0:
                scores.append({**self.rows[key], "bm25_score": score})
        return sorted(scores, key=lambda row: (-row["bm25_score"], row["chunk_id"]))[:limit]


def reciprocal_rank_fusion(rankings, limit=20):
    """Equal-weight rank fusion; deduplicate within each list and across lists."""
    if limit <= 0:
        raise ValueError("limit must be positive")
    scores, rows = {}, {}
    for ranking in rankings:
        seen = set()
        for row in ranking:
            key = str(row["chunk_id"])
            if key in seen:
                continue
            seen.add(key)
            rows.setdefault(key, row)
            scores[key] = scores.get(key, 0.0) + 1 / (RRF_CONSTANT + len(seen))
    ordered = sorted(scores, key=lambda key: (-scores[key], key))[:limit]
    return [{**rows[key], "rrf_score": scores[key]} for key in ordered]
