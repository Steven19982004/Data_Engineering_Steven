from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from movie_intelligence_agent.config import Settings
from movie_intelligence_agent.exceptions import PipelineError
from movie_intelligence_agent.logger import get_logger


@dataclass
class DataExtractor:
    settings: Settings

    def __post_init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)

    def load_movies_catalog(self) -> pd.DataFrame:
        path = self.settings.raw_data_dir / "movies_catalog.csv"
        return self._load_csv(path, "movies catalog")

    def load_ratings_snapshot(self) -> pd.DataFrame:
        path = self.settings.raw_data_dir / "ratings_snapshot.csv"
        return self._load_csv(path, "ratings snapshot")

    def load_reviews_corpus(self) -> pd.DataFrame:
        path = self.settings.raw_data_dir / "reviews_corpus.jsonl"
        try:
            rows: list[dict[str, Any]] = []
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        rows.append(json.loads(line))
            df = pd.DataFrame(rows)
            self.logger.info("Loaded reviews corpus: %s rows", len(df))
            return df
        except FileNotFoundError as exc:
            raise PipelineError(f"Reviews file not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise PipelineError(f"Invalid JSONL in {path}: {exc}") from exc

    def load_omdb_fixture(self) -> dict[str, dict[str, str]]:
        path = self.settings.raw_data_dir / "omdb_fixture.json"
        try:
            with path.open("r", encoding="utf-8") as f:
                fixture = json.load(f)
            self.logger.info("Loaded OMDb fixture entries: %s", len(fixture))
            return fixture
        except FileNotFoundError as exc:
            raise PipelineError(f"OMDb fixture not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise PipelineError(f"Invalid OMDb fixture JSON: {exc}") from exc

    def get_omdb_enrichment(self, titles: list[str]) -> pd.DataFrame:
        fixture = self.load_omdb_fixture()
        rows: list[dict[str, Any]] = []

        use_api = self.settings.enable_omdb_enrichment and bool(self.settings.omdb_api_key)
        if use_api:
            self.logger.info("OMDb enrichment enabled: trying online API first")

        for title in titles:
            payload: dict[str, Any] | None = None
            if use_api:
                payload = self._fetch_omdb_from_api(title)
            if payload is None:
                payload = fixture.get(title)
                source = "fixture"
            else:
                source = "omdb_api"

            rows.append(
                {
                    "title": title,
                    "awards": (payload or {}).get("awards", "N/A"),
                    "box_office": (payload or {}).get("box_office", "N/A"),
                    "country": (payload or {}).get("country", "N/A"),
                    "enrichment_source": source,
                }
            )

        return pd.DataFrame(rows)

    def _fetch_omdb_from_api(self, title: str) -> dict[str, str] | None:
        endpoint = "https://www.omdbapi.com/"
        params = {"apikey": self.settings.omdb_api_key, "t": title}

        try:
            response = requests.get(endpoint, params=params, timeout=6)
            response.raise_for_status()
            data = response.json()
            if data.get("Response") == "False":
                self.logger.warning("OMDb API returned no result for title=%s", title)
                return None

            return {
                "awards": data.get("Awards", "N/A"),
                "box_office": data.get("BoxOffice", "N/A"),
                "country": data.get("Country", "N/A"),
            }
        except Exception as exc:  # network and API errors should not break the pipeline
            self.logger.warning("OMDb API failed for title=%s error=%s", title, exc)
            return None

    def _load_csv(self, path: Path, label: str) -> pd.DataFrame:
        try:
            df = pd.read_csv(path)
            self.logger.info("Loaded %s: %s rows", label, len(df))
            return df
        except FileNotFoundError as exc:
            raise PipelineError(f"{label} file not found: {path}") from exc
        except Exception as exc:
            raise PipelineError(f"Failed reading {label}: {exc}") from exc
