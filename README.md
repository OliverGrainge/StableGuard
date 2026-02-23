# StableGuard (MVP scaffold)

## Ingestion MVP

Run API:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server.api.main:app --reload --host 0.0.0.0 --port 8000
```

Test frame upload:

```bash
curl -X POST http://127.0.0.1:8000/ingestion/frame \
  -F "camera_id=stable_01" \
  -F "timestamp=2026-02-23T20:00:00Z" \
  -F "frame=@/path/to/frame.jpg"
```

Process one pending detection job:

```bash
python -m server.detection.worker --once
```

Run MQTT listener:

```bash
python -m server.ingestion.mqtt_listener --host 127.0.0.1 --port 1883
```

Data output:
- frames: `data/frames`
- MQTT events: `data/events/mqtt_events.log`
- SQLite DB: `data/stableguard.db`
