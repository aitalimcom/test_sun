import json
import logging
import re
import uuid
from typing import Any
from langchain_core.messages import SystemMessage, HumanMessage
from core.agent import BaseAgent
from core.state import AgentState
from prompts.templates.output_synthesizer import OUTPUT_SYNTHESIZER_SYSTEM_PROMPT, OUTPUT_SYNTHESIZER_USER_PROMPT

logger = logging.getLogger(__name__)


class OutputSynthesizerAgent(BaseAgent):
    """Compiles subagent responses and outputs into structured formatted responses."""

    name = "output_synthesizer"
    description = "कृषि सेवा AI आउटपुट सिन्थेसाइजर - किसानको लागि अन्तिम नतिजा सम्पादन गर्ने कार्य"
    model_preference = "default"  # Use standard or slightly heavier model for quality synthesis

    @property
    def system_prompt(self) -> str:
        return OUTPUT_SYNTHESIZER_SYSTEM_PROMPT

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Synthesizing final output...")
        
        orig_query = state.get("normalized_query", "")
        processed = state.get("processed_input", {})
        multimodal_context = processed.get("enriched_context", orig_query)
        intent = state.get("intent", "general")
        agent_results = state.get("agent_results", [])
        tool_results = state.get("tool_results", [])

        # Create input prompt
        user_prompt = OUTPUT_SYNTHESIZER_USER_PROMPT.format(
            query=orig_query,
            multimodal_context=multimodal_context,
            intent=intent,
            agent_results=json.dumps(agent_results, ensure_ascii=False),
            tool_results=json.dumps(tool_results, ensure_ascii=False),
        )

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ]

        # Standard feedback ID generation for government portal
        feedback_id = f"feedback-{uuid.uuid4().hex[:12]}"

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()

            parsed = self._parse_json(content)
            if not parsed:
                logger.warning("Synthesizer failed to return valid JSON. Generating text fallback.")
                return {
                    "final_response": {
                        "output_type": "chat",
                        "message_np": content or "म तपाईंको प्रश्नको जवाफ तयार गर्न असमर्थ भएँ। कृपया फेरि प्रयास गर्नुहोस्।",
                        "tasks": None,
                        "alerts": None,
                        "report": None,
                        "suggestions": ["मुख्य पृष्ठ", "बाली उपचार"],
                        "agent_trace": self._build_agent_trace(state),
                        "feedback_id": feedback_id,
                    },
                    "output_type": "chat",
                }

            # Inject trace and feedback id
            final_res = {
                "output_type": parsed.get("output_type", "chat"),
                "message_np": parsed.get("message_np", ""),
                "tasks": parsed.get("tasks"),
                "alerts": parsed.get("alerts"),
                "report": parsed.get("report"),
                "suggestions": parsed.get("suggestions", ["मुख्य पृष्ठ"]),
                "agent_trace": self._build_agent_trace(state),
                "feedback_id": feedback_id,
            }

            return {
                "final_response": final_res,
                "output_type": final_res["output_type"],
            }

        except Exception as e:
            logger.error(f"Output synthesis failed: {e}")
            error_response = {
                "output_type": "chat",
                "message_np": "माफ गर्नुहोस्, किसान मित्र। अन्तिम जवाफ तयार गर्दा समस्या आयो।",
                "tasks": None,
                "alerts": None,
                "report": None,
                "suggestions": ["मौसम", "बजार भाउ"],
                "agent_trace": self._build_agent_trace(state, err=str(e)),
                "feedback_id": feedback_id,
            }
            return {
                "final_response": error_response,
                "output_type": "chat",
            }

    def _build_agent_trace(self, state: AgentState, err: str | None = None) -> list[dict[str, Any]]:
        trace = []
        # Add supervisor
        trace.append({"agent_name": "supervisor", "success": True})
        
        # Add subagents that ran
        for res in state.get("agent_results", []):
            trace.append({
                "agent_name": res.get("agent_name"),
                "success": res.get("success", True),
                "error": res.get("error"),
            })
            
        # Add synthesizer itself
        trace.append({
            "agent_name": self.name,
            "success": err is None,
            "error": err,
        })
        return trace

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
