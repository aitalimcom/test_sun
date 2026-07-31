"""LangGraph workflow definition — the multi-agent orchestration graph."""

from __future__ import annotations

import logging
from typing import Any, Literal

from langgraph.graph import StateGraph, END

from core.state import AgentState
from core.agent import BaseAgent

logger = logging.getLogger(__name__)


class AgentGraph:
    """Builds and runs the LangGraph multi-agent workflow.

    Architecture:
        START → preprocess → supervisor → (subagents) → synthesize → END

    - preprocess: parses multimodal input, standardizes audio/images and translates queries to Devanagari Nepali.
    - supervisor: classifies the intent and selects the specialized subagent.
    - subagents: execute specific tasks (weather, market, disease, species, etc.).
    - synthesize: output synthesizer agent that compiles everything into a structured response.
    """

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}
        self._graph: StateGraph | None = None
        self._compiled = None

    def register_agent(self, agent: BaseAgent) -> None:
        """Register a subagent with the graph."""
        self._agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")

    def build(self) -> None:
        """Build the LangGraph workflow."""
        graph = StateGraph(AgentState)

        # Add preprocess node
        graph.add_node("preprocess", self._preprocess_node)

        # Add supervisor node
        graph.add_node("supervisor", self._supervisor_node)

        # Add subagent nodes
        for name, agent in self._agents.items():
            if name not in ("supervisor", "output_synthesizer"):
                graph.add_node(name, self._make_agent_node(agent))

        # Add synthesis node (Output Synthesizer Agent)
        graph.add_node("synthesize", self._synthesize_node)

        # Entry point is preprocess
        graph.set_entry_point("preprocess")

        # Preprocess goes to supervisor
        graph.add_edge("preprocess", "supervisor")

        # Supervisor routes to subagents or directly to synthesize
        subagent_names = [name for name in self._agents if name not in ("supervisor", "output_synthesizer")]
        graph.add_conditional_edges(
            "supervisor",
            self._route_from_supervisor,
            {name: name for name in subagent_names} | {"__end__": "synthesize"},
        )

        # All subagents go to synthesize
        for name in subagent_names:
            graph.add_edge(name, "synthesize")

        # Synthesize goes to end
        graph.add_edge("synthesize", END)

        self._graph = graph
        self._compiled = graph.compile()
        logger.info(f"Graph built with agents: {list(self._agents.keys())}")

    async def run(
        self,
        initial_state: AgentState,
        max_iterations: int = 5,
    ) -> AgentState:
        """Run the graph with the given initial state."""
        if self._compiled is None:
            self.build()

        config = {"recursion_limit": max_iterations * 2}
        final_state = await self._compiled.ainvoke(initial_state, config)
        return final_state

    # ── Node implementations ──

    async def _preprocess_node(self, state: AgentState) -> dict[str, Any]:
        """Node for preprocessing multimodal input and language standardization."""
        logger.info("Executing preprocess node...")
        from core.multimodal.preprocessor import MultimodalPreprocessor
        
        preprocessor = MultimodalPreprocessor()
        
        orig = state.get("original_input", {})
        user_text = orig.get("text", "")
        images = orig.get("images", [])
        audio_data = orig.get("audio_data")
        
        processed = await preprocessor.process(
            text=user_text,
            images=images,
            audio_data=audio_data,
            source_language=state["metadata"].get("language", "auto")
        )
        
        return {
            "processed_input": processed.to_dict(),
            "normalized_query": processed.normalized_text,
            "detected_language": processed.detected_language,
            "image_analyses": [analysis.to_dict() for analysis in processed.image_analyses],
        }

    async def _supervisor_node(self, state: AgentState) -> dict[str, Any]:
        """Supervisor: classify intent and decide routing."""
        logger.info("Executing supervisor node...")
        from agents.supervisor.agent import SupervisorAgent

        supervisor = SupervisorAgent()
        result = await supervisor.execute(state)

        return {
            "intent": result.get("intent"),
            "next_agent": result.get("next_agent"),
            "dispatch_query": result.get("dispatch_query"),
            "needs_agent": result.get("needs_agent", False),
            "is_complete": result.get("is_complete", False),
            "final_response": result.get("final_response"),
            "messages": result.get("new_messages", []),
        }

    def _make_agent_node(self, agent: BaseAgent):
        """Create a LangGraph node function for an agent."""
        async def agent_node(state: AgentState) -> dict[str, Any]:
            logger.info(f"Executing agent node: {agent.name}...")
            result = await agent.execute(state)
            
            # Store in agent_results accumulator
            agent_results = list(state.get("agent_results", []))
            agent_results.append({
                "agent_name": agent.name,
                "result": result.get("result"),
                "success": result.get("success", True),
                "error": result.get("error"),
                "metadata": result.get("metadata", {}),
            })
            
            return {
                "agent_results": agent_results,
                "messages": result.get("new_messages", []),
                "tool_results": state.get("tool_results", []) + result.get("tool_results", []),
            }
            
        agent_node.__name__ = f"node_{agent.name}"
        return agent_node

    async def _synthesize_node(self, state: AgentState) -> dict[str, Any]:
        """Synthesize final response using Output Synthesizer Agent."""
        logger.info("Executing synthesize node...")
        from agents.output_synthesizer.agent import OutputSynthesizerAgent

        synthesizer = OutputSynthesizerAgent()
        result = await synthesizer.execute(state)

        return {
            "final_response": result.get("final_response"),
            "output_type": result.get("output_type", "chat"),
            "is_complete": True,
        }

    # ── Routing logic ──

    def _route_from_supervisor(self, state: AgentState) -> str:
        """Route to appropriate subagent or END."""
        if state.get("is_complete") or not state.get("needs_agent"):
            return "__end__"

        next_agent = state.get("next_agent")
        if next_agent and next_agent in self._agents:
            return next_agent

        return "__end__"

    def get_compiled_graph(self):
        """Get the compiled graph."""
        if self._compiled is None:
            self.build()
        return self._compiled


# Singleton
agent_graph = AgentGraph()
