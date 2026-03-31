from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]


def _run_pipeline() -> None:
    subprocess.run(
        [sys.executable, str(ROOT_DIR / "scripts" / "run_pipeline.py")],
        cwd=str(ROOT_DIR),
        check=True,
    )


def test_pipeline_outputs_processed_files_and_sqlite_tables() -> None:
    _run_pipeline()

    processed_dir = ROOT_DIR / "data" / "processed"
    expected_files = [
        processed_dir / "01_ingested_csv.csv",
        processed_dir / "02_ingested_tmdb.csv",
        processed_dir / "03_cleaned_csv.csv",
        processed_dir / "04_cleaned_tmdb.csv",
        processed_dir / "05_merged_movies.csv",
        processed_dir / "06_movie_documents.csv",
    ]

    for file_path in expected_files:
        assert file_path.exists(), f"Missing processed output: {file_path}"

    merged_df = pd.read_csv(processed_dir / "05_merged_movies.csv")
    docs_df = pd.read_csv(processed_dir / "06_movie_documents.csv")
    assert len(merged_df) >= 10
    assert len(docs_df) >= 10

    db_path = ROOT_DIR / "storage" / "movie_agent.db"
    assert db_path.exists()

    with sqlite3.connect(db_path) as conn:
        movie_count = conn.execute("SELECT COUNT(*) FROM movies;").fetchone()[0]
        doc_count = conn.execute("SELECT COUNT(*) FROM movie_documents;").fetchone()[0]

    assert movie_count >= 10
    assert doc_count >= 10
