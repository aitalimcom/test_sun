"""Developer CLI Utility — Interactive tools for testing and seeding KrishiMitra.

Usage:
  python cli.py [command]

Commands:
  chat       Start an interactive chat session with the multi-agent graph.
  seed       Generate mock databases and run the RAG vector store indexer.
  test-ai    Test local Ollama availability and show downloaded models.
  status     Inspect the status of database collections and active alerts.
"""

import sys
import asyncio
import json
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from config import settings
from core.graph import agent_graph
from core.state import create_initial_state
from agents.registry import initialize_graph, get_all_agents
from db.knowledge import knowledge_db
from db.tasks import tasks_db
from db.market_prices import market_db
from db.alerts import alerts_db
from db.iot_devices import iot_devices_db


async def run_chat():
    """Start an interactive chat CLI."""
    print("\n=== KrishiMitra Developer Chat CLI ===")
    print("Initializing Multi-Agent Graph...")
    initialize_graph()
    
    session_id = "cli-session-dev"
    print("Ready! Type 'exit' or 'quit' to stop.")
    print("--------------------------------------")
    
    while True:
        try:
            query = input("\nकिसान मित्र (You): ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit"):
                break
                
            # Initialize State
            state = create_initial_state(
                user_message=query,
                session_id=session_id,
                language="ne-NP"
            )
            
            print("Processing graph execution...")
            final_state = await agent_graph.run(state)
            
            final_response = final_state.get("final_response") or {}
            message_np = final_response.get("message_np", "प्रतिक्रिया पाउन सकिएन।")
            output_type = final_state.get("output_type", "chat")
            agent_trace = final_response.get("agent_trace", [])
            tasks = final_response.get("tasks")
            alerts = final_response.get("alerts")
            
            print(f"\nकृषिमित्र (AI) [{output_type.upper()}]: {message_np}")
            
            if tasks:
                print(f"Suggested Tasks: {json.dumps(tasks, ensure_ascii=False)}")
            if alerts:
                print(f"Urgent Alerts: {json.dumps(alerts, ensure_ascii=False)}")
                
            # Print routing execution trace
            trace_str = " -> ".join([t["agent_name"] for t in agent_trace])
            print(f"Agent Trace: {trace_str}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error executing chat turn: {e}")


async def run_seed():
    """Seed database mocks and index markdown files."""
    print("\n=== Seeding Database & Rebuilding RAG ===")
    
    from data.market_mock import seed_market_prices
    from data.weather_mock import seed_weather_history
    from data.seed_knowledge import seed_and_index_knowledge
    
    print("1. Seeding market price mocks...")
    seed_market_prices()
    
    print("2. Seeding weather history CSV...")
    seed_weather_history()
    
    print("3. Seeding RAG knowledge base markdown wiki docs & indexing...")
    await seed_and_index_knowledge()
    
    print("Seeding complete!")


async def run_test_ai():
    """Test connection to local Ollama and list models."""
    print("\n=== Testing local AI connectivity ===")
    try:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=settings.gemma_model, base_url=settings.ollama_base_url)
        print(f"Ollama Endpoint: {settings.ollama_base_url}")
        print(f"Checking model tag: '{settings.gemma_model}'...")
        
        # Short quick call
        resp = await llm.ainvoke("नमस्ते")
        print(f"Ollama response successfully: '{resp.content.strip()}'")
        
    except Exception as e:
        print(f"Ollama connection error: {e}")
        print("Please ensure Ollama is running and the model tag is pulled locally.")


def run_status():
    """Inspect DB counts and status."""
    print("\n=== Inspecting Database Collections ===")
    print(f"Database Directory: {Path(settings.database_root).resolve()}")
    print(f"RAG Wiki files: {knowledge_db.get_stats()}")
    print(f"Market prices tracked: {len(market_db.list_all())}")
    print(f"Active warnings/alerts: {len(alerts_db.list_active_alerts())}")
    print(f"Registered IoT probes: {len(iot_devices_db.list_devices())}")
    print(f"Farmer tasks checklist: {len(tasks_db.list_tasks())}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()
    if cmd == "chat":
        asyncio.run(run_chat())
    elif cmd == "seed":
        asyncio.run(run_seed())
    elif cmd == "test-ai":
        asyncio.run(run_test_ai())
    elif cmd == "status":
        run_status()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
