from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "AI Policy Research Platform"
    app_env: str = "development"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"

    crawling_enabled: bool = False
    default_request_timeout_seconds: float = Field(default=30, gt=0, le=300)
    default_max_pages: int = Field(default=100, gt=0, le=10000)
    default_concurrency: int = Field(default=3, gt=0, le=20)
    user_agent: str = "AI-Policy-Research-Bot/0.1"

    database_enabled: bool = False
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_policy"
    database_pool_pre_ping: bool = False
    persistence_backend: str = "database"
    crawled_document_store_path: Path = Path("data/state/crawled_documents.json")
    attachment_download_dir: Path = Path("data/attachments")

    document_storage_dir: Path = Path("data/pdfs")
    legacy_document_storage_dir: Path = Path("data/pdf")
    vector_index_dir: Path = Path("data/vector_index")
    default_top_k: int = Field(default=6, ge=1, le=20)
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    embedding_batch_size: int = Field(default=32, ge=1, le=256)
    model_cache_dir: Path = Path("data/model_cache")
    default_embedding_dimensions: int = 384
    structure_aware_chunking: bool = True
    child_target_tokens: int = Field(default=320, ge=64)
    child_max_tokens: int = Field(default=380, ge=64)
    child_overlap_tokens: int = Field(default=50, ge=0)
    parent_target_min_tokens: int = Field(default=600, ge=1)
    parent_target_max_tokens: int = Field(default=1500, ge=64)
    use_llm_contextual_header: bool = False
    embedding_max_input_tokens: int = Field(default=512, ge=128)
    embedding_special_tokens: int = Field(default=4, ge=0)
    embedding_safety_margin: int = Field(default=16, ge=0)
    contextual_header_reserve_tokens: int = Field(default=64, ge=0)
    structure_prefix_max_tokens: int = Field(default=96, ge=16)
    child_candidate_k: int = Field(default=30, ge=1)
    child_lexical_candidate_k: int = Field(default=30, ge=0)
    hybrid_rrf_rank_constant: int = Field(default=60, ge=1)
    rag_allow_partial_answers: bool = True
    rag_claim_binding_enabled: bool = False
    rag_packing_policy: Literal["original", "per_document_backfill_v1"] = "original"
    compound_retrieval_enabled: bool = False
    controlled_retrieval_enabled: bool = False
    child_rerank_k: int = Field(default=8, ge=1)
    child_selection_strategy: Literal[
        "reranker_top_k",
        "reranker_rrf_reciprocal_rank_v1",
        "reranker_protected_rrf_backfill_v1",
    ] = "reranker_top_k"
    # Independent inspection pool for post-rerank Child selection.  This is
    # not the number of Children sent to generation; the existing child
    # rerank K, Parent K, and token budget remain the downstream limits.
    child_selection_pool_k: int = Field(default=20, ge=1)
    parent_context_k: int = Field(default=8, ge=1)
    max_parents_per_document: int = Field(default=5, ge=1)
    rag_context_window_tokens: int = Field(default=32768, ge=1024)
    rag_max_context_tokens: int = Field(default=6000, ge=128)
    rag_tokenizer_path: Path = Path("data/tokenizers/deepseek-v4/tokenizer.json")
    rag_reserved_output_tokens: int = Field(default=2048, ge=128)
    rag_prompt_safety_tokens: int = Field(default=512, ge=0)

    # Pages whose native (non-OCR) extracted text is shorter than this are
    # treated as scanned/image-only and re-read via OCR.
    ocr_min_text_chars: int = Field(default=20, ge=0)
    # Tesseract language pack(s), e.g. "eng", "chi_sim", or "eng+chi_sim".
    ocr_languages: str = "eng"
    # Explicit path to the tesseract binary. Leave unset to auto-detect via
    # PATH (Linux/Docker) or common Windows install locations.
    ocr_tesseract_cmd: str | None = None

    app_secret: str = "development-only-change-me"

    firecrawl_api_key: str | None = None
    admin_register_secret: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


DATA_DIR = BACKEND_ROOT / "data"
SETTINGS_PATH = DATA_DIR / "settings.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def resolve_backend_path(path: Path) -> Path:
    return path if path.is_absolute() else BACKEND_ROOT / path
