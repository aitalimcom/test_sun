from abc import ABC, abstractmethod
import logging
from typing import Any
from langchain_core.language_models import BaseChatModel
from core.state import AgentState, ToolCallResult
from core.model_registry import get_llm


class BaseAgent(ABC):
    """Abstract base class for all KrishiMitra domain agents."""

    name: str = "base"
    description: str = "Base agent"
    description_np: str = "आधारभूत एजेन्ट"
    model_preference: str = "default"  # "default" | "vision" | "reasoning" | "routing"

    def __init__(self, llm: BaseChatModel | None = None):
        self.logger = logging.getLogger(f"krishimitra.agents.{self.name}")
        self._llm = llm

    @property
    def llm(self) -> BaseChatModel:
        """Dynamically load LLM based on preference if not provided in __init__."""
        if self._llm is None:
            self._llm = get_llm(self.model_preference)
        return self._llm

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the default system prompt for this agent."""
        pass

    @abstractmethod
    async def execute(self, state: AgentState) -> dict[str, Any]:
        """Execute the agent's logic.

        Should return a dictionary of state updates.
        """
        pass

    async def run(self, state: AgentState) -> dict[str, Any]:
        """Compatibility layer for existing code calling .run() instead of .execute()."""
        return await self.execute(state)

    def create_tool_result(
        self,
        query: str,
        result: str,
        success: bool = True,
        error: str | None = None,
        latency_ms: float = 0.0,
    ) -> ToolCallResult:
        """Helper to construct a ToolCallResult TypedDict."""
        return ToolCallResult(
            agent_name=self.name,
            query=query,
            result=result,
            success=success,
            error=error,
            latency_ms=latency_ms,
        )
