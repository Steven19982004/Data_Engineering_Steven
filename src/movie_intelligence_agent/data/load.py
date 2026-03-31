from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from movie_intelligence_agent.logger import get_logger


@dataclass
class SQLiteLoader:
    db_path: Path

    def __post_init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def load_all(self, movies_df: pd.DataFrame, reviews_df: pd.DataFrame) -> None:
        with sqlite3.connect(self.db_path) as conn:
            self._init_schema(conn)
            self._load_movies(conn, movies_df)
            self._load_ratings(conn, movies_df)
            self._load_reviews(conn, reviews_df)
            self._create_views(conn)
            conn.commit()

        self.logger.info("SQLite load complete: %s", self.db_path)

    def _init_schema(self, conn: sqlite3.Connection) -> None:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(
            """
            DROP VIEW IF EXISTS movie_fact;
            DROP TABLE IF EXISTS reviews;
            DROP TABLE IF EXISTS ratings;
            DROP TABLE IF EXISTS movies;

            CREATE TABLE movies (
                movie_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                normalized_title TEXT NOT NULL,
                release_year INTEGER NOT NULL,
                director TEXT,
                genres TEXT,
                runtime_min INTEGER,
                language TEXT,
                overview TEXT,
                awards TEXT,
                box_office TEXT,
                country TEXT,
                enrichment_source TEXT
            );

            CREATE TABLE ratings (
                movie_id TEXT PRIMARY KEY,
                imdb_rating REAL,
                vote_count INTEGER,
                metascore REAL,
                last_updated TEXT,
                FOREIGN KEY(movie_id) REFERENCES movies(movie_id)
            );

            CREATE TABLE reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                movie_id TEXT NOT NULL,
                movie_title TEXT NOT NULL,
                review_text TEXT NOT NULL,
                sentiment TEXT,
                source TEXT,
                FOREIGN KEY(movie_id) REFERENCES movies(movie_id)
            );
            """
        )

    def _load_movies(self, conn: sqlite3.Connection, movies_df: pd.DataFrame) -> None:
        movies_cols = [
            "movie_id",
            "title",
            "normalized_title",
            "release_year",
            "director",
            "genres",
            "runtime_min",
            "language",
            "overview",
            "awards",
            "box_office",
            "country",
            "enrichment_source",
        ]
        movies_df[movies_cols].to_sql("movies", conn, if_exists="append", index=False)

    def _load_ratings(self, conn: sqlite3.Connection, movies_df: pd.DataFrame) -> None:
        ratings_cols = ["movie_id", "imdb_rating", "vote_count", "metascore", "last_updated"]
        movies_df[ratings_cols].to_sql("ratings", conn, if_exists="append", index=False)

    def _load_reviews(self, conn: sqlite3.Connection, reviews_df: pd.DataFrame) -> None:
        payload = reviews_df[["movie_id", "movie_title", "review_text", "sentiment", "source"]].copy()
        payload.to_sql("reviews", conn, if_exists="append", index=False)

    def _create_views(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE VIEW movie_fact AS
            SELECT
                m.movie_id,
                m.title,
                m.release_year,
                m.director,
                m.genres,
                m.runtime_min,
                m.language,
                m.overview,
                m.awards,
                m.box_office,
                m.country,
                m.enrichment_source,
                r.imdb_rating,
                r.vote_count,
                r.metascore,
                r.last_updated
            FROM movies m
            LEFT JOIN ratings r ON m.movie_id = r.movie_id;
            """
        )
