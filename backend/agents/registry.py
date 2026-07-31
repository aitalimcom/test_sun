"""Agent registry — central registration and dispatch of all agents."""

from __future__ import annotations

import logging
from typing import Any

from core.agent import BaseAgent
from core.graph import agent_graph

logger = logging.getLogger(__name__)

# Import all agents
from agents.supervisor.agent import SupervisorAgent
from agents.disease.agent import DiseaseAgent
from agents.diagnosis.agent import DiagnosisAgent
from agents.species.agent import SpeciesAgent
from agents.weather.agent import WeatherAgent
from agents.market.agent import MarketAgent
from agents.iot.agent import IoTAgent
from agents.farm_cycle.agent import FarmCycleAgent
from agents.nutrient.agent import NutrientAgent
from agents.knowledge.agent import KnowledgeAgent
from agents.calendar.agent import CalendarAgent
from agents.bajar.agent import BajarAgent
from agents.table_query.agent import TableAgent
from agents.web_search.agent import WebSearchAgent
from agents.daily.agent import DailyAgent
from agents.advisory.agent import AdvisoryAgent
from agents.output_synthesizer.agent import OutputSynthesizerAgent


# Agent registry mapping
AGENTS: dict[str, type[BaseAgent]] = {
    "supervisor": SupervisorAgent,
    "disease": DiseaseAgent,
    "diagnosis": DiagnosisAgent,
    "species": SpeciesAgent,
    "weather": WeatherAgent,
    "market": MarketAgent,
    "iot": IoTAgent,
    "iot_status": IoTAgent,  # Direct mapping for backward compatibility
    "farm_cycle": FarmCycleAgent,
    "nutrient": NutrientAgent,
    "knowledge": KnowledgeAgent,
    "calendar": CalendarAgent,
    "bajar": BajarAgent,
    "table_query": TableAgent,
    "web_search": WebSearchAgent,
    "daily": DailyAgent,
    "advisory": AdvisoryAgent,
    "output_synthesizer": OutputSynthesizerAgent,
}


def get_agent(name: str) -> BaseAgent:
    """Get an agent instance by name."""
    agent_cls = AGENTS.get(name)
    if not agent_cls:
        raise ValueError(f"Unknown agent: {name}. Available: {list(AGENTS.keys())}")
    return agent_cls()


def get_all_agents() -> dict[str, BaseAgent]:
    """Get all agent instances."""
    return {name: cls() for name, cls in AGENTS.items()}


def initialize_graph():
    """Initialize the LangGraph workflow with all agents and return compiled graph."""
    for name, cls in AGENTS.items():
        if name not in ("supervisor", "output_synthesizer"):
            agent = cls()
            agent_graph.register_agent(agent)

    agent_graph.build()
    logger.info("LangGraph orchestrator built successfully.")
    return agent_graph.get_compiled_graph()


async def dispatch_to_agent(
    agent_name: str,
    query: str,
    state: dict[str, Any] | None = None,
) -> str:
    """Simple dispatch to a single agent (bypassing the graph structure).

    Useful for cron tasks, direct actions, or direct API routes.
    """
    agent = get_agent(agent_name)
    from core.state import AgentState, create_initial_state

    initial_state = create_initial_state(
        user_message=query,
        session_id=state.get("session_id") if state else None,
        images=state.get("images") if state else None,
        language=state.get("language", "ne-NP") if state else "ne-NP",
    )

    # Prepare dispatcher context
    initial_state["dispatch_query"] = query

    result = await agent.execute(initial_state)
    messages = result.get("new_messages", [])
    if messages:
        return messages[-1].get("content", "")
    
    return result.get("result") or "सम्बन्धित एजेन्टबाट कुनै प्रतिक्रिया प्राप्त भएन।"
