from __future__ import annotations

import logging

import pandas as pd


logger = logging.getLogger("merge_sources")


def _first_not_null(values: list) -> object:
    for value in values:
        if pd.notna(value) and str(value).strip() != "":
            return value
    return None


def merge_movie_sources(csv_df: pd.DataFrame, tmdb_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge two movie sources using title + year as the primary key.

    Why title + year:
    - IDs differ across systems (internal CSV id vs TMDB id).
    - Title alone is ambiguous across remakes/reboots.
    - Title + release year gives a practical, explainable key for coursework scale.
    """
    if csv_df.empty and tmdb_df.empty:
        raise ValueError("Cannot merge empty sources")

    left = csv_df.copy()
    right = tmdb_df.copy()

    merged = left.merge(
        right,
        on=["normalized_title", "release_year"],
        how="outer",
        suffixes=("_csv", "_tmdb"),
    )

    records = []
    for _, row in merged.iterrows():
        title = _first_not_null([row.get("title_csv"), row.get("title_tmdb")])
        release_year = int(row["release_year"])
        movie_pk = f"{row['normalized_title']}_{release_year}"

        source_flags = []
        if pd.notna(row.get("title_csv")):
            source_flags.append("csv")
        if pd.notna(row.get("title_tmdb")):
            source_flags.append("tmdb")

        record = {
            "movie_pk": movie_pk,
            "csv_movie_id": _first_not_null([row.get("csv_movie_id_csv")]),
            "tmdb_id": _first_not_null([row.get("tmdb_id_tmdb"), row.get("tmdb_id_csv")]),
            "title": title,
            "normalized_title": row["normalized_title"],
            "release_date": _first_not_null([row.get("release_date_csv"), row.get("release_date_tmdb")]),
            "release_year": release_year,
            "director": _first_not_null([row.get("director_csv"), row.get("director_tmdb"), "Unknown"]),
            "genres": _first_not_null([row.get("genres_csv"), row.get("genres_tmdb"), ""]),
            "original_language": _first_not_null(
                [row.get("original_language_csv"), row.get("original_language_tmdb"), "unknown"]
            ),
            "runtime_min": _first_not_null([row.get("runtime_min_csv"), row.get("runtime_min_tmdb")]),
            "imdb_rating": _first_not_null([row.get("imdb_rating_csv"), row.get("imdb_rating_tmdb")]),
            "vote_count": int(_first_not_null([row.get("vote_count_csv"), row.get("vote_count_tmdb"), 0])),
            "popularity": _first_not_null([row.get("popularity_csv"), row.get("popularity_tmdb")]),
            "overview": _first_not_null([row.get("overview_csv"), row.get("overview_tmdb"), ""]),
            "tagline": _first_not_null([row.get("tagline_csv"), row.get("tagline_tmdb"), ""]),
            "review_snippet": _first_not_null(
                [row.get("review_snippet_csv"), row.get("review_snippet_tmdb"), ""]
            ),
            "source_flags": "|".join(source_flags),
        }
        records.append(record)

    result = pd.DataFrame(records)

    # Safety dedup after merge.
    result = result.sort_values(by=["vote_count"], ascending=False)
    result = result.drop_duplicates(subset=["normalized_title", "release_year"], keep="first")
    result = result.reset_index(drop=True)

    logger.info("Merged sources into %s unified movie rows", len(result))
    return result
