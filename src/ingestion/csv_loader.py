from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd


EXPECTED_COLUMNS = {
    "movie_id",
    "tmdb_id",
    "title",
    "release_date",
    "release_year",
    "director",
    "genres",
    "original_language",
    "runtime_min",
    "imdb_rating",
    "vote_count",
    "popularity",
    "overview",
}


def load_movies_csv(csv_path: Path) -> pd.DataFrame:
    """Load local movie CSV fixture into a normalized ingestion DataFrame."""
    logger = logging.getLogger("csv_loader")

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    missing = EXPECTED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {sorted(missing)}")

    out = pd.DataFrame(
        {
            "csv_movie_id": df.get("movie_id"),
            "tmdb_id": df.get("tmdb_id"),
            "title": df.get("title"),
            "release_date": df.get("release_date"),
            "release_year": df.get("release_year"),
            "director": df.get("director"),
            "genres": df.get("genres"),
            "original_language": df.get("original_language"),
            "runtime_min": df.get("runtime_min"),
            "imdb_rating": df.get("imdb_rating"),
            "vote_count": df.get("vote_count"),
            "popularity": df.get("popularity"),
            "overview": df.get("overview"),
            "tagline": df.get("tagline"),
            "review_snippet": df.get("review_snippet"),
            "source_name": "csv_fixture",
        }
    )

    logger.info("Loaded %s rows from CSV fixture: %s", len(out), csv_path)
    return out
