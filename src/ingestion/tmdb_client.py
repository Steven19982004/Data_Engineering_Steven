from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import requests


@dataclass
class TMDBClient:
    """
    TMDB data loader with a safe offline-first fallback.

    - If API is enabled and key exists, it tries TMDB API.
    - If API fails or is disabled, it loads local fixture JSON.
    """

    api_key: str
    enable_api: bool = False
    timeout: int = 10

    def __post_init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.base_url = "https://api.themoviedb.org/3"

    def load_movies(
        self,
        fixture_path: Path,
        pages: int = 1,
        language: str = "en-US",
    ) -> pd.DataFrame:
        if self.enable_api and self.api_key:
            self.logger.info("TMDB API enabled. Attempting live fetch.")
            try:
                return self.fetch_from_api(pages=pages, language=language)
            except Exception as exc:
                self.logger.warning(
                    "TMDB API fetch failed. Falling back to fixture. error=%s", exc
                )

        self.logger.info("Loading TMDB data from fixture: %s", fixture_path)
        return self.load_from_fixture(fixture_path)

    def fetch_from_api(self, pages: int = 1, language: str = "en-US") -> pd.DataFrame:
        rows: list[dict[str, Any]] = []

        for page in range(1, pages + 1):
            payload = self._request_json(
                endpoint="/movie/popular",
                params={"page": page, "language": language},
            )
            genre_map = self._build_genre_map_from_api(language=language)
            records = payload.get("results", [])
            for record in records:
                rows.append(self._normalize_record(record, genre_map, source_name="tmdb_api"))

        if not rows:
            raise RuntimeError("TMDB API returned no rows")

        df = pd.DataFrame(rows)
        self.logger.info("Fetched %s rows from TMDB API", len(df))
        return df

    def load_from_fixture(self, fixture_path: Path) -> pd.DataFrame:
        if not fixture_path.exists():
            raise FileNotFoundError(f"TMDB fixture not found: {fixture_path}")

        with fixture_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        genre_map = {
            int(item["id"]): str(item["name"])
            for item in payload.get("genres", [])
            if "id" in item and "name" in item
        }
        source_name = str(payload.get("source", "tmdb_fixture"))

        rows = [
            self._normalize_record(record, genre_map=genre_map, source_name=source_name)
            for record in payload.get("results", [])
        ]

        if not rows:
            raise RuntimeError(f"No movie results found in fixture: {fixture_path}")

        df = pd.DataFrame(rows)
        self.logger.info("Loaded %s rows from TMDB fixture", len(df))
        return df

    def _build_genre_map_from_api(self, language: str = "en-US") -> dict[int, str]:
        payload = self._request_json("/genre/movie/list", params={"language": language})
        return {
            int(item["id"]): str(item["name"])
            for item in payload.get("genres", [])
            if "id" in item and "name" in item
        }

    def _request_json(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("TMDB API key is empty")

        req_params = {"api_key": self.api_key, **params}
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=req_params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def _normalize_record(
        self,
        record: dict[str, Any],
        genre_map: dict[int, str],
        source_name: str,
    ) -> dict[str, Any]:
        genre_ids = record.get("genre_ids", []) or []
        genres = "|".join([genre_map.get(int(gid), str(gid)) for gid in genre_ids])

        return {
            "csv_movie_id": None,
            "tmdb_id": record.get("id"),
            "title": record.get("title"),
            "release_date": record.get("release_date"),
            "release_year": None,
            "director": record.get("director"),
            "genres": genres,
            "original_language": record.get("original_language"),
            "runtime_min": record.get("runtime") or None,
            "imdb_rating": record.get("vote_average"),
            "vote_count": record.get("vote_count"),
            "popularity": record.get("popularity"),
            "overview": record.get("overview"),
            "tagline": record.get("tagline"),
            "review_snippet": record.get("review_snippet"),
            "source_name": source_name,
        }
