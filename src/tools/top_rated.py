from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any


logger = logging.getLogger("top_rated")


def get_top_rated_movies(
    db_path: Path,
    genre: str | None = None,
    year_from: int | None = None,
    min_votes: int = 100000,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Get top rated movies with optional genre/year constraints."""
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite DB not found: {db_path}")

    clauses = ["imdb_rating IS NOT NULL", "vote_count >= ?"]
    params: list[Any] = [int(min_votes)]

    if genre:
        clauses.append("LOWER(genres) LIKE ?")
        params.append(f"%{genre.lower()}%")

    if year_from is not None:
        clauses.append("release_year >= ?")
        params.append(int(year_from))

    sql = f"""
        SELECT
            movie_pk, title, release_year, director, genres,
            imdb_rating, vote_count, source_flags
        FROM movies
        WHERE {' AND '.join(clauses)}
        ORDER BY imdb_rating DESC, vote_count DESC
        LIMIT ?;
    """
    params.append(int(limit))

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()

    results = [dict(r) for r in rows]
    logger.info("get_top_rated_movies returned %s rows", len(results))
    return results
