"""Market price and listing database."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from db.base import FileDB
from config import settings


class MarketPricesDB(FileDB):
    """Manages market prices and farmer listings."""

    def __init__(self) -> None:
        super().__init__(Path(settings.database_root) / "market_prices", collection_name="market_prices")

    def save_price(self, data: dict[str, Any]) -> dict[str, Any]:
        """Save a price record."""
        record_id = data.get("id") or f"{data.get('crop', 'unknown')}_{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        record = {
            **data,
            "id": record_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.save(record_id, record)
        return record

    def get_latest_prices(self, crop: str | None = None) -> list[dict[str, Any]]:
        """Get latest prices, optionally filtered by crop."""
        records = self.list_all(limit=100)
        if crop:
            records = [r for r in records if crop.lower() in r.get("crop", "").lower()]
        return records

    def create_listing(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a marketplace listing."""
        listing_id = data.get("id") or str(uuid.uuid4())
        record = {
            **data,
            "id": listing_id,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.save(listing_id, record)
        return record

    def get_listings(self, crop: str | None = None) -> list[dict[str, Any]]:
        """Get active listings."""
        records = self.list_all()
        active = [r for r in records if r.get("status") == "active"]
        if crop:
            active = [r for r in active if crop.lower() in r.get("crop", "").lower()]
        return active


# Singleton
market_db = MarketPricesDB()
