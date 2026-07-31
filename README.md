# KrishiMitra (कृषिमित्र) — Multi-Agent Agricultural Ecosystem

KrishiMitra is a bilingual (Nepali/English), multimodal, multi-agent AI system designed to empower smallholder farmers in Nepal. It combines sensor telemetry (IoT), real-time weather forecasting, mandi market pricing, local crop directories (RAG), and automatic document OCR (citizenship card parsing) into a single system, paired with a government administration dashboard.

---

## Project Structure

```text
hackathon/
├── backend/                # FastAPI application & Multi-Agent orchestration
│   ├── agents/             # 15 specialized agents + supervisor + output synthesizer
│   ├── core/               # State schemas, LangGraph configs, Multimodal preprocessors
│   ├── db/                 # File-system database CRUD wrappers
│   ├── data/               # Mock datasets & seed scripts (NPK, weather, market, wiki)
│   ├── routes/             # API routing (chat, ocr, doctor, market, weather, iot, etc.)
│   ├── services/           # External service wrappers (ChromaDB RAG, DuckDuckGo search)
│   ├── config.py           # App settings (Pydantic Settings v2)
│   ├── cli.py              # Developer workflow CLI
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # Astro 5 + Bootstrap 5 Admin Panel
│   ├── src/
│   │   ├── pages/          # Astro pages (Dashboard, schemes, reports, registration)
│   │   └── layouts/        # Layout frameworks (Bootstrap + HTML wrapper templates)
│   └── package.json        # Frontend configuration
│
└── database/               # Flat-file database collections (JSON files & CSVs)
    ├── chat_history/       # Chat session history
    ├── csv/                # Weather, price history & IoT telemetry logs
    ├── diagnoses/          # Crop health diagnoses
    ├── feedback/           # Audit reviews for government portals
    ├── iot/                # Registered sensor details
    ├── knowledge/          # Markdown documents (guides, disease facts)
    └── market_prices/      # Kalimati crop prices
```

---

## 1. Backend Service (FastAPI + LangGraph)

The backend is built around a custom **LangGraph** state machine executing a supervisor coordinator routing patterns across 15 specialized micro-agents.

### Configuration (`.env`)
Create `backend/.env` (or set environment variables) using [`.env.example`](file:///.env.example):
```bash
# default AI model provider: "ollama" or "google_ai_studio"
DEFAULT_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=gemma4:e2b

# OCR extraction agent settings (OpenRouter)
OPENROUTER_API_KEY=your-openrouter-key-here
OPENROUTER_MODEL=google/gemma-4-31b-it

# Database root directory
DATABASE_ROOT=../database
```

### Installation & Run
1. Install Python 3.10+ dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Developer CLI (`cli.py`)
To improve developer experience, we created a terminal utility. Run it from `backend/`:
- **Inspecting database status**:
  ```bash
  python cli.py status
  ```
- **Seeding mock files & RAG index**:
  ```bash
  python cli.py seed
  ```
- **Interactive multi-agent chat session**:
  ```bash
  python cli.py chat
  ```
- **Testing AI model loading**:
  ```bash
  python cli.py test-ai
  ```

---

## 2. Frontend Application (Astro 5)

The frontend is an Astro v5 application styled with Bootstrap v5.

### Key Pages
- **ड्यासबोर्ड (Dashboard)** (`/`): Visualizes overall system metrics (registered farmers, active schemes, notifications, pending approvals).
- **किसान दर्ता (Farmer Registration)** (`/farmer/register`):
  - Includes **नागरिकता OCR (Citizenship OCR)** powered by **Gemma 4 Vision** via OpenRouter.
  - Allows drag-and-drop or test image upload (Front/Back) to parse `first_name`, `last_name`, `citizenship_number`, `gender`, `dob`, `address`, and `father_name`.
  - Autofills the form with high-confidence AI suggestions.
- **योजनाहरू (Schemes)** (`/schemes`): Lists current subsidy schemes.
- **अभिलेख (Records)** (`/farmer/records`): Inspects individual land size, crops type, and history.

### Installation & Run
1. Install Bun (or npm) dependencies:
   ```bash
   cd frontend
   bun install   # or npm install
   ```
2. Start the development server (proxies `/api` routes to backend on port 8000):
   ```bash
   bun run dev   # or npm run dev
   ```
   Open `http://localhost:4321` in your browser.

---

## 3. Database Layer (Flat-Files & Vector RAG)

All data is stored in the `database/` root folder in clean flat-file structures. No complex SQL installation is needed.

- **Flat-file JSON Collections**: Located under `database/chat_history/`, `database/diagnoses/`, `database/tasks/`, and `database/feedback/`. Saves structures as lightweight JSON objects.
- **Tabular Databases**: Historical weather logs, mandi rates, and sensor telemetry values are structured in CSV sheets (`database/csv/`), queryable by the **Table Query Agent** using Pandas.
- **RAG Knowledge Base**: Agricultural wiki directories (`database/knowledge/`) indexed into **ChromaDB** using HuggingFace sentence embeddings for semantic retrieval.
