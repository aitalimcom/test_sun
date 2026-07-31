"""Custom exceptions for KrishiMitra backend."""


class AgentError(Exception):
    """Base exception for agent-related errors."""

    def __init__(self, message: str, agent_name: str = "unknown"):
        self.agent_name = agent_name
        super().__init__(f"[{agent_name}] {message}")


class AgentTimeoutError(AgentError):
    """Agent took too long to respond."""

    def __init__(self, agent_name: str = "unknown", timeout: float = 30.0):
        super().__init__(f"Timed out after {timeout}s", agent_name)
        self.timeout = timeout


class AgentDispatchError(AgentError):
    """Failed to dispatch to a subagent."""

    def __init__(self, target_agent: str, reason: str = "dispatch failed"):
        super().__init__(f"Cannot dispatch to '{target_agent}': {reason}", "supervisor")


class GemmaConnectionError(Exception):
    """Cannot connect to Ollama/Gemma."""

    def __init__(self, url: str = "http://localhost:11434", reason: str = "connection refused"):
        self.url = url
        super().__init__(f"Gemma connection failed at {url}: {reason}")


class GemmaResponseError(Exception):
    """Gemma returned an invalid or unparseable response."""

    def __init__(self, detail: str = "invalid response format"):
        self.detail = detail
        super().__init__(f"Gemma response error: {detail}")


class RAGNotReadyError(Exception):
    """RAG vector store has not been initialized."""

    def __init__(self):
        super().__init__("RAG vector store not initialized. Call initialize() first.")


class DBError(Exception):
    """Base database error."""

    def __init__(self, collection: str, detail: str = "operation failed"):
        self.collection = collection
        super().__init__(f"DB error [{collection}]: {detail}")


class DBNotFoundError(DBError):
    """Record not found in database."""

    def __init__(self, collection: str, record_id: str):
        super().__init__(collection, f"Record '{record_id}' not found")
        self.record_id = record_id
