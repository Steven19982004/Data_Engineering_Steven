from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from movie_intelligence_agent.exceptions import ToolExecutionError
from movie_intelligence_agent.logger import get_logger


@dataclass
class SQLTools:
    db_path: Path

    def __post_init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)

    def fetch_high_rated_scifi(
        self, year_from: int = 2015, min_rating: float = 7.5, limit: int = 10
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT title, release_year, director, imdb_rating, vote_count
            FROM movie_fact
            WHERE release_year >= ?
              AND genres LIKE '%Sci-Fi%'
              AND imdb_rating >= ?
            ORDER BY imdb_rating DESC, vote_count DESC
            LIMIT ?;
        """
        return self._query(sql, (year_from, min_rating, limit))

    def fetch_high_quality_thrillers(
        self, min_rating: float = 7.5, min_votes: int = 120000, limit: int = 10
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT title, release_year, director, imdb_rating, vote_count
            FROM movie_fact
            WHERE genres LIKE '%Thriller%'
              AND imdb_rating >= ?
              AND vote_count >= ?
            ORDER BY imdb_rating DESC, vote_count DESC
            LIMIT ?;
        """
        return self._query(sql, (min_rating, min_votes, limit))

    def compare_directors(self, director_a: str, director_b: str) -> list[dict[str, Any]]:
        sql = """
            SELECT
                director,
                COUNT(*) AS movie_count,
                ROUND(AVG(imdb_rating), 3) AS avg_rating,
                SUM(vote_count) AS total_votes,
                ROUND(MAX(imdb_rating), 3) AS best_rating
            FROM movie_fact
            WHERE director IN (?, ?)
            GROUP BY director
            ORDER BY avg_rating DESC;
        """
        return self._query(sql, (director_a, director_b))

    def safe_readonly_sql(self, sql: str) -> list[dict[str, Any]]:
        stripped = sql.strip().lower()
        if not stripped.startswith("select"):
            raise ToolExecutionError("Only SELECT statements are allowed in safe_readonly_sql")
        return self._query(sql, ())

    def _query(self, sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
        if not self.db_path.exists():
            raise ToolExecutionError(f"SQLite database not found: {self.db_path}")

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(sql, params).fetchall()
                return [dict(row) for row in rows]
        except Exception as exc:
            self.logger.exception("SQL tool failed")
            raise ToolExecutionError(str(exc)) from exc
