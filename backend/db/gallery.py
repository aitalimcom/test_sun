"""Visual crop disease gallery database."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from db.base import FileDB
from config import settings


class GalleryDB(FileDB):
    """Manages visual crop disease images, Nepali captions, and metadata tags."""

    def __init__(self) -> None:
        super().__init__(Path(settings.database_root) / "gallery", collection_name="gallery")

    def add_item(
        self,
        image_path: str,
        caption_np: str,
        crop_type: str = "potato",
        disease_tags: list[str] | None = None,
        visual_features: str = "",
        source_doc: str = "Manual Upload",
    ) -> dict[str, Any]:
        """Add a new gallery item."""
        gallery_id = f"gal-{uuid.uuid4().hex[:12]}"
        record = {
            "id": gallery_id,
            "image_path": image_path,
            "caption_np": caption_np,
            "crop_type": crop_type,
            "disease_tags": disease_tags or ["आलु रोग"],
            "visual_features": visual_features,
            "source_doc": source_doc,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.save(gallery_id, record)
        return record

    def list_gallery(self, crop_type: str | None = None) -> list[dict[str, Any]]:
        """List gallery items."""
        items = self.list_all()
        if crop_type:
            items = [i for i in items if i.get("crop_type", "").lower() == crop_type.lower()]
        return items


# Singleton
gallery_db = GalleryDB()
