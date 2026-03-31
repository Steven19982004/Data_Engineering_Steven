from __future__ import annotations

import logging

import pandas as pd

from storage.db import SQLiteDB


class MovieRepository:
    def __init__(self, db: SQLiteDB) -> None:
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)

    def upsert_movies(self, movies_df: pd.DataFrame) -> int:
        if movies_df.empty:
            self.logger.warning("upsert_movies called with empty DataFrame")
            return 0

        sql = """
            INSERT INTO movies (
                movie_pk, csv_movie_id, tmdb_id, title, normalized_title, release_date,
                release_year, director, genres, original_language, runtime_min,
                imdb_rating, vote_count, popularity, overview, tagline,
                review_snippet, source_flags
            ) VALUES (
                :movie_pk, :csv_movie_id, :tmdb_id, :title, :normalized_title, :release_date,
                :release_year, :director, :genres, :original_language, :runtime_min,
                :imdb_rating, :vote_count, :popularity, :overview, :tagline,
                :review_snippet, :source_flags
            )
            ON CONFLICT(movie_pk) DO UPDATE SET
                csv_movie_id=excluded.csv_movie_id,
                tmdb_id=excluded.tmdb_id,
                title=excluded.title,
                normalized_title=excluded.normalized_title,
                release_date=excluded.release_date,
                release_year=excluded.release_year,
                director=excluded.director,
                genres=excluded.genres,
                original_language=excluded.original_language,
                runtime_min=excluded.runtime_min,
                imdb_rating=excluded.imdb_rating,
                vote_count=excluded.vote_count,
                popularity=excluded.popularity,
                overview=excluded.overview,
                tagline=excluded.tagline,
                review_snippet=excluded.review_snippet,
                source_flags=excluded.source_flags;
        """

        records = movies_df.to_dict(orient="records")
        with self.db.connect() as conn:
            conn.executemany(sql, records)
            conn.commit()

        self.logger.info("Upserted %s movie rows", len(records))
        return len(records)

    def upsert_movie_documents(self, docs_df: pd.DataFrame) -> int:
        if docs_df.empty:
            self.logger.warning("upsert_movie_documents called with empty DataFrame")
            return 0

        sql = """
            INSERT INTO movie_documents (
                doc_id, movie_pk, title, document_text, metadata_json
            ) VALUES (
                :doc_id, :movie_pk, :title, :document_text, :metadata_json
            )
            ON CONFLICT(doc_id) DO UPDATE SET
                movie_pk=excluded.movie_pk,
                title=excluded.title,
                document_text=excluded.document_text,
                metadata_json=excluded.metadata_json;
        """

        records = docs_df.to_dict(orient="records")
        with self.db.connect() as conn:
            conn.executemany(sql, records)
            conn.commit()

        self.logger.info("Upserted %s document rows", len(records))
        return len(records)

    def get_counts(self) -> dict[str, int]:
        with self.db.connect() as conn:
            movie_count = conn.execute("SELECT COUNT(*) AS c FROM movies;").fetchone()["c"]
            doc_count = conn.execute("SELECT COUNT(*) AS c FROM movie_documents;").fetchone()["c"]

        return {"movies": int(movie_count), "movie_documents": int(doc_count)}
