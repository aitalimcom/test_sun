"""Generates weather history CSV databases for dataframe querying."""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, timezone
from config import settings


def seed_weather_history() -> None:
    """Generate weather history CSV databases for tabular querying."""
    csv_dir = Path(settings.database_root) / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)
    weather_csv = csv_dir / "weather_history.csv"

    # Generate 30 days weather metrics
    data = []
    base_date = datetime.now(timezone.utc) - timedelta(days=30)
    for i in range(30):
        date_str = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        # Simulate temp cyclic patterns (22 to 32 degrees)
        temp = 24.0 + (i % 7) * 1.2
        humidity = 65 + (i % 5) * 4
        rainfall = 0.0 if i % 4 != 0 else 5.0 + (i % 3) * 4.2
        data.append({
            "date": date_str,
            "temp": temp,
            "humidity": humidity,
            "rainfall": rainfall
        })

    df = pd.DataFrame(data)
    df.to_csv(weather_csv, index=False)
