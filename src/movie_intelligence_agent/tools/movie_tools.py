from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from movie_intelligence_agent.retrieval.rag import build_theme_summary
from movie_intelligence_agent.retrieval.vector_store import LocalVectorStore
from movie_intelligence_agent.tools.sql_tools import SQLTools


@dataclass
class MovieTools:
    db_path: Path
    vector_store: LocalVectorStore

    def find_similar_movies(self, movie_title: str, top_k: int = 5) -> list[dict[str, Any]]:
        base_doc = self._get_movie_document(movie_title)
        if not base_doc:
            return []

        query_text = " ".join([base_doc["title"], base_doc["overview"], base_doc["reviews_text"]]).strip()
        results = self.vector_store.query(query_text=query_text, top_k=top_k + 1)

        filtered = [r for r in results if r["title"].lower() != movie_title.lower()]
        return filtered[:top_k]

    def retrieve_by_question(self, question: str, top_k: int = 5) -> list[dict[str, Any]]:
        return self.vector_store.query(query_text=question, top_k=top_k)

    def summarize_common_themes(self, movie_titles: list[str]) -> dict[str, Any]:
        texts: list[str] = []
        matched_titles: list[str] = []
        for title in movie_titles:
            row = self._get_movie_document(title)
            if not row:
                continue
            matched_titles.append(row["title"])
            texts.append(" ".join([row["overview"], row["reviews_text"]]))

        if not texts:
            return {
                "matched_titles": [],
                "summary": "No matching movies were found in current dataset.",
            }

        summary = build_theme_summary(texts)
        return {"matched_titles": matched_titles, "summary": summary}

    def list_movie_titles(self) -> list[str]:
        sql = "SELECT title FROM movies ORDER BY title;"
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(sql).fetchall()
        return [r[0] for r in rows]

    def list_directors(self) -> list[str]:
        sql = "SELECT DISTINCT director FROM movies WHERE director IS NOT NULL ORDER BY director;"
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(sql).fetchall()
        return [r[0] for r in rows]

    def _get_movie_document(self, title: str) -> dict[str, str] | None:
        sql = """
            SELECT
                m.title,
                m.overview,
                COALESCE(GROUP_CONCAT(r.review_text, ' '), '') AS reviews_text
            FROM movies m
            LEFT JOIN reviews r ON m.movie_id = r.movie_id
            WHERE lower(m.title) = lower(?)
            GROUP BY m.movie_id, m.title, m.overview;
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(sql, (title,)).fetchone()

        return dict(row) if row else None
