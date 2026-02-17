# EquiGuard Backend

FastAPI backend implementing the MVP API in `plan.md`.

Requires [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

## Run

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

API base URL: `http://127.0.0.1:8000`

## Streamlit dashboard

Run API (terminal 1):

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Run dashboard (terminal 2):

```bash
cd frontend
uv sync
uv run streamlit run app.py
```

Dashboard URL (default): `http://localhost:8501`

## Environment variables

- `DATABASE_URL` (default: `sqlite:///./equiguard.db`)
- `UPLOADS_DIR` (default: `./uploads`)
- `USE_MOCK_VLM` (default: `true`)
- `VLM_PROVIDER` (`mock`, `anthropic`, `openai`, `ollama`; default: `mock`)
- `VLM_MODEL` (default: `claude-3-5-sonnet-latest`; set per provider)
- `ANTHROPIC_API_KEY` (for `VLM_PROVIDER=anthropic`)
- `OPENAI_API_KEY` (for `VLM_PROVIDER=openai`)
- `OLLAMA_BASE_URL` (default: `http://localhost:11434`)
- `CONFIDENCE_THRESHOLD` (default: `0.35`)

## Endpoints

- `POST /api/horses` (multipart: `name`, `description`, `image`)
  Creates a horse profile and stores the uploaded reference image.
- `GET /api/horses`
  Lists all horses (newest first).
- `GET /api/horses/{id}`
  Returns one horse plus its 20 most recent detections.
- `POST /api/locations`
  Creates a camera/location area (for example, "Stable A").
- `GET /api/locations`
  Lists all locations.
- `POST /api/detections/analyze?location_id={id}` (multipart: `image`)
  Uploads a new capture image, runs analysis, links it to a horse if matched, and saves a detection row.
- `GET /api/detections?horse_id=&location_id=&date=YYYY-MM-DD`
  Lists detections, optionally filtered by horse, location, and date.
- `GET /api/detections/{horse_id}/timeline`
  Returns timeline/history for one horse (latest first).
- `GET /health`
  Simple liveness check.

## Database and persistence

- Yes, there is a database.
- By default it is SQLite at `backend/equiguard.db` (`DATABASE_URL=sqlite:///./equiguard.db`).
- On server startup, SQLAlchemy runs `create_all`, so missing tables are created automatically.
- Uploaded files are separate from DB rows and go to `backend/uploads` by default (`UPLOADS_DIR=./uploads`):
  - Horse images: `uploads/horses`
  - Detection images: `uploads/detections`

## Resetting local data

Stop the server before resetting.

Reset only database rows (keep uploaded images):

```bash
cd backend
rm -f equiguard.db
```

Reset database rows and uploaded files:

```bash
cd backend
rm -f equiguard.db
rm -rf uploads
```

Then start the server again; tables and directories are recreated automatically on startup.
