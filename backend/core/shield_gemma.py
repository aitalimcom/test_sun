"""
ShieldGemma Agricultural Safety & Guardrail Filter Module.
Evaluates user prompts and LLM answers for safety, PII exposure, and agricultural non-toxicity.
Returns YES (Safe) or NO (Unsafe) with safety rationale.
"""

from __future__ import annotations

import logging
import re
from core.model_registry import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

SHIELD_SYSTEM_PROMPT = """You are ShieldGemma, an agricultural safety and guardrail evaluator for Krishi Sewa.
Your job is to assess farmer inputs and AI responses for safety, dangerous chemical misuse, toxicity, and PII protection.

CRITICAL EVALUATION RULES:
1. SAFE (YES): Normal agricultural questions, crop disease symptoms, Mandi prices, fertilizer calculation, weather, general farming advice.
2. UNSAFE (NO): Advice on dangerous banned chemical poisons for self-harm, hate speech, illegal land grabbing, or un-sanitized citizen PII exposure.

Respond ONLY in valid JSON format:
{
  "is_safe": true | false,
  "verdict": "YES" | "NO",
  "explanation_np": "नेपालीमा सुरक्षा व्याख्या"
}"""


async def evaluate_safety(text: str) -> dict[str, Any]:
    """Evaluate input text for agricultural safety using Gemma 4 Shield filter."""
    if not text or len(text.strip()) == 0:
        return {"is_safe": True, "verdict": "YES", "explanation_np": "सुरक्षित"}

    try:
        llm = get_llm("routing")
        messages = [
            SystemMessage(content=SHIELD_SYSTEM_PROMPT),
            HumanMessage(content=f"Evaluate this text: {text}")
        ]
        resp = await llm.ainvoke(messages)
        content = resp.content.strip()

        match = re.search(r"\{[\s\S]*\}", content)
        if match:
            import json
            parsed = json.loads(match.group(0))
            return {
                "is_safe": parsed.get("is_safe", True),
                "verdict": parsed.get("verdict", "YES"),
                "explanation_np": parsed.get("explanation_np", "सुरक्षित सामग्री"),
            }
    except Exception as e:
        logger.warning(f"ShieldGemma evaluation fallback: {e}")

    return {"is_safe": True, "verdict": "YES", "explanation_np": "सुरक्षित"}
