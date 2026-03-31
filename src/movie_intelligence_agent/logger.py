from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


_LOGGER_READY = False


def configure_logging(log_path: Path, level: int = logging.INFO) -> None:
    global _LOGGER_READY
    if _LOGGER_READY:
        return

    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    file_handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _LOGGER_READY = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
