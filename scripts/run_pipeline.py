from __future__ import annotations

import json
import logging
import shutil
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import Settings  # noqa: E402
from ingestion.ingest_pipeline import IngestPipeline  # noqa: E402
from processing.build_documents import build_movie_documents  # noqa: E402
from processing.clean_movies import clean_movies  # noqa: E402
from processing.merge_sources import merge_movie_sources  # noqa: E402
from processing.validate_schema import (  # noqa: E402
    validate_documents_schema,
    validate_movies_schema,
)
from retrieval.retriever import MovieSemanticRetriever  # noqa: E402
from storage.db import SQLiteDB  # noqa: E402
from storage.repository import MovieRepository  # noqa: E402


def configure_logging(log_path: Path, level: str = "INFO") -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )


def ensure_seeded_raw_files(settings: Settings) -> tuple[Path, Path]:
    raw_dir = ROOT_DIR / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    csv_dst = raw_dir / "movies_from_csv.csv"
    tmdb_dst = raw_dir / "movies_from_tmdb_fixture.json"

    if not csv_dst.exists():
        shutil.copy2(settings.fixture_movies_csv, csv_dst)
    if not tmdb_dst.exists():
        shutil.copy2(settings.fixture_tmdb_json, tmdb_dst)

    return csv_dst, tmdb_dst


def save_processed_outputs(
    csv_ingested,
    tmdb_ingested,
    csv_clean,
    tmdb_clean,
    merged,
    docs,
) -> None:
    processed_dir = ROOT_DIR / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    csv_ingested.to_csv(processed_dir / "01_ingested_csv.csv", index=False)
    tmdb_ingested.to_csv(processed_dir / "02_ingested_tmdb.csv", index=False)
    csv_clean.to_csv(processed_dir / "03_cleaned_csv.csv", index=False)
    tmdb_clean.to_csv(processed_dir / "04_cleaned_tmdb.csv", index=False)
    merged.to_csv(processed_dir / "05_merged_movies.csv", index=False)
    docs.to_csv(processed_dir / "06_movie_documents.csv", index=False)


def main() -> None:
    settings = Settings.from_env()
    settings.ensure_dirs()

    configure_logging(settings.log_path, settings.log_level)
    logger = logging.getLogger("run_pipeline")

    try:
        csv_path, tmdb_path = ensure_seeded_raw_files(settings)
        logger.info("Using raw CSV: %s", csv_path)
        logger.info("Using TMDB source file: %s", tmdb_path)

        # 1) ingest
        ingest_pipeline = IngestPipeline(settings)
        ingested = ingest_pipeline.run(csv_path=csv_path, tmdb_fixture_path=tmdb_path)

        # 2) clean
        csv_clean = clean_movies(ingested.csv_movies, source_label="csv")
        tmdb_clean = clean_movies(ingested.tmdb_movies, source_label="tmdb")

        # 3) merge
        merged_movies = merge_movie_sources(csv_clean, tmdb_clean)
        validate_movies_schema(merged_movies, stage="post-merge")

        # 4) build embedding documents
        documents = build_movie_documents(merged_movies)
        validate_documents_schema(documents, stage="post-document-build")

        # 5) write processed files
        save_processed_outputs(
            csv_ingested=ingested.csv_movies,
            tmdb_ingested=ingested.tmdb_movies,
            csv_clean=csv_clean,
            tmdb_clean=tmdb_clean,
            merged=merged_movies,
            docs=documents,
        )

        # 6) load sqlite
        db = SQLiteDB(settings.sqlite_path)
        db.create_tables()
        repo = MovieRepository(db)
        repo.upsert_movies(merged_movies)
        repo.upsert_movie_documents(documents)
        counts = repo.get_counts()

        # 7) initialize local vector index (with dependency-safe fallback backend)
        retriever = MovieSemanticRetriever(settings)
        vector_status = retriever.build_or_refresh_index(force_rebuild=True)

        summary = {
            "status": "ok",
            "rows": {
                "ingested_csv": int(len(ingested.csv_movies)),
                "ingested_tmdb": int(len(ingested.tmdb_movies)),
                "clean_csv": int(len(csv_clean)),
                "clean_tmdb": int(len(tmdb_clean)),
                "merged_movies": int(len(merged_movies)),
                "documents": int(len(documents)),
            },
            "sqlite_counts": counts,
            "vector_index": vector_status,
            "paths": {
                "sqlite": str(settings.sqlite_path),
                "processed_dir": str(ROOT_DIR / "data" / "processed"),
                "log": str(settings.log_path),
            },
        }

        print(json.dumps(summary, ensure_ascii=False, indent=2))
        logger.info("Pipeline finished successfully")
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        raise


if __name__ == "__main__":
    main()
