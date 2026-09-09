import pytest

from app.core.config import Settings
from app.modules.documents.parent_child import embedding_input
from app.modules.embedding import service
from app.modules.embedding.settings import EmbeddingConfig


def test_prefix_and_header_included_in_budget():
    chunk = {"text": "body " * 60, "metadata_json": {"structure_prefix": "prefix " * 50}}
    with pytest.raises(ValueError, match="exceeds"):
        embedding_input(
            chunk,
            "header " * 40,
            settings=Settings(embedding_max_input_tokens=128),
            count=lambda t: len(t.split()),
        )


def test_provider_rejects_before_silent_truncation(monkeypatch, caplog):
    monkeypatch.setattr(service, "active_config", lambda: EmbeddingConfig())
    monkeypatch.setattr(service, "count_input_tokens", lambda _: 513)
    with pytest.raises(ValueError, match="safe model limit"):
        service.validate_inputs(["not logged"])
    assert "embedding_input_rejected" in caplog.text
    assert "not logged" not in caplog.text
