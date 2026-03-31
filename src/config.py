from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _resolve_path(value: str, root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (root / path)


@dataclass(frozen=True)
class Settings:
    app_env: str
    log_level: str
    log_path: Path

    openai_api_key: str
    tmdb_api_key: str

    use_real_llm: bool
    llm_provider: str
    llm_model: str

    enable_tmdb_api: bool
    fixture_movies_csv: Path
    fixture_tmdb_json: Path

    sqlite_path: Path
    vector_db_backend: str
    vector_db_path: Path

    embedding_model: str
    default_top_k: int

    min_vote_count: int
    high_rating_threshold: float
    year_filter_default: int

    @classmethod
    def from_env(cls) -> "Settings":
        root = PROJECT_ROOT
        return cls(
            app_env=os.getenv("APP_ENV", "dev"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_path=_resolve_path(os.getenv("LOG_PATH", "logs/app.log"), root),
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            tmdb_api_key=os.getenv("TMDB_API_KEY", "").strip(),
            use_real_llm=_to_bool(os.getenv("USE_REAL_LLM", "false")),
            llm_provider=os.getenv("LLM_PROVIDER", "openai"),
            llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            enable_tmdb_api=_to_bool(os.getenv("ENABLE_TMDB_API", "false")),
            fixture_movies_csv=_resolve_path(
                os.getenv("FIXTURE_MOVIES_CSV", "data/fixtures/sample_movies.csv"), root
            ),
            fixture_tmdb_json=_resolve_path(
                os.getenv("FIXTURE_TMDB_JSON", "data/fixtures/tmdb_sample_movies.json"), root
            ),
            sqlite_path=_resolve_path(os.getenv("SQLITE_PATH", "storage/movie_agent.db"), root),
            vector_db_backend=os.getenv("VECTOR_DB_BACKEND", "chroma"),
            vector_db_path=_resolve_path(os.getenv("VECTOR_DB_PATH", "storage/chroma_db"), root),
            embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            default_top_k=int(os.getenv("DEFAULT_TOP_K", "5")),
            min_vote_count=int(os.getenv("MIN_VOTE_COUNT", "100000")),
            high_rating_threshold=float(os.getenv("HIGH_RATING_THRESHOLD", "7.5")),
            year_filter_default=int(os.getenv("YEAR_FILTER_DEFAULT", "2015")),
        )

    def ensure_dirs(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
