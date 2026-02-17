# EquiGuard Server Tutorial

This guide walks through running and using the EquiGuard backend API.

## 1. What You Get

The server provides:
- Horse registration with reference image upload
- Location registration (camera areas)
- Detection analysis from uploaded images
- Activity history and timelines

The API is built with FastAPI and stores data in SQLite by default.

## 2. How Backend Endpoints Work (plain language)

Every endpoint is just a URL that performs one backend action.

- `POST` endpoints create or analyze data.
- `GET` endpoints read data.

In this project:
- `/api/horses` stores horse profiles and their reference image paths.
- `/api/locations` stores location records (camera areas).
- `/api/detections/analyze` stores one uploaded capture + model result as a detection.
- `/api/detections` and `/api/detections/{horse_id}/timeline` read detection history.

The backend does not keep images inside the DB file. It stores image files on disk and saves file paths in the DB.

## 3. Quick Start

```bash
cd api-service
uv sync
uv run uvicorn app.main:app --reload
```

Server URL:
- `http://127.0.0.1:8000`

Swagger docs:
- `http://127.0.0.1:8000/docs`

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## 4. Configure VLM Provider

The server supports mock mode, remote models, and local models.

### A) Mock mode (default, no API keys)

```bash
export USE_MOCK_VLM=true
```

### B) Anthropic via LangChain

```bash
export USE_MOCK_VLM=false
export VLM_PROVIDER=anthropic
export VLM_MODEL=claude-3-5-sonnet-latest
export ANTHROPIC_API_KEY=your_key_here
```

### C) OpenAI via LangChain

```bash
export USE_MOCK_VLM=false
export VLM_PROVIDER=openai
export VLM_MODEL=gpt-4o
export OPENAI_API_KEY=your_key_here
```

### D) Local Ollama via LangChain

1. Start Ollama locally.
2. Pull a vision-capable model (example):

```bash
ollama pull llava:latest
```

3. Set environment variables:

```bash
export USE_MOCK_VLM=false
export VLM_PROVIDER=ollama
export VLM_MODEL=llava:latest
export OLLAMA_BASE_URL=http://localhost:11434
```

## 5. API Walkthrough (End-to-End)

This section shows a full workflow in order.

### Step 1: Create a location

```bash
curl -X POST "http://127.0.0.1:8000/api/locations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Stable A",
    "description": "Main indoor stable"
  }'
```

Example response:

```json
{
  "name": "Stable A",
  "description": "Main indoor stable",
  "id": 1
}
```

### Step 2: Register a horse with a reference image

```bash
curl -X POST "http://127.0.0.1:8000/api/horses" \
  -F "name=Thunder" \
  -F "description=Bay gelding with white blaze" \
  -F "image=@./samples/thunder_ref.jpg"
```

Example response:

```json
{
  "name": "Thunder",
  "description": "Bay gelding with white blaze",
  "id": 1,
  "reference_image_path": "/abs/path/to/uploads/horses/....jpg",
  "created_at": "2026-02-16T12:00:00.000000Z"
}
```

### Step 3: Analyze a detection image

```bash
curl -X POST "http://127.0.0.1:8000/api/detections/analyze?location_id=1" \
  -F "image=@./samples/stable_capture_01.jpg"
```

Example response:

```json
{
  "detection_id": 1,
  "horse_id": 1,
  "horse_name": "Thunder",
  "location_id": 1,
  "action": "standing",
  "confidence": 0.71,
  "kept": true,
  "timestamp": "2026-02-16T12:05:20.000000Z",
  "image_path": "/abs/path/to/uploads/detections/....jpg",
  "raw_vlm_response": "..."
}
```

### Step 4: List detections

All recent:

```bash
curl "http://127.0.0.1:8000/api/detections"
```

Filter by horse:

```bash
curl "http://127.0.0.1:8000/api/detections?horse_id=1"
```

Filter by location:

```bash
curl "http://127.0.0.1:8000/api/detections?location_id=1"
```

Filter by date:

```bash
curl "http://127.0.0.1:8000/api/detections?date=2026-02-16"
```

### Step 5: Get horse details + recent activity

```bash
curl "http://127.0.0.1:8000/api/horses/1"
```

### Step 6: Get horse timeline

```bash
curl "http://127.0.0.1:8000/api/detections/1/timeline"
```

## 6. Important Behaviors

- Duplicate horse name returns `409`.
- Duplicate location name returns `409`.
- Unknown horse/location id returns `404`.
- Invalid date filter format returns `400` (must be `YYYY-MM-DD`).
- `kept` is calculated from `CONFIDENCE_THRESHOLD` (default `0.35`).

## 7. Data and Files

- SQLite DB file is created from `DATABASE_URL` (default `./equiguard.db`).
- Uploaded images are stored under `UPLOADS_DIR` (default `./uploads`).

Default upload paths:
- Horse reference images: `uploads/horses/...`
- Detection images: `uploads/detections/...`

## 8. How To Reset Data

Stop the server first, then run from `api-service/`.

Reset only DB rows (keep uploaded images):

```bash
rm -f equiguard.db
```

Reset DB rows and all uploaded images:

```bash
rm -f equiguard.db
rm -rf uploads
```

Start the server again:

```bash
uv run uvicorn app.main:app --reload
```

On startup, tables and upload directories are recreated automatically.

## 9. Troubleshooting

### `ModuleNotFoundError`

Install dependencies with uv:

```bash
uv sync
```

### Provider misconfiguration falls back to mock

If provider package/key is missing, service may use mock mode. Verify env vars and installed packages:
- `VLM_PROVIDER`
- `VLM_MODEL`
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` (if applicable)
- `OLLAMA_BASE_URL` and local Ollama status (if applicable)

### Ollama issues

Check local service:

```bash
curl http://localhost:11434/api/tags
```

## 10. Suggested Next Improvements

1. Add `.env` loading (`python-dotenv`) for easier local config.
2. Add authentication/API keys for client access.
3. Add Alembic migrations for schema evolution.
4. Add tests for each endpoint and provider mode.
