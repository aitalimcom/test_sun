from langchain_core.language_models import BaseChatModel
from core.model_registry import get_llm as registry_get_llm


def get_llm(model: str | None = None) -> BaseChatModel:
    """Compatibility wrapper that directs to core.model_registry.get_llm."""
    return registry_get_llm(task=None)
