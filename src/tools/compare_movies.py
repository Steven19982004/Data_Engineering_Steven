from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any


logger = logging.getLogger("compare_movies")


def compare_movies_or_directors(
    db_path: Path,
    movie_titles: list[str] | None = None,
    directors: list[str] | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
) -> dict[str, Any]:
    """
    Compare either movie-level facts or director-level aggregated performance.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite DB not found: {db_path}")

    movie_titles = [t for t in (movie_titles or []) if str(t).strip()]
    directors = [d for d in (directors or []) if str(d).strip()]

    if not movie_titles and not directors:
        return {"mode": "empty", "results": []}

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        output: dict[str, Any] = {"mode": "", "results": {}}

        if directors:
            placeholders = ", ".join(["?"] * len(directors))
            extra_clauses: list[str] = []
            extra_params: list[Any] = []
            if year_from is not None:
                extra_clauses.append("release_year >= ?")
                extra_params.append(int(year_from))
            if year_to is not None:
                extra_clauses.append("release_year <= ?")
                extra_params.append(int(year_to))

            where_suffix = ""
            if extra_clauses:
                where_suffix = " AND " + " AND ".join(extra_clauses)
            sql = f"""
                SELECT
                    director,
                    COUNT(*) AS movie_count,
                    ROUND(AVG(imdb_rating), 3) AS avg_rating,
                    ROUND(MAX(imdb_rating), 3) AS best_rating,
                    SUM(vote_count) AS total_votes
                FROM movies
                WHERE LOWER(director) IN ({placeholders}) {where_suffix}
                GROUP BY director
                ORDER BY avg_rating DESC;
            """
            params = [d.lower() for d in directors] + extra_params
            rows = conn.execute(sql, params).fetchall()
            output["results"]["director_comparison"] = [dict(r) for r in rows]

        if movie_titles:
            placeholders = " OR ".join(["LOWER(title)=?" for _ in movie_titles])
            extra_clauses: list[str] = []
            extra_params: list[Any] = []
            if year_from is not None:
                extra_clauses.append("release_year >= ?")
                extra_params.append(int(year_from))
            if year_to is not None:
                extra_clauses.append("release_year <= ?")
                extra_params.append(int(year_to))

            where_suffix = ""
            if extra_clauses:
                where_suffix = " AND " + " AND ".join(extra_clauses)
            sql = f"""
                SELECT
                    movie_pk, title, release_year, director,
                    genres, imdb_rating, vote_count, source_flags
                FROM movies
                WHERE ({placeholders}) {where_suffix}
                ORDER BY imdb_rating DESC, vote_count DESC;
            """
            params = [title.lower() for title in movie_titles] + extra_params
            rows = conn.execute(sql, params).fetchall()
            output["results"]["movie_comparison"] = [dict(r) for r in rows]

    if directors and movie_titles:
        output["mode"] = "mixed"
    elif directors:
        output["mode"] = "director"
    else:
        output["mode"] = "movie"

    logger.info("compare_movies_or_directors mode=%s", output["mode"])
    return output
