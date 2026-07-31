# Krishi Sewa (कृषि सेवा) — Government Agriculture Admin Panel

Krishi Sewa is a bilingual (Nepali/English) government agriculture administration system with IoT monitoring, powered by Gemma 4 AI agents. It combines IoT device management, sensor telemetry, OCR-based farmer registration, and a multi-agent chat system into a single admin panel.

---

## Project Structure

```text
hackathon/
├── backend/                    # FastAPI application
│   ├── agents/                 # AI agents (Gemma 4 via OpenRouter)
│   │   ├── iot_device/         # Agent 1: Add-device configuration
│   │   ├── iot_control/        # Agent 2: Device control & scheduling
│   │   ├── iot_monitor/        # Agent 3: Threshold monitoring & alerts
│   │   └── ocr/                # Citizenship OCR (vision)
│   ├── core/
│   │   └── cron.py             # Background cron scheduler
│   ├── db/
│   │   └── iot_db.py           # CSV-based IoT database layer
│   ├── data/
│   │   └── iot_defaults.py     # Sensor/actuator type definitions
│   ├── models/
│   │   └── iot.py              # Pydantic models for IoT API
│   ├── routes/
│   │   ├── iot.py              # IoT REST API (devices, telemetry, alerts)
│   │   ├── iot_chat.py         # Chat endpoints for both agents
│   │   └── iot_cron.py         # Cron job management API
│   ├── config.py               # App settings
│   └── main.py                 # FastAPI entry point
│
├── frontend/                   # Astro 5 + Bootstrap 5.3 Admin Panel
│   └── src/
│       ├── layouts/
│       │   └── AdminLayout.astro   # Sidebar with IoT accordion
│       └── pages/
│           ├── index.astro         # Dashboard
│           ├── iot/
│           │   ├── index.astro     # IoT dashboard (devices, chat, cron)
│           │   └── [id].astro      # Device detail (gauges, controls, chat)
│           └── farmer/             # Farmer management
│
└── database/
    └── iot/                    # CSV-based IoT data
        ├── devices.csv         # Registered devices
        ├── telemetry_*.csv     # Per-device sensor readings
        ├── alerts.csv          # Active/resolved alerts
        └── schedules.csv       # Device schedules
```

---

## 1. Backend (FastAPI)

### Configuration (`.env`)
```bash
# OCR agent (OpenRouter)
OPENROUTER_API_KEY=your-key
OPENROUTER_MODEL=google/gemma-4-31b-it

# Database
DATABASE_ROOT=../database

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

### Run
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

---

## 2. Frontend (Astro 5 + Bootstrap 5.3)

### Key Pages
- `/` — Dashboard with stat cards and recent activity
- `/iot` — IoT dashboard: device grid, add-device chat, cron agents, alerts
- `/iot/{id}` — Device detail: live sensor gauges, actuator controls, control chat, schedules
- `/farmer` — Farmer management
- `/farmer/register` — Farmer registration with OCR
- `/schemes`, `/reports`, `/settings` — Government admin pages

### Run
```bash
cd frontend
bun install
bun run dev    # Opens http://localhost:4321
```

---

## 3. IoT Monitoring Station

### Architecture
Three Gemma 4 agents (via OpenRouter) power the IoT system:

| Agent | Endpoint | Purpose |
|-------|----------|---------|
| **iot_device** | `POST /api/iot/chat/add-device` | User describes device → generates config + ESP32 code |
| **iot_control** | `POST /api/iot/chat/control/{id}` | Actuator commands, scheduling, summaries |
| **iot_monitor** | Cron (hourly) | Threshold checks → alerts → tasks |

### Sensors (float-priority)
| Sensor | Unit | Pin | Range |
|--------|------|-----|-------|
| temperature | °C | A0 | -10 to 60 |
| humidity | % | A1 | 0-100 |
| co2 | ppm | A2 | 0-2000 |
| moisture | % | A3 | 0-100 |
| ph | pH | A4 | 0-14 |
| light | lux | A5 | 0-100000 |
| pressure | hPa | I2C | 300-1100 |
| rainfall | mm | D8 | 0-500 |

### Actuators
| Actuator | Type | Pin | Control |
|----------|------|-----|---------|
| pump | toggle | D2 | on/off |
| ac | range | D3 | 15-40°C desired temp |
| light | toggle | D4 | on/off |
| fan | toggle | D5 | on/off |
| valve | toggle | D6 | open/close |
| heater | range | D7 | 15-45°C |

### API Endpoints
```
GET    /api/iot/devices                    — List all devices
POST   /api/iot/devices                    — Register new device
GET    /api/iot/devices/{id}               — Get device detail
PUT    /api/iot/devices/{id}               — Update device
DELETE /api/iot/devices/{id}               — Delete device

GET    /api/iot/device/{id}/telemetry      — Get telemetry history
POST   /api/iot/device/{id}/telemetry      — Post new reading
POST   /api/iot/device/{id}/sync           — Sync (generates mock data)
GET    /api/iot/device/{id}/config         — Get device config
POST   /api/iot/device/{id}/config         — Update config
POST   /api/iot/device/{id}/action         — Trigger actuator

GET    /api/iot/alerts                     — List alerts
POST   /api/iot/alerts                     — Create alert
POST   /api/iot/alerts/{id}/resolve        — Resolve alert

GET    /api/iot/schedules                  — List schedules
POST   /api/iot/schedules                  — Create schedule
DELETE /api/iot/schedules/{id}             — Delete schedule

POST   /api/iot/chat/add-device            — Add-device chat (Agent 1)
POST   /api/iot/chat/control/{id}          — Control chat (Agent 2)
POST   /api/iot/chat/control               — General control chat

GET    /api/iot/cron/jobs                  — List cron jobs
POST   /api/iot/cron/jobs/{name}/toggle    — Enable/disable job
POST   /api/iot/cron/trigger/{name}        — Manual trigger

GET    /api/iot/types/sensors              — Sensor type definitions
GET    /api/iot/types/actuators            — Actuator type definitions
GET    /api/iot/types/devices              — Device presets
```

### Cron Jobs
| Job | Interval | Description |
|-----|----------|-------------|
| `iot_monitor` | 1 hour | Check all sensors against thresholds, generate alerts |
| `weather_sync` | 30 seconds | Sync weather station telemetry (demo interval) |

### CSV Database Format
- `database/iot/devices.csv` — Device registry (device_id, name, type, location, sensors_json, actuators_json)
- `database/iot/telemetry_{device_id}.csv` — Per-device readings (timestamp + float values)
- `database/iot/alerts.csv` — Alert history (metric, value, threshold, severity)
- `database/iot/schedules.csv` — Scheduled actions (cron_expr, action, params)

### Default Device: Weather Station
- Device ID: `weather-001`
- Sensors: temperature, humidity, co2
- Auto-syncs every 30 seconds with mock data
- Sync button on dashboard for manual trigger
