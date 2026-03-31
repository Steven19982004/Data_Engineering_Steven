from __future__ import annotations

import logging
import re
from typing import Any

import pandas as pd


logger = logging.getLogger("clean_movies")

_TITLE_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_title(title: str | None) -> str:
    if not title:
        return ""
    cleaned = str(title).strip().lower()
    return _TITLE_NON_ALNUM.sub("", cleaned)


def normalize_genres(value: Any) -> str:
    """
    Normalize genres into a pipe-separated string.

    Examples:
    - "Sci-Fi, Drama" -> "Drama|Sci-Fi"
    - ["Action", "Thriller"] -> "Action|Thriller"
    """
    if value is None:
        return ""

    if isinstance(value, list):
        parts = [str(v).strip() for v in value if str(v).strip()]
    else:
        text = str(value).replace(",", "|").replace("/", "|")
        parts = [p.strip() for p in text.split("|") if p.strip()]

    deduped = sorted(set(parts))
    return "|".join(deduped)


def _coerce_year(row: pd.Series) -> int | None:
    year = row.get("release_year")
    if pd.notna(year):
        try:
            y = int(year)
            if 1880 <= y <= 2100:
                return y
        except Exception:
            pass

    release_date = str(row.get("release_date") or "")
    if len(release_date) >= 4 and release_date[:4].isdigit():
        y = int(release_date[:4])
        if 1880 <= y <= 2100:
            return y

    return None


def clean_movies(df: pd.DataFrame, source_label: str) -> pd.DataFrame:
    """Clean and standardize ingested movie records."""
    if df.empty:
        logger.warning("Input DataFrame is empty for source=%s", source_label)
        return df.copy()

    out = df.copy()

    # Standardize text fields.
    out["title"] = out["title"].fillna("").astype(str).str.strip()
    out["normalized_title"] = out["title"].map(normalize_title)

    out["release_date"] = out["release_date"].fillna("").astype(str).str.strip()
    out["release_year"] = out.apply(_coerce_year, axis=1)

    out["director"] = out.get("director", "").fillna("Unknown").astype(str).str.strip()
    out["genres"] = out.get("genres", "").map(normalize_genres)
    out["original_language"] = (
        out.get("original_language", "unknown").fillna("unknown").astype(str).str.strip().str.lower()
    )
    out["overview"] = out.get("overview", "").fillna("").astype(str).str.strip()
    out["tagline"] = out.get("tagline", "").fillna("").astype(str).str.strip()
    out["review_snippet"] = out.get("review_snippet", "").fillna("").astype(str).str.strip()

    # Numeric fields.
    out["runtime_min"] = pd.to_numeric(out.get("runtime_min"), errors="coerce")
    out["imdb_rating"] = pd.to_numeric(out.get("imdb_rating"), errors="coerce")
    out["vote_count"] = pd.to_numeric(out.get("vote_count"), errors="coerce").fillna(0).astype(int)
    out["popularity"] = pd.to_numeric(out.get("popularity"), errors="coerce")
    out["tmdb_id"] = pd.to_numeric(out.get("tmdb_id"), errors="coerce")

    # Keep only rows that can be keyed by title + year.
    out = out[(out["normalized_title"] != "") & (out["release_year"].notna())].copy()
    out["release_year"] = out["release_year"].astype(int)

    # Deduplicate by logical key using highest vote_count as tie-breaker.
    out = out.sort_values(by=["vote_count"], ascending=False)
    out = out.drop_duplicates(subset=["normalized_title", "release_year"], keep="first")

    out["source_name"] = source_label
    out = out.reset_index(drop=True)

    logger.info("Cleaned %s rows for source=%s", len(out), source_label)
    return out
