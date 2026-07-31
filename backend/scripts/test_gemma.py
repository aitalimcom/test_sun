"""
Test Gemma — Quick connection test
Run: python scripts/test_gemma.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from services.gemma_service import gemma


async def test():
    print("🧪 Testing Gemma connection...\n")
    print(f"Provider: {gemma.provider}")
    print(f"Model: {gemma.model}\n")

    try:
        response = await gemma.generate(
            prompt="What is rice blast disease? Answer in 2 sentences.",
            system_prompt="You are a farming expert.",
        )
        print(f"✅ Response:\n{response}")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure Ollama is running: ollama serve")
        print(f"And the model is pulled: ollama pull {gemma.model}")


if __name__ == "__main__":
    asyncio.run(test())
