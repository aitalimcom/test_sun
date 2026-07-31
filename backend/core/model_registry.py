import logging
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from config import settings

logger = logging.getLogger(__name__)


def get_llm(task: str | None = None) -> BaseChatModel:
    """Factory to get the correct LangChain ChatModel based on the task and provider settings."""
    # Determine the model name based on task preference
    model_name = None
    if task == "vision":
        model_name = settings.vision_model or settings.ollama_default_model
    elif task == "audio":
        model_name = settings.audio_model or settings.ollama_default_model
    elif task == "routing":
        model_name = settings.routing_model or settings.ollama_default_model
    elif task == "reasoning":
        model_name = settings.reasoning_model or settings.ollama_default_model

    # Default fallback
    if not model_name:
        model_name = settings.gemma_model or settings.ollama_default_model

    # Check the provider
    provider = settings.default_provider.lower()

    if provider == "openrouter":
        api_key = settings.openrouter_api_key
        if not api_key:
            import os
            api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key:
            try:
                from langchain_openai import ChatOpenAI
                openrouter_model = settings.openrouter_model or "google/gemma-4-31b-it"
                logger.info(f"Using OpenRouter provider with model: {openrouter_model}")
                return ChatOpenAI(
                    model=openrouter_model,
                    api_key=api_key,
                    base_url="https://openrouter.ai/api/v1",
                    temperature=0.7,
                )
            except Exception as e:
                logger.warning(f"OpenRouter initialization failed ({e}). Falling back.")
        else:
            logger.warning("OpenRouter API Key not found. Falling back to local Ollama.")
    
    if provider == "google_ai_studio" or provider == "google":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            # Map gemma4 tags to google names if necessary
            google_model_name = model_name
            if "gemma4" in model_name or "gemma-4" in model_name:
                google_model_name = settings.google_default_model or "gemma-2-9b-it"  # Fallback to a standard model name if not configured
            
            api_key = settings.google_api_key
            if not api_key:
                import os
                api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
                
            if not api_key:
                logger.warning("Google API Key not found. Falling back to local Ollama.")
            else:
                logger.info(f"Using Google AI Studio provider with model: {google_model_name}")
                return ChatGoogleGenerativeAI(
                    model=google_model_name,
                    google_api_key=api_key,
                    temperature=0.7,
                )
        except ImportError:
            logger.warning("langchain-google-genai is not installed. Falling back to local Ollama.")
    
    # Local Ollama Fallback
    logger.info(f"Using Ollama provider with model: {model_name}")
    return ChatOllama(
        model=model_name,
        base_url=settings.ollama_base_url,
        temperature=0.7,
    )
