from pathlib import Path
from types import SimpleNamespace

import pytest

from app.modules.chat.rag import context_packing


def test_defaults_require_tokenizer_and_use_d_budget():
    from app.core.config import Settings

    settings = Settings(_env_file=None)
    assert settings.rag_max_context_tokens == 6000
    assert settings.parent_context_k == 8
    assert settings.max_parents_per_document == 5
    assert settings.child_selection_strategy == "reranker_top_k"
    assert settings.child_selection_pool_k == 20
    assert settings.rag_tokenizer_path == Path("data/tokenizers/deepseek-v4/tokenizer.json")


def test_configured_tokenizer_not_byte_length(monkeypatch):
    monkeypatch.setattr(
        context_packing,
        "get_settings",
        lambda: SimpleNamespace(rag_tokenizer_path=Path("tokenizer.json")),
    )

    class Tokenizer:
        def encode(self, text, *, add_special_tokens):
            assert not add_special_tokens
            return SimpleNamespace(ids=[1, 2])

    monkeypatch.setattr(context_packing, "_tokenizer", lambda path: Tokenizer())
    assert context_packing.generation_tokens("a long test sentence") == 2


def test_missing_configured_tokenizer_fails_instead_of_silent_byte_fallback(monkeypatch):
    monkeypatch.setattr(
        context_packing,
        "get_settings",
        lambda: SimpleNamespace(rag_tokenizer_path=Path("missing-test-tokenizer.json")),
    )
    with pytest.raises(FileNotFoundError):
        context_packing.generation_tokens("test")
