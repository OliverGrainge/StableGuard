# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

StableGuard (internally EquiGuard) is a vision monitoring system for equine yards. Edge cameras capture horse images; a backend uses Vision Language Models (VLMs) to identify horses, classify behavior, and build activity timelines. The MVP uses manual image upload rather than live feeds.

## Commands

### Backend
```bash
cd backend
uv sync                                    # Install dependencies
uv run uvicorn app.main:app --reload       # Start API at http://127.0.0.1:8000
```

### Frontend (React — primary)
```bash
cd web
npm install                                # Install dependencies
npm run dev                                # Start dev server at http://localhost:5173
npm run build                              # Production build
```

### Frontend (Streamlit — legacy)
```bash
cd frontend
uv sync                                    # Install dependencies
uv run streamlit run app.py                # Start dashboard at http://localhost:8501
```

### Reset Data
```bash
rm -f backend/equiguard.db                 # Delete SQLite DB
rm -rf backend/uploads                     # Delete uploaded images
```

No test suite, linter, or migration system exists yet. Swagger UI is at `/docs`.

## Architecture

Two independent Python apps sharing no code:

- **Backend** (`backend/`): FastAPI REST API on port 8000. Synchronous SQLAlchemy with SQLite. All routes under `/api`. Images stored on disk in `uploads/` with UUID filenames; paths saved in DB.
- **Frontend** (`web/`): React + TypeScript SPA built with Vite, Tailwind CSS v4, and shadcn/ui. Uses react-router-dom for routing and @tanstack/react-query for data fetching. Vite proxies `/api`, `/uploads`, and `/health` to the backend. Key dirs: `src/api/` (fetch client + types), `src/hooks/` (React Query hooks), `src/pages/` (route pages), `src/components/` (UI components).
- **Frontend (legacy)** (`frontend/`): Single-file Streamlit dashboard (`app.py`) that calls the backend API via `requests`. Set `EQUIGUARD_API_URL` to override the default API base URL.

### Backend Key Components

- `app/config.py` — Pydantic Settings; all config from env vars (see table below)
- `app/models.py` — Three ORM models: **Horse**, **Location**, **Detection** (with foreign keys and indexes)
- `app/schemas.py` — Pydantic request/response schemas
- `app/vlm_service.py` — VLM provider abstraction (mock, anthropic, openai, ollama) using LangChain structured output
- `app/horse_identifier.py` — Simple name-matching logic to identify horses from scene descriptions
- `app/routes/` — Resource-based route modules: `horses.py`, `locations.py`, `detections.py`
- `app/main.py` — App setup, CORS (open), startup hook creates DB tables, mounts `/uploads` static files
- `app/database.py` — SQLAlchemy engine and session factory (`get_db` dependency)

### Detection Flow

1. Image uploaded to `POST /api/detections/analyze?location_id=`
2. `vlm_service.analyze_scene()` sends base64 image to VLM, gets structured action + confidence
3. `horse_identifier` matches scene description against registered horse names
4. Detection record saved with horse_id (nullable if unmatched), action, confidence

## Environment Variables (Backend)

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite:///./equiguard.db` | DB connection |
| `UPLOADS_DIR` | `./uploads` | Image storage path |
| `USE_MOCK_VLM` | `true` | Force mock VLM provider |
| `VLM_PROVIDER` | `mock` | `mock`, `anthropic`, `openai`, `ollama` |
| `VLM_MODEL` | `claude-3-5-sonnet-latest` | Model name per provider |
| `ANTHROPIC_API_KEY` | — | Required for Anthropic provider |
| `OPENAI_API_KEY` | — | Required for OpenAI provider |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `CONFIDENCE_THRESHOLD` | `0.35` | Min confidence for horse match |

## Conventions

- Package manager is **uv** (not pip/poetry)
- Python 3.11+
- Backend uses synchronous FastAPI (no async/await in routes)
- No authentication; open CORS
- DB tables auto-created on startup via `Base.metadata.create_all`; no migration framework
- Sample test images in `assets/` (kenny1-3.jpeg, phillip1-2.jpeg)
