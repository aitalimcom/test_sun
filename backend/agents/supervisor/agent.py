import json
import logging
import re
from typing import Any
from langchain_core.messages import SystemMessage, HumanMessage
from core.agent import BaseAgent
from core.state import AgentState
from prompts.templates.supervisor import SUPERVISOR_SYSTEM_PROMPT, SUPERVISOR_ROUTING_PROMPT

logger = logging.getLogger(__name__)


class SupervisorAgent(BaseAgent):
    """Main routing and coordination agent.

    Classifies intent and delegates query to specialised domain agents.
    """

    name = "supervisor"
    description = "कृषि सेवा AI सुपरवाइजर - किसानको प्रश्न वर्गीकरण र उपयुक्त शाखामा पठाउने कार्य"
    model_preference = "routing"  # Lightweight model for quick classification

    @property
    def system_prompt(self) -> str:
        return SUPERVISOR_SYSTEM_PROMPT

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Executing supervisor intent routing...")
        
        # Determine the text context to classify
        orig_query = state.get("normalized_query", "")
        enriched_ctx = state.get("processed_input", {}).get("enriched_context", orig_query)

        # Build routing query prompt
        user_prompt = SUPERVISOR_ROUTING_PROMPT.format(
            query=orig_query,
            context=enriched_ctx,
        )

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()

            parsed = self._parse_json(content)
            if not parsed:
                # If JSON parsing failed, return generic greeting or direct response
                logger.warning("Supervisor routing returned invalid JSON. Falling back to direct chat.")
                return {
                    "intent": None,
                    "next_agent": None,
                    "dispatch_query": orig_query,
                    "needs_agent": False,
                    "is_complete": True,
                    "final_response": {
                        "output_type": "chat",
                        "message_np": content or "नमस्ते! म तपाईंलाई कसरी मद्दत गर्न सक्छु?",
                        "suggestions": ["मौसम कस्तो छ?", "बाली उपचार"],
                        "agent_trace": [{"agent_name": self.name, "success": True}],
                    },
                    "new_messages": [{"role": "assistant", "content": content}],
                }

            intent = parsed.get("intent")
            dispatch_query = parsed.get("dispatch_query", orig_query)
            direct_response = parsed.get("direct_response", "")

            # If there's an agent to route to
            if intent:
                logger.info(f"Supervisor decided to route to agent: {intent}")
                return {
                    "intent": intent,
                    "next_agent": intent,
                    "dispatch_query": dispatch_query,
                    "needs_agent": True,
                    "is_complete": False,
                    "new_messages": [],
                }
            
            # Handling directly
            logger.info("Supervisor decided to handle request directly.")
            return {
                "intent": None,
                "next_agent": None,
                "dispatch_query": None,
                "needs_agent": False,
                "is_complete": True,
                "final_response": {
                    "output_type": "chat",
                    "message_np": direct_response or "नमस्ते! म तपाईंलाई कसरी मद्दत गर्न सक्छु?",
                    "suggestions": ["बालीको रोग", "बजार भाउ"],
                    "agent_trace": [{"agent_name": self.name, "success": True}],
                },
                "new_messages": [{"role": "assistant", "content": direct_response}],
            }

        except Exception as e:
            logger.error(f"Supervisor routing failed: {e}")
            error_msg = "माफ गर्नुहोस्, किसान मित्र। प्रणालीमा केही प्राविधिक समस्या आयो। कृपया पुनः प्रयास गर्नुहोस्।"
            return {
                "intent": None,
                "next_agent": None,
                "dispatch_query": None,
                "needs_agent": False,
                "is_complete": True,
                "final_response": {
                    "output_type": "chat",
                    "message_np": error_msg,
                    "suggestions": ["मौसम", "बजार भाउ"],
                    "agent_trace": [{"agent_name": self.name, "success": False, "error": str(e)}],
                },
                "new_messages": [{"role": "assistant", "content": error_msg}],
            }

    def _parse_json(self, text: str) -> dict | None:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
            
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return None
