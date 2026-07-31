"""Alerts and notifications database."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from db.base import FileDB
from config import settings


class AlertsDB(FileDB):
    """Manages active agricultural or system alerts."""

    def __init__(self) -> None:
        super().__init__(Path(settings.database_root) / "alerts", collection_name="alerts")

    def create_alert(
        self,
        title: str,
        severity: str,  # "info" | "warning" | "danger"
        description: str = "",
        source: str = "system",
    ) -> dict[str, Any]:
        """Create a new alert record."""
        alert_id = f"alert-{uuid.uuid4().hex[:12]}"
        record = {
            "id": alert_id,
            "title": title,
            "severity": severity,
            "description": description,
            "source": source,
            "active": True,
            "resolved_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.save(alert_id, record)
        return record

    def list_active_alerts(self) -> list[dict[str, Any]]:
        """List active alerts."""
        alerts = self.list_all()
        return [a for a in alerts if a.get("active", True)]

    def resolve_alert(self, alert_id: str) -> dict[str, Any] | None:
        """Mark an alert as resolved."""
        alert = self.get(alert_id)
        if not alert:
            return None
        alert["active"] = False
        alert["resolved_at"] = datetime.now(timezone.utc).isoformat()
        self.save(alert_id, alert)
        return alert


# Singleton
alerts_db = AlertsDB()
