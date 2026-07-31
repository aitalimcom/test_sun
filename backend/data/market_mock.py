"""Generates price history CSV databases and updates market price collections."""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, timezone
from config import settings
from db.market_prices import market_db


def seed_market_prices() -> None:
    """Seed market prices collection with realistic rates."""
    crops_rates = [
        {"crop": "आलु (रातो)", "min_price": 60, "max_price": 70, "unit": "केजी", "market": "kalimati"},
        {"crop": "गोलभेडा (ठूलो)", "min_price": 80, "max_price": 95, "unit": "केजी", "market": "kalimati"},
        {"crop": "बन्दा", "min_price": 30, "max_price": 38, "unit": "केजी", "market": "kalimati"},
        {"crop": "काउली स्थानीय", "min_price": 70, "max_price": 82, "unit": "केजी", "market": "kalimati"},
        {"crop": "प्याज (सुकेको)", "min_price": 120, "max_price": 135, "unit": "केजी", "market": "kalimati"},
    ]
    
    for rate in crops_rates:
        market_db.save_price(rate)

    # Now create CSV database files
    csv_dir = Path(settings.database_root) / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)
    price_csv = csv_dir / "price_history.csv"
    
    # Generate 30 days price history for pandas queries
    data = []
    base_date = datetime.now(timezone.utc) - timedelta(days=30)
    for i in range(30):
        date_str = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        data.append({"date": date_str, "crop": "potato", "market": "kalimati", "min_price": 50 + (i * 0.5), "max_price": 60 + (i * 0.5)})
        data.append({"date": date_str, "crop": "tomato", "market": "kalimati", "min_price": 70 + (i * 0.8), "max_price": 85 + (i * 0.8)})
        
    df = pd.DataFrame(data)
    df.to_csv(price_csv, index=False)
