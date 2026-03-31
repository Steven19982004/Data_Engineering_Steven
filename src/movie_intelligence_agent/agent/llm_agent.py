from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from movie_intelligence_agent.config import Settings
from movie_intelligence_agent.exceptions import AgentUnavailableError
from movie_intelligence_agent.models import AgentResponse
from movie_intelligence_agent.tools.movie_tools import MovieTools
from movie_intelligence_agent.tools.sql_tools import SQLTools

try:
    from openai import OpenAI
except Exception:  # optional dependency for fully offline mode
    OpenAI = None


SYSTEM_PROMPT = (
    "You are a movie intelligence agent. Use tools for factual retrieval first, then answer concisely. "
    "Do not fabricate data. Cite tool outputs in plain language."
)


@dataclass
class OpenAIToolAgent:
    settings: Settings
    sql_tools: SQLTools
    movie_tools: MovieTools

    def __post_init__(self) -> None:
        if OpenAI is None:
            raise AgentUnavailableError("openai package not installed")
        if not self.settings.openai_api_key:
            raise AgentUnavailableError("OPENAI_API_KEY is empty")

        self.client = OpenAI(api_key=self.settings.openai_api_key)

    def ask(self, question: str) -> AgentResponse:
        tools = self._tool_specs()
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
        trace: list[dict[str, Any]] = []

        for _ in range(6):
            completion = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0,
            )
            message = completion.choices[0].message

            if not message.tool_calls:
                return AgentResponse(
                    question=question,
                    answer=message.content or "No response generated.",
                    tool_trace=trace,
                    mode="openai_tool_calling",
                )

            assistant_msg = {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": c.id,
                        "type": "function",
                        "function": {"name": c.function.name, "arguments": c.function.arguments},
                    }
                    for c in message.tool_calls
                ],
            }
            messages.append(assistant_msg)

            for call in message.tool_calls:
                args = json.loads(call.function.arguments or "{}")
                result = self._dispatch(call.function.name, args)
                trace.append({"tool": call.function.name, "params": args})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        return AgentResponse(
            question=question,
            answer="Tool-calling loop reached max iterations. Please refine your query.",
            tool_trace=trace,
            mode="openai_tool_calling",
        )

    def _dispatch(self, name: str, args: dict[str, Any]) -> Any:
        if name == "sql_fetch_high_rated_scifi":
            return self.sql_tools.fetch_high_rated_scifi(
                year_from=int(args.get("year_from", 2015)),
                min_rating=float(args.get("min_rating", 7.5)),
                limit=int(args.get("limit", 10)),
            )
        if name == "sql_fetch_high_quality_thrillers":
            return self.sql_tools.fetch_high_quality_thrillers(
                min_rating=float(args.get("min_rating", 7.5)),
                min_votes=int(args.get("min_votes", self.settings.thriller_min_votes)),
                limit=int(args.get("limit", 10)),
            )
        if name == "sql_compare_directors":
            return self.sql_tools.compare_directors(
                director_a=str(args.get("director_a", "Christopher Nolan")),
                director_b=str(args.get("director_b", "Denis Villeneuve")),
            )
        if name == "vector_find_similar_movies":
            return self.movie_tools.find_similar_movies(
                movie_title=str(args.get("movie_title", "Interstellar")),
                top_k=int(args.get("top_k", self.settings.default_top_k)),
            )
        if name == "nlp_summarize_common_themes":
            return self.movie_tools.summarize_common_themes(
                movie_titles=list(args.get("movie_titles", []))
            )
        if name == "vector_retrieve_by_question":
            return self.movie_tools.retrieve_by_question(
                question=str(args.get("question", "")),
                top_k=int(args.get("top_k", self.settings.default_top_k)),
            )
        raise ValueError(f"Unknown tool: {name}")

    def _tool_specs(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "sql_fetch_high_rated_scifi",
                    "description": "Find high-rated sci-fi movies after a given year.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "year_from": {"type": "integer"},
                            "min_rating": {"type": "number"},
                            "limit": {"type": "integer"},
                        },
                        "required": ["year_from"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "sql_fetch_high_quality_thrillers",
                    "description": "Find thriller movies with high rating and enough votes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "min_rating": {"type": "number"},
                            "min_votes": {"type": "integer"},
                            "limit": {"type": "integer"},
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "sql_compare_directors",
                    "description": "Compare two directors by average rating and votes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "director_a": {"type": "string"},
                            "director_b": {"type": "string"},
                        },
                        "required": ["director_a", "director_b"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "vector_find_similar_movies",
                    "description": "Find movies semantically similar to a target movie.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "movie_title": {"type": "string"},
                            "top_k": {"type": "integer"},
                        },
                        "required": ["movie_title"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "nlp_summarize_common_themes",
                    "description": "Summarize common themes for a list of movie titles.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "movie_titles": {
                                "type": "array",
                                "items": {"type": "string"},
                            }
                        },
                        "required": ["movie_titles"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "vector_retrieve_by_question",
                    "description": "Retrieve semantically related movies for a user question.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "top_k": {"type": "integer"},
                        },
                        "required": ["question"],
                    },
                },
            },
        ]
