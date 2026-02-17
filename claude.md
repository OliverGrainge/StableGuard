# StableGuard (EquiGuard) - Claude Project Guide

## Project Overview

StableGuard (internally branded EquiGuard) is a **vision monitoring system for equine yards**. Edge cameras capture images of horses in stables, pens, and exercise areas. A backend server uses Vision Language Models (VLMs) to analyze uploaded images for:

- **Horse identification** – Match horses against registered profiles using visual features
- **Action recognition** – Classify behavior (standing, walking, running, rolling, eating, etc.)
- **Activity tracking** – Store detections and build timelines per horse

The MVP uses manual image upload rather than live camera feeds.

---

## Architecture

- **Backend** (`backend/`): FastAPI REST API, SQLite, VLM integration (Anthropic, OpenAI, Ollama, or mock)
- **Frontend** (`frontend/`): Streamlit dashboard for data inspection, horse registration, location management, and detection analysis
- **Data**: SQLite DB + uploaded images in `backend/uploads/`

---

## Tech Stack

| Layer        | Technologies                          |
|-------------|----------------------------------------|
| Backend     | FastAPI, SQLAlchemy, Pydantic, Pillow  |
| VLM         | LangChain (Anthropic, OpenAI, Ollama)  |
| Frontend    | Streamlit, requests                    |
| Database    | SQLite                                 |
| Package mgr | uv                                     |

---

## Repo Structure

```
StableGuard/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app, routes, health check
│   │   ├── config.py         # Settings, env vars
│   │   ├── database.py       # SQLAlchemy engine, Base
│   │   ├── models.py         # Horse, Location, Detection
│   │   ├── schemas.py        # Pydantic request/response models
│   │   ├── vlm_service.py    # VLM provider abstraction
│   │   ├── horse_identifier.py  # Horse ID + action recognition logic
│   │   └── routes/
│   │       ├── horses.py     # Horse CRUD
│   │       ├── locations.py  # Location CRUD
│   │       └── detections.py # Analyze endpoint, timeline
│   ├── pyproject.toml
│   ├── uploads/              # Horse & detection images (created at runtime)
│   └── equiguard.db          # SQLite DB (created at runtime)
├── frontend/
│   ├── app.py                # Streamlit dashboard
│   └── pyproject.toml
├── assets/                   # Sample/test images
├── plan.md                   # Detailed MVP plan
└── claude.md                 # This file
```

---

## Running the Project

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

API: `http://127.0.0.1:8000`

### Frontend

```bash
cd frontend
uv sync
uv run streamlit run app.py
```

Dashboard: `http://localhost:8501`

Set `EQUIGUARD_API_URL` to override the API base URL (default: `http://127.0.0.1:8000`).

---

## Environment Variables (Backend)

| Variable             | Default                      | Description                          |
|----------------------|-----------------------------|--------------------------------------|
| `DATABASE_URL`       | `sqlite:///./equiguard.db`  | SQLite path                          |
| `UPLOADS_DIR`        | `./uploads`                 | Horse and detection image storage    |
| `USE_MOCK_VLM`       | `true`                      | Use mock VLM when `true`             |
| `VLM_PROVIDER`       | `mock`                      | `mock`, `anthropic`, `openai`, `ollama` |
| `VLM_MODEL`          | `claude-3-5-sonnet-latest`  | Model per provider                   |
| `ANTHROPIC_API_KEY`  | -                           | For Anthropic                        |
| `OPENAI_API_KEY`     | -                           | For OpenAI                           |
| `OLLAMA_BASE_URL`    | `http://localhost:11434`    | For Ollama                           |
| `CONFIDENCE_THRESHOLD` | `0.35`                    | Min confidence for horse match       |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check |
| POST | `/api/horses` | Register horse (multipart: name, description, image) |
| GET | `/api/horses` | List horses (newest first) |
| GET | `/api/horses/{id}` | Horse details + 20 recent detections |
| POST | `/api/locations` | Create location (JSON: name, description) |
| GET | `/api/locations` | List locations |
| POST | `/api/detections/analyze?location_id=` | Upload image, analyze, save detection (multipart: image) |
| GET | `/api/detections` | List detections (optional: horse_id, location_id, date) |
| GET | `/api/detections/{horse_id}/timeline` | Timeline for one horse |

---

## Conventions & Notes

1. **Backend**: FastAPI + synchronous SQLAlchemy; routes live under `/api`.
2. **VLM**: `vlm_service.py` abstracts providers; `horse_identifier.py` uses it for registration (visual description) and detection (match + action).
3. **Images**: Stored in `uploads/horses/` and `uploads/detections/`; paths are saved in the DB.
4. **Reset data**: Stop server, then `rm -f backend/equiguard.db` and optionally `rm -rf backend/uploads`.
5. **Frontend**: Single Streamlit `app.py`; reads from API; filters by horse_id, location_id, date.

---

## Key Files to Inspect

- `plan.md` – Full MVP design, phases, prompt strategy, schema
- `backend/app/vlm_service.py` – VLM provider switching
- `backend/app/horse_identifier.py` – Horse ID and action recognition logic
- `backend/app/routes/detections.py` – `/analyze` and timeline endpoints
