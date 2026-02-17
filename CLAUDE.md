# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

StableGuard (internally EquiGuard) is a vision monitoring system for equine yards. Edge cameras capture horse images; a backend uses a local ML service (VLM + visual embeddings) to classify horse behavior and identify individuals. The MVP uses manual image upload rather than live feeds.

## Commands

### API Service
```bash
cd api-service
uv sync                                    # Install dependencies
uv run uvicorn app.main:app --reload       # Start API at http://127.0.0.1:8000
```

### ML Service
```bash
cd ml-service
uv sync                                    # Install dependencies (torch, transformers, etc.)
MOCK_MODE=true uv run uvicorn app.main:app --port 8001 --reload   # Mock mode (no GPU needed)
uv run uvicorn app.main:app --port 8001    # Real models (requires GPU recommended)
```

### Web Service (React — primary)
```bash
cd web-service
npm install                                # Install dependencies
npm run dev                                # Start dev server at http://localhost:5173
npm run build                              # Production build
```

### Reset Data
```bash
rm -f api-service/equiguard.db             # Delete SQLite DB
rm -rf api-service/uploads                 # Delete uploaded images
```

No test suite, linter, or migration system exists yet. Backend Swagger UI at `/docs`. ML service Swagger UI at `http://localhost:8001/docs`.

## Architecture

Three independent services sharing no code:

- **API Service** (`api-service/`): FastAPI REST API on port 8000. Synchronous SQLAlchemy with SQLite. All routes under `/api`. Images stored on disk in `uploads/` with UUID filenames; paths saved in DB. No ML libraries — calls the ML service via HTTP (`httpx`). Horse identification is done locally via cosine similarity against stored embeddings.
- **ML Service** (`ml-service/`): FastAPI inference service on port 8001. Loads HuggingFace models at startup (VLM for action recognition, SigLIP for embeddings). Stateless — no DB, no file storage. Designed for GPU deployment; supports `MOCK_MODE=true` for development without GPU.
- **Web Service** (`web-service/`): React + TypeScript SPA built with Vite, Tailwind CSS v4, and shadcn/ui. Uses react-router-dom for routing and @tanstack/react-query for data fetching. Vite proxies `/api`, `/uploads`, and `/health` to the backend. Key dirs: `src/api/` (fetch client + types), `src/hooks/` (React Query hooks), `src/pages/` (route pages), `src/components/` (UI components).

### API Service Key Components

- `app/config.py` — Pydantic Settings; all config from env vars (see table below)
- `app/models.py` — Three ORM models: **Horse** (with `embedding` column), **Location**, **Detection** (with `vlm_model_id`, `embed_model_id` for MLOps tracking)
- `app/schemas.py` — Pydantic request/response schemas
- `app/ml_client.py` — HTTP client for the ML service (`MLClient`); mock mode returns deterministic fakes without calling the service
- `app/horse_identifier.py` — Cosine similarity matching, embedding serialize/deserialize
- `app/routes/` — Resource-based route modules: `horses.py`, `locations.py`, `detections.py`
- `app/main.py` — App setup, CORS (open), lifespan creates DB tables + runs migrations, mounts `/uploads` static files
- `app/database.py` — SQLAlchemy engine, session factory (`get_db`), `run_migrations()` for additive column migrations

### ML Service Key Components

- `app/config.py` — `pydantic-settings` BaseSettings; model IDs and device from env vars
- `app/registry.py` — `ModelRegistry` singleton: loads models once at startup, tracks metadata (model_id, revision, loaded_at, device)
- `app/models/vlm.py` — Qwen2-VL inference: `load_vlm()` + `analyze_action(bytes) → ActionResponse`
- `app/models/embedder.py` — SigLIP inference: `load_embedder()` + `generate_embedding(bytes) → EmbedResponse`
- `app/routes/action.py` — `POST /action`
- `app/routes/embed.py` — `POST /embed`
- `app/routes/health.py` — `GET /health`, `GET /models`

### Detection Flow

1. Image uploaded to `POST /api/detections/analyze?location_id=`
2. Backend calls `POST http://ml-service:8001/action` → `{action, confidence, description, model_id}`
3. Backend calls `POST http://ml-service:8001/embed` → `{embedding: float[], dim, model_id}`
4. Backend computes cosine similarity against all stored horse embeddings → best match
5. Detection record saved with `horse_id`, `action`, `confidence`, `vlm_model_id`, `embed_model_id`

### Horse Registration Flow

1. Image uploaded to `POST /api/horses`
2. Backend calls `POST http://ml-service:8001/embed` → embedding stored in `horse.embedding` (JSON in Text column)
3. `POST /api/horses/{id}/reembed` — regenerate one horse's embedding (use after deploying new model)
4. `POST /api/horses/reembed-all` — regenerate all horse embeddings

### MLOps Model Swap Workflow

1. Update `EMBED_MODEL_ID` (or `VLM_MODEL_ID`) in `ml-service/.env`
2. Restart ML service — `GET /models` confirms new model is active
3. For embedding model change: call `POST /api/horses/reembed-all` to re-embed all reference images
4. New detections will use the new model; `vlm_model_id`/`embed_model_id` on Detection records track which version produced each prediction

## Environment Variables (Backend)

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite:///./equiguard.db` | DB connection |
| `UPLOADS_DIR` | `./uploads` | Image storage path |
| `ML_SERVICE_URL` | `http://localhost:8001` | ML service base URL |
| `USE_MOCK_ML` | `true` | Skip ML service calls, return deterministic fakes |
| `CONFIDENCE_THRESHOLD` | `0.35` | Min cosine similarity for horse match |

## Environment Variables (ML Service)

| Variable | Default | Purpose |
|----------|---------|---------|
| `VLM_MODEL_ID` | `Qwen/Qwen2-VL-2B-Instruct` | HuggingFace model ID for action recognition |
| `EMBED_MODEL_ID` | `google/siglip-so400m-patch14-384` | HuggingFace model ID for embeddings |
| `DEVICE` | `auto` | `cuda`, `cpu`, or `auto` |
| `MOCK_MODE` | `false` | Skip model loading, return deterministic fakes |
| `HF_TOKEN` | — | HuggingFace token for gated/private models |

## Conventions

- Package manager is **uv** (not pip/poetry)
- Python 3.11+
- Backend uses synchronous FastAPI (no async/await in routes); ML service uses async lifespan only
- No authentication; open CORS
- DB columns added via `run_migrations()` in `database.py` (idempotent `ALTER TABLE ADD COLUMN`)
- Sample test images in `assets/` (kenny1-3.jpeg, phillip1-2.jpeg)
- ML service note: on first run, HuggingFace models are downloaded to `~/.cache/huggingface/`; this can be several GB
