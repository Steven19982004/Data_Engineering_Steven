from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any


logger = logging.getLogger("search_movies")


def search_movies_by_filters(
    db_path: Path,
    title_contains: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    genres: list[str] | None = None,
    min_rating: float | None = None,
    min_votes: int | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Structured movie search using SQL filters."""
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite DB not found: {db_path}")

    clauses: list[str] = ["1=1"]
    params: list[Any] = []

    if title_contains:
        clauses.append("LOWER(title) LIKE ?")
        params.append(f"%{title_contains.lower()}%")

    if year_from is not None:
        clauses.append("release_year >= ?")
        params.append(int(year_from))

    if year_to is not None:
        clauses.append("release_year <= ?")
        params.append(int(year_to))

    if min_rating is not None:
        clauses.append("imdb_rating >= ?")
        params.append(float(min_rating))

    if min_votes is not None:
        clauses.append("vote_count >= ?")
        params.append(int(min_votes))

    for genre in genres or []:
        clauses.append("LOWER(genres) LIKE ?")
        params.append(f"%{genre.lower()}%")

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
    logger.info("search_movies_by_filters returned %s rows", len(results))
    return results
