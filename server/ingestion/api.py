from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from server.storage.db import (
    get_event,
    init_db,
    insert_ingestion_event,
    insert_job,
    list_detections_for_event,
)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

FRAMES_DIR = Path("data/frames")
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
init_db()


@router.post("/frame")
async def upload_frame(
    camera_id: str = Form(...),
    timestamp: str | None = Form(None),
    frame: UploadFile = File(...),
) -> dict:
    if not frame.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    ext = Path(frame.filename).suffix or ".jpg"
    safe_camera = camera_id.replace("/", "_").replace(" ", "_")
    received_at = datetime.now(timezone.utc)

    # Keep naming simple and sortable: camera + receive time + random suffix.
    out_name = f"{safe_camera}_{received_at.strftime('%Y%m%dT%H%M%S%fZ')}_{uuid4().hex[:8]}{ext}"
    out_path = FRAMES_DIR / out_name

    payload = await frame.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Empty frame payload")

    out_path.write_bytes(payload)
    event_id = insert_ingestion_event(
        camera_id=camera_id,
        captured_at=timestamp,
        frame_path=str(out_path),
        size_bytes=len(payload),
    )
    job_id = insert_job(job_type="detect", event_id=event_id)

    return {
        "ok": True,
        "event_id": event_id,
        "job_id": job_id,
        "camera_id": camera_id,
        "timestamp": timestamp,
        "received_at": received_at.isoformat(),
        "saved_path": str(out_path),
        "size_bytes": len(payload),
    }


@router.get("/health")
def health() -> dict:
    return {"ok": True, "service": "ingestion"}


@router.get("/events/{event_id}")
def get_ingestion_event(event_id: int) -> dict:
    row = get_event(event_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return dict(row)


@router.get("/events/{event_id}/detections")
def get_event_detections(event_id: int) -> dict:
    output: list[dict] = []
    for row in list_detections_for_event(event_id):
        record = dict(row)
        features_raw = record.get("features_json")
        try:
            record["features"] = json.loads(features_raw) if features_raw else {}
        except json.JSONDecodeError:
            record["features"] = {}
        output.append(record)
    return {"event_id": event_id, "detections": output}
