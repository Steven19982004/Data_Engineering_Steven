from __future__ import annotations

import json
import logging
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import Settings  # noqa: E402
from evaluation.evaluator import Evaluator  # noqa: E402


def configure_logging(log_path: Path, level: str = "INFO") -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )


def main() -> None:
    settings = Settings.from_env()
    settings.ensure_dirs()
    configure_logging(settings.log_path, settings.log_level)

    evaluator = Evaluator(settings)
    report = evaluator.run(top_k=settings.default_top_k)

    output_dir = ROOT_DIR / "data" / "processed"
    saved = evaluator.save(report, output_dir=output_dir)

    summary = {
        "summary": report["summary"],
        "saved_paths": saved,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
