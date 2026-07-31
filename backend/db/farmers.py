"""Farmer database class wrapping FileDB for database/farms storage."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from db.base import FileDB
from config import settings


class FarmerDB(FileDB):
    """Manages registered farmer profiles and farm metadata."""

    def __init__(self) -> None:
        super().__init__(Path(settings.database_root) / "farms", collection_name="farms")

    def save_farmer(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a farmer record."""
        farmer_id = data.get("id") or data.get("citizenship_no") or f"farmer_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        
        record = {
            "id": farmer_id,
            "full_name": data.get("full_name", ""),
            "citizenship_no": data.get("citizenship_no", ""),
            "phone": data.get("phone", ""),
            "district": data.get("district", ""),
            "palika": data.get("palika", ""),
            "ward": str(data.get("ward", "")),
            "land_size_ropani": float(data.get("land_size_ropani", 0.0)),
            "land_size_bigha": float(data.get("land_size_bigha", 0.0)),
            "crops": data.get("crops", []),
            "status": data.get("status", "active"),
            "updated_at": now,
            "created_at": data.get("created_at") or now,
        }
        self.save(farmer_id, record)
        return record

    def get_farmer(self, farmer_id: str) -> dict[str, Any] | None:
        """Get farmer details by ID."""
        return self.get(farmer_id)

    def list_farmers(self, district: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """List registered farmers, optionally filtered by district."""
        records = self.list_all(limit=limit)
        if district:
            records = [r for r in records if district.lower() in r.get("district", "").lower()]
        return records

    def update_farmer(self, farmer_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        """Update fields of an existing farmer record."""
        existing = self.get(farmer_id)
        if not existing:
            return None
        existing.update(updates)
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.save(farmer_id, existing)
        return existing

    def delete_farmer(self, farmer_id: str) -> bool:
        """Delete a farmer record."""
        return self.delete(farmer_id)


# Singleton instance
farmer_db = FarmerDB()
