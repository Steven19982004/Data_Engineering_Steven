from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from movie_intelligence_agent.exceptions import DataValidationError
from movie_intelligence_agent.logger import get_logger


_TITLE_PATTERN = re.compile(r"[^a-z0-9]+")


def normalize_title(value: str) -> str:
    value = (value or "").strip().lower()
    return _TITLE_PATTERN.sub("", value)


@dataclass
class DataTransformer:
    def __post_init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)

    def clean_movies(self, df: pd.DataFrame) -> pd.DataFrame:
        required = {
            "movie_id",
            "title",
            "release_date",
            "director",
            "genres",
            "runtime_min",
            "language",
            "overview",
        }
        self._ensure_columns(df, required, "movies_catalog")

        out = df.copy()
        out["title"] = out["title"].astype(str).str.strip()
        out["normalized_title"] = out["title"].map(normalize_title)
        out["release_date"] = pd.to_datetime(out["release_date"], errors="coerce")
        out["release_year"] = out["release_date"].dt.year
        out["runtime_min"] = pd.to_numeric(out["runtime_min"], errors="coerce").fillna(0).astype(int)
        out["genres"] = out["genres"].astype(str).str.replace("|", ", ", regex=False)
        out["overview"] = out["overview"].fillna("No overview provided").astype(str)

        out = out.dropna(subset=["release_year"])
        out = out.drop_duplicates(subset=["normalized_title", "release_year"])

        self.logger.info("Cleaned movies rows: %s", len(out))
        return out

    def clean_ratings(self, df: pd.DataFrame) -> pd.DataFrame:
        required = {"title", "release_year", "imdb_rating", "vote_count", "metascore", "last_updated"}
        self._ensure_columns(df, required, "ratings_snapshot")

        out = df.copy()
        out["title"] = out["title"].astype(str).str.strip()
        out["normalized_title"] = out["title"].map(normalize_title)
        out["release_year"] = pd.to_numeric(out["release_year"], errors="coerce")
        out["imdb_rating"] = pd.to_numeric(out["imdb_rating"], errors="coerce")
        out["vote_count"] = pd.to_numeric(out["vote_count"], errors="coerce").fillna(0).astype(int)
        out["metascore"] = pd.to_numeric(out["metascore"], errors="coerce")
        out["last_updated"] = pd.to_datetime(out["last_updated"], errors="coerce")

        out = out.dropna(subset=["release_year", "imdb_rating"])
        out["release_year"] = out["release_year"].astype(int)
        out = out.drop_duplicates(subset=["normalized_title", "release_year"], keep="last")

        self.logger.info("Cleaned ratings rows: %s", len(out))
        return out

    def clean_reviews(self, df: pd.DataFrame) -> pd.DataFrame:
        required = {"movie_title", "review_text", "sentiment", "source"}
        self._ensure_columns(df, required, "reviews_corpus")

        out = df.copy()
        out["movie_title"] = out["movie_title"].astype(str).str.strip()
        out["normalized_title"] = out["movie_title"].map(normalize_title)
        out["review_text"] = out["review_text"].fillna("").astype(str).str.strip()
        out["sentiment"] = out["sentiment"].fillna("unknown").astype(str).str.lower()
        out = out[out["review_text"].str.len() > 0]

        self.logger.info("Cleaned reviews rows: %s", len(out))
        return out

    def merge_movies_and_ratings(self, movies_df: pd.DataFrame, ratings_df: pd.DataFrame) -> pd.DataFrame:
        merged = movies_df.merge(
            ratings_df[
                [
                    "normalized_title",
                    "release_year",
                    "imdb_rating",
                    "vote_count",
                    "metascore",
                    "last_updated",
                ]
            ],
            on=["normalized_title", "release_year"],
            how="left",
        )

        merged["imdb_rating"] = merged["imdb_rating"].fillna(0.0)
        merged["vote_count"] = merged["vote_count"].fillna(0).astype(int)
        merged["metascore"] = merged["metascore"].fillna(0.0)
        merged["last_updated"] = merged["last_updated"].dt.strftime("%Y-%m-%d").fillna("")

        self.logger.info("Merged movie records: %s", len(merged))
        return merged

    def attach_enrichment(self, movies_df: pd.DataFrame, enrichment_df: pd.DataFrame) -> pd.DataFrame:
        if enrichment_df.empty:
            movies_df["awards"] = "N/A"
            movies_df["box_office"] = "N/A"
            movies_df["country"] = "N/A"
            movies_df["enrichment_source"] = "none"
            return movies_df

        out = movies_df.merge(enrichment_df, on="title", how="left")
        for col in ["awards", "box_office", "country", "enrichment_source"]:
            out[col] = out[col].fillna("N/A")
        return out

    def attach_movie_ids_to_reviews(
        self, reviews_df: pd.DataFrame, movies_df: pd.DataFrame
    ) -> pd.DataFrame:
        mapped = reviews_df.merge(
            movies_df[["movie_id", "normalized_title"]],
            on="normalized_title",
            how="left",
        )
        mapped = mapped.dropna(subset=["movie_id"]).copy()
        mapped["movie_id"] = mapped["movie_id"].astype(str)
        return mapped

    def build_movie_documents(
        self, movies_df: pd.DataFrame, reviews_df: pd.DataFrame
    ) -> list[dict[str, str]]:
        review_grouped = reviews_df.groupby("movie_id")["review_text"].apply(lambda x: " ".join(x)).to_dict()

        docs: list[dict[str, str]] = []
        for _, row in movies_df.iterrows():
            combined_text = " ".join(
                [
                    str(row["title"]),
                    str(row["director"]),
                    str(row["genres"]),
                    str(row["overview"]),
                    review_grouped.get(row["movie_id"], ""),
                ]
            ).strip()
            docs.append(
                {
                    "movie_id": str(row["movie_id"]),
                    "title": str(row["title"]),
                    "text": combined_text,
                }
            )
        return docs

    def write_processed_files(
        self,
        merged_movies_df: pd.DataFrame,
        processed_dir: Path,
        lineage_payload: dict[str, Any],
    ) -> None:
        processed_dir.mkdir(parents=True, exist_ok=True)

        merged_movies_df.to_csv(processed_dir / "unified_movies.csv", index=False)
        with (processed_dir / "data_lineage.json").open("w", encoding="utf-8") as f:
            json.dump(lineage_payload, f, ensure_ascii=False, indent=2)

    def _ensure_columns(self, df: pd.DataFrame, required: set[str], label: str) -> None:
        missing = required - set(df.columns)
        if missing:
            raise DataValidationError(f"{label} missing required columns: {sorted(missing)}")
