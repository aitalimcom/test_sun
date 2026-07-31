"""
Hash-Based Caching System for ASR Audio Transcriptions and TTS Speech Audio.
Uses SHA-256 / MD5 hashing to cache speech transcriptions and audio payloads.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CACHE_DIR = Path("database/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
ASR_CACHE_FILE = CACHE_DIR / "asr_cache.json"
TTS_CACHE_FILE = CACHE_DIR / "tts_cache.json"


def _load_cache(file_path: Path) -> dict[str, Any]:
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_cache(file_path: Path, data: dict[str, Any]) -> None:
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def compute_hash(data: str | bytes) -> str:
    """Compute SHA-256 hash for input string or byte payload."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def get_asr_cache(audio_bytes: bytes) -> str | None:
    """Get cached ASR transcript for audio byte payload."""
    key = compute_hash(audio_bytes)
    cache = _load_cache(ASR_CACHE_FILE)
    return cache.get(key)


def set_asr_cache(audio_bytes: bytes, transcript: str) -> None:
    """Cache ASR transcript for audio byte payload."""
    key = compute_hash(audio_bytes)
    cache = _load_cache(ASR_CACHE_FILE)
    cache[key] = transcript
    _save_cache(ASR_CACHE_FILE, cache)


def get_tts_cache(text: str) -> str | None:
    """Get cached TTS audio base64 payload for Devanagari text."""
    key = compute_hash(text.strip().lower())
    cache = _load_cache(TTS_CACHE_FILE)
    return cache.get(key)


def set_tts_cache(text: str, audio_b64: str) -> None:
    """Cache TTS audio base64 payload for Devanagari text."""
    key = compute_hash(text.strip().lower())
    cache = _load_cache(TTS_CACHE_FILE)
    cache[key] = audio_b64
    _save_cache(TTS_CACHE_FILE, cache)
