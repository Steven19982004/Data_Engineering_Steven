from __future__ import annotations

import argparse
import json

from movie_intelligence_agent.agent.runner import MovieIntelligenceAgent
from movie_intelligence_agent.config import Settings
from movie_intelligence_agent.data.pipeline import run_data_pipeline
from movie_intelligence_agent.evaluation.evaluate import run_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(description="Movie Intelligence Agent CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Run ETL pipeline and build vector index")
    build_parser.set_defaults(command="build")

    ask_parser = subparsers.add_parser("ask", help="Ask agent a question")
    ask_parser.add_argument("--question", required=True, help="Natural language question")
    ask_parser.add_argument("--force-local", action="store_true", help="Force local rule-based agent")
    ask_parser.add_argument("--json", action="store_true", help="Print response as JSON")

    eval_parser = subparsers.add_parser("eval", help="Run basic evaluation suite")
    eval_parser.add_argument("--force-local", action="store_true", help="Force local rule-based agent")

    args = parser.parse_args()
    settings = Settings.from_env()

    if args.command == "build":
        summary = run_data_pipeline(settings)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    if args.command == "ask":
        agent = MovieIntelligenceAgent(settings=settings, force_local=args.force_local)
        response = agent.ask(args.question)
        if args.json:
            print(json.dumps(response.__dict__, ensure_ascii=False, indent=2))
        else:
            print(f"mode: {response.mode}")
            print("tools:", response.tool_trace)
            print("\nanswer:\n")
            print(response.answer)
        return

    if args.command == "eval":
        report = run_evaluation(settings=settings, force_local=args.force_local)
        print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
