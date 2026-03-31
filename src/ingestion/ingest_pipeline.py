from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from config import Settings
from ingestion.csv_loader import load_movies_csv
from ingestion.tmdb_client import TMDBClient


@dataclass
class IngestionResult:
    csv_movies: pd.DataFrame
    tmdb_movies: pd.DataFrame


class IngestPipeline:
    """Orchestrates ingestion from CSV and TMDB (API or fixture)."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(
        self,
        csv_path: Path,
        tmdb_fixture_path: Path,
    ) -> IngestionResult:
        self.logger.info("Starting ingestion stage")

        csv_df = load_movies_csv(csv_path)
        tmdb_client = TMDBClient(
            api_key=self.settings.tmdb_api_key,
            enable_api=self.settings.enable_tmdb_api,
        )
        tmdb_df = tmdb_client.load_movies(fixture_path=tmdb_fixture_path, pages=1)

        self.logger.info(
            "Ingestion completed. csv_rows=%s tmdb_rows=%s",
            len(csv_df),
            len(tmdb_df),
        )
        return IngestionResult(csv_movies=csv_df, tmdb_movies=tmdb_df)
