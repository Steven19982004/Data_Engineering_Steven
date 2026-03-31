from __future__ import annotations

import argparse
import json
import logging

from agent.agent_service import AgentService
from config import Settings


def configure_logging(log_path, level: str = "INFO") -> None:
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
    parser = argparse.ArgumentParser(description="Movie Intelligence Agent CLI")
    parser.add_argument("--query", required=True, help="User question")
    parser.add_argument("--top-k", type=int, default=None, help="Top-k retrieval/results")
    parser.add_argument("--json", action="store_true", help="Print full JSON response")
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Force rebuild semantic index before answering",
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    settings.ensure_dirs()
    configure_logging(settings.log_path, settings.log_level)

    service = AgentService(settings)

    if args.rebuild_index:
        status = service.retriever.build_or_refresh_index(force_rebuild=True)
        logging.getLogger("main").info("Rebuilt index status: %s", status)

    response = service.answer(query=args.query, top_k=args.top_k)

    if args.json:
        print(json.dumps(response, ensure_ascii=False, indent=2))
        return

    print(f"route: {response['route']['route_type']}")
    print(f"used_tools: {response['used_tools']}")
    print("\nanswer:\n")
    print(response["answer"])


if __name__ == "__main__":
    main()
