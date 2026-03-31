from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SQLiteDB:
    db_path: Path

    def __post_init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def create_tables(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                PRAGMA foreign_keys = OFF;

                DROP VIEW IF EXISTS movie_fact;
                DROP TABLE IF EXISTS reviews;
                DROP TABLE IF EXISTS ratings;
                DROP TABLE IF EXISTS movie_documents;
                DROP TABLE IF EXISTS movies;

                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS movies (
                    movie_pk TEXT PRIMARY KEY,
                    csv_movie_id TEXT,
                    tmdb_id INTEGER,
                    title TEXT NOT NULL,
                    normalized_title TEXT NOT NULL,
                    release_date TEXT,
                    release_year INTEGER NOT NULL,
                    director TEXT,
                    genres TEXT,
                    original_language TEXT,
                    runtime_min INTEGER,
                    imdb_rating REAL,
                    vote_count INTEGER,
                    popularity REAL,
                    overview TEXT,
                    tagline TEXT,
                    review_snippet TEXT,
                    source_flags TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS movie_documents (
                    doc_id TEXT PRIMARY KEY,
                    movie_pk TEXT NOT NULL,
                    title TEXT NOT NULL,
                    document_text TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(movie_pk) REFERENCES movies(movie_pk) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_movies_title_year
                    ON movies(normalized_title, release_year);

                CREATE INDEX IF NOT EXISTS idx_movie_docs_movie_pk
                    ON movie_documents(movie_pk);
                """
            )
        self.logger.info("SQLite schema ensured at: %s", self.db_path)
