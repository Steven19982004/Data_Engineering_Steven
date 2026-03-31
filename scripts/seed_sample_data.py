from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import Settings  # noqa: E402


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def copy_if_needed(src: Path, dst: Path, force: bool = False) -> bool:
    if not src.exists():
        raise FileNotFoundError(f"Source fixture not found: {src}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not force:
        return False

    shutil.copy2(src, dst)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed raw data from fixture files")
    parser.add_argument("--force", action="store_true", help="Overwrite raw files if they exist")
    args = parser.parse_args()

    configure_logging()
    logger = logging.getLogger("seed_sample_data")

    settings = Settings.from_env()

    raw_csv = ROOT_DIR / "data" / "raw" / "movies_from_csv.csv"
    raw_tmdb = ROOT_DIR / "data" / "raw" / "movies_from_tmdb_fixture.json"

    copied_csv = copy_if_needed(settings.fixture_movies_csv, raw_csv, force=args.force)
    copied_tmdb = copy_if_needed(settings.fixture_tmdb_json, raw_tmdb, force=args.force)

    logger.info(
        "Seeding done. csv=%s tmdb=%s raw_dir=%s",
        "copied" if copied_csv else "kept",
        "copied" if copied_tmdb else "kept",
        ROOT_DIR / "data" / "raw",
    )


if __name__ == "__main__":
    main()
