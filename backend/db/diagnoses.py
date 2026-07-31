"""Diagnosis history database."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from db.base import FileDB
from config import settings


class DiagnosisDB(FileDB):
    """Manages crop diagnosis records."""

    def __init__(self) -> None:
        super().__init__(Path(settings.database_root) / "diagnoses", collection_name="diagnoses")

    def save_diagnosis(
        self,
        diagnosis_id: str,
        crop_type: str,
        result: dict[str, Any],
        image_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Save a diagnosis record."""
        record = {
            "id": diagnosis_id,
            "crop_type": crop_type,
            "result": result,
            "image_metadata": image_metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.save(diagnosis_id, record)
        return record

    def get_diagnosis(self, diagnosis_id: str) -> dict[str, Any] | None:
        """Get a diagnosis by ID."""
        return self.get(diagnosis_id)

    def list_diagnoses(self, limit: int = 20) -> list[dict[str, Any]]:
        """List recent diagnoses."""
        return self.list_all(limit=limit)

    def get_by_crop(self, crop_type: str) -> list[dict[str, Any]]:
        """Get all diagnoses for a specific crop."""
        return self.search("crop_type", crop_type)


# Singleton
diagnosis_db = DiagnosisDB()
