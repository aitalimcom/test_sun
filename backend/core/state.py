from typing import TypedDict, Annotated, Literal, Any
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class ToolCallResult(TypedDict):
    """Result of a tool/subagent execution."""
    agent_name: str
    query: str
    result: str
    success: bool
    error: str | None
    latency_ms: float


class AgentMetadata(TypedDict):
    """Metadata about the conversation turn."""
    active_agent: str
    language: str
    session_id: str | None
    thinking_trace: str
    latency_ms: float
    model_used: str
    tokens_prompt: int
    tokens_completion: int


class AgentState(TypedDict):
    """The unified state shared across all agents in the LangGraph workflow."""
    
    # --- Conversation messages ---
    messages: Annotated[list[BaseMessage], add_messages]
    
    # --- Multimodal inputs & processed info ---
    original_input: dict[str, Any]       # {"text": str, "images": list[str], "audio_data": str}
    processed_input: dict[str, Any]      # {"normalized_text": str, "detected_language": str, "image_analyses": list}
    normalized_query: str                 # Devanagari Nepali query
    detected_language: str                # E.g. "ne-NP", "en-US", "hi-IN"
    image_analyses: list[dict[str, Any]]  # Classification/VQA outcomes for each image
    
    # --- Routing & Execution ---
    intent: str | None                    # E.g. "disease", "weather", "market", etc.
    next_agent: str | None                # Target agent for routing
    dispatch_query: str | None            # Prompt/query for subagent
    
    # --- Results accumulation ---
    agent_results: list[dict[str, Any]]   # Raw outputs from subagents
    tool_results: list[ToolCallResult]    # Outcomes of internal tool calls
    
    # --- Final Synthesized Response ---
    final_response: dict[str, Any] | None # Formatted final response
    output_type: Literal["chat", "task", "alert", "report"]
    
    # --- Status Flags & Session ---
    session_id: str | None
    metadata: AgentMetadata
    is_complete: bool
    needs_agent: bool
    error: str | None


def create_initial_state(
    user_message: str,
    session_id: str | None = None,
    images: list[str] | None = None,
    audio_data: str | None = None,
    language: str = "ne-NP",
    chat_history: list[BaseMessage] | None = None,
) -> AgentState:
    """Helper to initialize the AgentState."""
    return AgentState(
        messages=chat_history or [],
        original_input={
            "text": user_message,
            "images": images or [],
            "audio_data": audio_data,
        },
        processed_input={},
        normalized_query=user_message,
        detected_language=language,
        image_analyses=[],
        intent=None,
        next_agent=None,
        dispatch_query=None,
        agent_results=[],
        tool_results=[],
        final_response=None,
        output_type="chat",
        session_id=session_id,
        metadata={
            "active_agent": "supervisor",
            "language": language,
            "session_id": session_id,
            "thinking_trace": "",
            "latency_ms": 0.0,
            "model_used": "",
            "tokens_prompt": 0,
            "tokens_completion": 0,
        },
        is_complete=False,
        needs_agent=False,
        error=None,
    )
