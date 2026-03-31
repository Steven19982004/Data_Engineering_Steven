from __future__ import annotations

from dataclasses import dataclass

from movie_intelligence_agent.agent.llm_agent import OpenAIToolAgent
from movie_intelligence_agent.agent.local_agent import LocalRuleBasedAgent
from movie_intelligence_agent.config import Settings
from movie_intelligence_agent.exceptions import AgentUnavailableError
from movie_intelligence_agent.logger import configure_logging, get_logger
from movie_intelligence_agent.models import AgentResponse
from movie_intelligence_agent.retrieval.vector_store import LocalVectorStore
from movie_intelligence_agent.tools.movie_tools import MovieTools
from movie_intelligence_agent.tools.sql_tools import SQLTools


@dataclass
class MovieIntelligenceAgent:
    settings: Settings
    force_local: bool = False

    def __post_init__(self) -> None:
        self.settings.ensure_directories()
        configure_logging(self.settings.log_path)
        self.logger = get_logger(self.__class__.__name__)

        self.sql_tools = SQLTools(db_path=self.settings.sqlite_path)
        self.vector_store = LocalVectorStore(store_dir=self.settings.vector_store_dir)
        self.movie_tools = MovieTools(db_path=self.settings.sqlite_path, vector_store=self.vector_store)

        if self.force_local:
            self.agent = LocalRuleBasedAgent(self.settings, self.sql_tools, self.movie_tools)
            self.mode = "local_rule_based"
            return

        try:
            self.agent = OpenAIToolAgent(self.settings, self.sql_tools, self.movie_tools)
            self.mode = "openai_tool_calling"
            self.logger.info("Agent mode: openai_tool_calling")
        except AgentUnavailableError as exc:
            self.logger.warning("Falling back to local rule-based agent: %s", exc)
            self.agent = LocalRuleBasedAgent(self.settings, self.sql_tools, self.movie_tools)
            self.mode = "local_rule_based"

    def ask(self, question: str) -> AgentResponse:
        response = self.agent.ask(question)
        self.logger.info("Agent question=%s mode=%s tools=%s", question, self.mode, response.tool_trace)
        return response
