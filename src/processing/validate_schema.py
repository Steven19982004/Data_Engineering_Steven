from __future__ import annotations

import logging

import pandas as pd


logger = logging.getLogger("validate_schema")


MOVIE_REQUIRED_COLUMNS = {
    "movie_pk",
    "title",
    "normalized_title",
    "release_year",
    "genres",
    "overview",
}

DOCUMENT_REQUIRED_COLUMNS = {
    "doc_id",
    "movie_pk",
    "title",
    "document_text",
    "metadata_json",
}


def validate_movies_schema(df: pd.DataFrame, stage: str) -> None:
    missing = MOVIE_REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"[{stage}] movies schema missing columns: {sorted(missing)}")

    if df.empty:
        raise ValueError(f"[{stage}] movies DataFrame is empty")

    if df["movie_pk"].isna().any():
        raise ValueError(f"[{stage}] movie_pk contains null values")

    if df["movie_pk"].duplicated().any():
        dup_count = int(df["movie_pk"].duplicated().sum())
        raise ValueError(f"[{stage}] movie_pk has {dup_count} duplicates")

    logger.info("[%s] movies schema validation passed (%s rows)", stage, len(df))


def validate_documents_schema(df: pd.DataFrame, stage: str) -> None:
    missing = DOCUMENT_REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"[{stage}] documents schema missing columns: {sorted(missing)}")

    if df.empty:
        raise ValueError(f"[{stage}] documents DataFrame is empty")

    if df["doc_id"].duplicated().any():
        dup_count = int(df["doc_id"].duplicated().sum())
        raise ValueError(f"[{stage}] doc_id has {dup_count} duplicates")

    logger.info("[%s] document schema validation passed (%s rows)", stage, len(df))
