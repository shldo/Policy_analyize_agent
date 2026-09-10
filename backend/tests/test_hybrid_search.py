from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import pytest

from app.modules.documents import controlled_retrieval as controlled
from app.modules.documents import service
from app.modules.documents.hybrid_search import BM25Index, bm25_query, reciprocal_rank_fusion
from app.modules.documents.repositories import embeddings


@pytest.fixture
def index():
    value = BM25Index()
    yield value
    value.close()


def child(key, text="", **kwargs):
    return {"chunk_id": key, "text": text, **kwargs}


def test_bm25_term_frequency_length_and_stemming(index):
    corpus = [
        child("short", "watermark watermark"),
        child("long", "watermark " + "unrelated " * 50),
        *[child(str(i), "bank governance") for i in range(8)],
    ]
    hits = index.search("watermarks", corpus, 5)
    assert [key for key, _ in hits] == ["short", "long"]
    assert hits[0][1] > hits[1][1] > 0


@pytest.mark.parametrize("query", ["", "???", "the and of"])
def test_empty_query(index, query):
    assert index.search(query, [child("a", "policy")], 10) == []


def test_query_is_literal_and_keeps_modality():
    query = bm25_query('must NOT "watermarks" OR body:governance*')
    assert '"must"' in query and '"not"' in query
    assert ":" not in query and "*" not in query


def test_snapshot_changes_and_cache_is_bounded(index):
    assert index.search("watermark", [child("a", "watermark")], 2)
    assert not index.search("watermark", [child("a", "training")], 2)
    assert index.search("training", [child("b", "training")], 2)[0][0] == "b"
    assert len(index._indexes) == 2
    assert index.search("training", [], 2) == []
    # A smaller authorized scope cannot return a formerly accessible document.
    assert not index.search("training", [child("c", "nothing")], 2)


def test_bm25_concurrent_search(index):
    corpus = [child("a", "training"), child("b", "watermark")]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: index.search("training", corpus, 1), range(12)))
    assert all(hits[0][0] == "a" for hits in results)


def test_rrf_formula_duplicates_ties_provenance_and_real_distance():
    dense = [child("a", distance=0.1), child("b", distance=0.3)]
    lexical = [child("b", distance=0.3, bm25_score=500), child("c", distance=0.8)]
    result = reciprocal_rank_fusion({"dense": dense, "bm25": [*lexical, lexical[0]]})
    assert [c["chunk_id"] for c in result] == ["b", "a", "c"]
    assert result[0]["rrf_score"] == pytest.approx(1 / 62 + 1 / 61)
    assert result[0]["retrieval_ranks"] == {"dense": 2, "bm25": 1}
    assert result[0]["bm25_score"] == 500
    assert result[0]["distance"] == 0.3
    assert "rrf_score" not in dense[0]
    tied = reciprocal_rank_fusion({"dense": [child("z")], "bm25": [child("a")]})
    assert [c["chunk_id"] for c in tied] == ["a", "z"]
    assert reciprocal_rank_fusion({"dense": [], "bm25": []}) == []
    with pytest.raises(ValueError):
        reciprocal_rank_fusion({}, rank_constant=0)


@pytest.mark.parametrize("document_ids", [None, ["doc"]])
@pytest.mark.parametrize("restricted", [False, True])
def test_repository_authorized_corpus_before_bm25(monkeypatch, document_ids, restricted):
    rows = [dict(child("a", "watermark"), document_id="doc", page_start=1, page_end=1)]
    captured = {}

    class Connection:
        def execute(self, sql, values):
            captured.update(sql=sql, values=values)
            return self

        def fetchall(self):
            return rows

    @contextmanager
    def connection():
        yield Connection()

    monkeypatch.setattr(embeddings, "get_connection", connection)
    monkeypatch.setattr(embeddings, "_table_exists", lambda *a: True)
    monkeypatch.setattr(embeddings, "_active_table_dim", lambda: ("chunk_embeddings", 384))
    repo = embeddings.EmbeddingRepository()
    monkeypatch.setattr(repo, "original_query_distances", lambda q, ids: {"a": 0.75})
    hits = repo.retrieve_lexical(
        "watermarks", "vector", document_ids, limit=3, include_restricted=restricted
    )
    assert hits[0]["distance"] == 0.75
    assert hits[0]["bm25_score"] > 0
    assert ("d.approved = true" in captured["sql"]) == (not restricted)
    assert ("d.access_level = 'public'" in captured["sql"]) == (not restricted)
    assert ("c.document_id = ANY" in captured["sql"]) == (document_ids is not None)
    assert "LIMIT" not in captured["sql"]  # BM25 must not be limited to ANN Top-K.


