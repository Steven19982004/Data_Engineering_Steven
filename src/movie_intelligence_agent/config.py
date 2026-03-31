from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def _resolve_path(value: str, root_dir: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root_dir / path


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    root_dir: Path
    sqlite_path: Path
    vector_store_dir: Path
    log_path: Path
    raw_data_dir: Path
    processed_data_dir: Path
    eval_data_path: Path
    output_dir: Path
    default_top_k: int
    thriller_min_votes: int

    openai_api_key: str
    openai_model: str

    enable_omdb_enrichment: bool
    omdb_api_key: str

    @classmethod
    def from_env(cls) -> "Settings":
        root_dir = ROOT_DIR
        sqlite_path = _resolve_path(os.getenv("SQLITE_PATH", "storage/movie_agent.db"), root_dir)
        vector_store_dir = _resolve_path(
            os.getenv("VECTOR_STORE_DIR", "storage/vector_store"), root_dir
        )
        log_path = _resolve_path(os.getenv("LOG_PATH", "logs/app.log"), root_dir)

        raw_data_dir = root_dir / "data" / "raw"
        processed_data_dir = root_dir / "data" / "processed"
        eval_data_path = root_dir / "data" / "eval" / "eval_cases.json"
        output_dir = root_dir / "output"

        return cls(
            root_dir=root_dir,
            sqlite_path=sqlite_path,
            vector_store_dir=vector_store_dir,
            log_path=log_path,
            raw_data_dir=raw_data_dir,
            processed_data_dir=processed_data_dir,
            eval_data_path=eval_data_path,
            output_dir=output_dir,
            default_top_k=int(os.getenv("DEFAULT_TOP_K", "5")),
            thriller_min_votes=int(os.getenv("THRILLER_MIN_VOTES", "120000")),
            openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            enable_omdb_enrichment=_to_bool(os.getenv("ENABLE_OMDB_ENRICHMENT", "false")),
            omdb_api_key=os.getenv("OMDB_API_KEY", "").strip(),
        )

    def ensure_directories(self) -> None:
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
