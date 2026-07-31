from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List, Dict, Any


class Settings(BaseSettings):
    # ── Default Provider ──
    default_provider: str = "ollama"  # "ollama" or "google_ai_studio"

    # ── Ollama Settings ──
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "gemma4:e2b"

    # ── Google AI Studio Settings ──
    google_api_key: str = ""
    google_default_model: str = "gemma-4-12b"

    # ── Per-Task Model Configuration ──
    gemma_model: str = "gemma4:e2b"  # Compatibility with existing files
    vision_model: str = ""           # Override for vision/multimodal tasks (e.g. gemma4:e2b, gemma-4-12b)
    audio_model: str = ""            # Override for audio tasks
    routing_model: str = ""          # Override for routing (supervisor)
    reasoning_model: str = ""        # Override for deep advisory (thinking mode)

    # ── Server Settings ──
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:4321,http://localhost:3000"

    # ── OpenRouter (OCR Agent) ──
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemma-4-31b-it"

    # ── Database & API Keys ──
    database_root: str = "../database"
    openweather_api_key: str = ""

    @property
    def database_path(self) -> Path:
        return Path(self.database_root).resolve()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