def test_repository_disabled_and_empty_scope_do_not_query(monkeypatch):
    monkeypatch.setattr(embeddings, "_active_table_dim", lambda: pytest.fail("queried DB"))
    repo = embeddings.EmbeddingRepository()
    assert repo.retrieve_lexical("q", "v", [], limit=30) == []
    assert repo.retrieve_lexical("q", "v", limit=0) == []


@pytest.mark.parametrize("full_corpus", [False, True])
def test_classic_and_full_corpus_use_fused_candidates(monkeypatch, full_corpus):
    monkeypatch.setattr(service, "embed_query", lambda q: [1])
    monkeypatch.setattr(service, "vector_literal", lambda v: "vector")
    monkeypatch.setattr(service, "resolve_document_ids", lambda *a: ["doc"])
    monkeypatch.setattr(service, "reranker_enabled", lambda: False)
    dense = [child("a", distance=0.1), child("b", distance=0.2)]
    monkeypatch.setattr(service.embedding_repository, "retrieve", lambda *a, **kw: dense)
    monkeypatch.setattr(service.embedding_repository, "retrieve_all", lambda *a, **kw: dense)
    monkeypatch.setattr(
        service.embedding_repository,
        "retrieve_lexical",
        lambda *a, **kw: [child("b", distance=0.2, bm25_score=1)],
    )
    result = (
        service.search_full_corpus("q")
        if full_corpus
        else service.retrieve_relevant_chunks("q", ["doc"])
    )
    assert result[0]["chunk_id"] == "b"
    assert result[0]["retrieval_sources"] == ["dense", "bm25"]


def test_controlled_first_and_targeted_search_share_hybrid(monkeypatch):
    from app.modules.chat.rag import evidence, generation

    captured = []

    def retrieve(query, **kwargs):
        captured.append((query, kwargs))
        return [child("a", "Evidence.", distance=0.1, reranker_score=9, rrf_score=0.02)]

    def run(q, **kwargs):
        assert kwargs["retrieve"](q, q)[0]["rrf_score"] == 0.02
        assert kwargs["retrieve"]("targeted", q)[0]["distance"] == 0.2
        return [], {}

    monkeypatch.setattr(service, "retrieve_child_candidates", retrieve)
    monkeypatch.setattr(service, "_rerank_or_dense", lambda q, c, n: c)
    monkeypatch.setattr(service, "embed_query", lambda q: [1])
    monkeypatch.setattr(service, "vector_literal", lambda v: "vector")
    monkeypatch.setattr(
        service.embedding_repository, "original_query_distances", lambda q, ids: {"a": 0.2}
    )
    monkeypatch.setattr(evidence, "max_vector_distance", lambda: 1.0)
    monkeypatch.setattr(evidence, "min_reranker_score", lambda: 0)
    monkeypatch.setattr(generation, "resolve_generation_target", lambda _: ("p", "m", None))
    monkeypatch.setattr(controlled, "run_controlled", run)
    controlled.retrieve_controlled("original", document_ids=["doc"])
    assert [q for q, _ in captured] == ["original", "targeted"]
    assert all(
        args["document_ids"] == ["doc"] and not args["expand_aspects"] for _, args in captured
    )
