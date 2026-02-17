from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.database import get_db
from app.horse_identifier import match_horses
from app.ml_client import ml_client

router = APIRouter(prefix="/detections", tags=["detections"])


def _save_upload(upload: UploadFile, subdir: str) -> tuple[str, str]:
    """Save upload and return (absolute_path, relative_path)."""
    destination_dir = Path(settings.uploads_dir) / subdir
    destination_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(upload.filename or "capture.jpg").suffix or ".jpg"
    filename = f"{uuid4().hex}{ext}"
    destination = destination_dir / filename
    destination.write_bytes(upload.file.read())
    return str(destination.resolve()), f"{subdir}/{filename}"


def _parse_horse_scores(detection: models.Detection) -> list[schemas.HorseScore] | None:
    if not detection.horse_scores_json:
        return None
    try:
        data = json.loads(detection.horse_scores_json)
        return [schemas.HorseScore(**s) for s in data]
    except (json.JSONDecodeError, TypeError):
        return None


def _detection_to_read(d: models.Detection) -> schemas.DetectionRead:
    return schemas.DetectionRead(
        id=d.id,
        horse_id=d.horse_id,
        location_id=d.location_id,
        image_path=d.image_path,
        timestamp=d.timestamp,
        action=d.action,
        confidence=d.confidence,
        raw_vlm_response=d.raw_vlm_response,
        created_at=d.created_at,
        horse_scores=_parse_horse_scores(d),
        vlm_model_id=d.vlm_model_id,
        embed_model_id=d.embed_model_id,
    )


@router.post("/analyze", response_model=schemas.AnalyzeResponse, status_code=201)
def analyze_detection(
    location_id: int = Query(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    location = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found.")

    abs_path, rel_path = _save_upload(image, "detections")

    # Step 1: Action recognition via ML service
    action_result = ml_client.analyze_action(abs_path)

    # Step 2: Generate embedding for the detection image
    emb_result = ml_client.generate_embedding(abs_path)

    # Step 3: Cosine similarity against all registered horse embeddings
    horses = db.query(models.Horse).all()
    best_horse_id, best_similarity, all_scores = match_horses(emb_result.embedding, horses)

    # Only accept the match if similarity clears the threshold
    if best_similarity < settings.confidence_threshold:
        best_horse_id = None

    # Combined confidence: average of action confidence and similarity score
    if best_horse_id is not None:
        combined_confidence = round((action_result.confidence + best_similarity) / 2.0, 3)
    else:
        combined_confidence = round(action_result.confidence, 3)

    kept = combined_confidence >= settings.confidence_threshold

    horse_scores_json = json.dumps(all_scores) if all_scores else None
    raw_inference = json.dumps({
        "action": {
            "action": action_result.action,
            "confidence": action_result.confidence,
            "description": action_result.description,
            "model_id": action_result.model_id,
        },
        "embedding": {
            "dim": emb_result.dim,
            "model_id": emb_result.model_id,
            "best_similarity": round(best_similarity, 4),
        },
    })

    detection = models.Detection(
        horse_id=best_horse_id,
        location_id=location_id,
        image_path=rel_path,
        timestamp=datetime.now(timezone.utc),
        action=action_result.action,
        confidence=combined_confidence,
        raw_vlm_response=raw_inference,
        horse_scores_json=horse_scores_json,
        vlm_model_id=action_result.model_id,
        embed_model_id=emb_result.model_id,
    )
    db.add(detection)
    db.commit()
    db.refresh(detection)

    horse_name: str | None = None
    if best_horse_id is not None:
        matched = next((h for h in horses if h.id == best_horse_id), None)
        horse_name = matched.name if matched else None

    response_scores = [
        schemas.HorseScore(
            horse_id=s["horse_id"],
            horse_name=s["horse_name"],
            probability=s["probability"],
        )
        for s in all_scores
    ]

    return schemas.AnalyzeResponse(
        detection_id=detection.id,
        horse_id=best_horse_id,
        horse_name=horse_name,
        location_id=location_id,
        action=action_result.action,
        confidence=combined_confidence,
        kept=kept,
        timestamp=detection.timestamp,
        image_path=detection.image_path,
        raw_vlm_response=raw_inference,
        horse_scores=response_scores,
        vlm_model_id=action_result.model_id,
        embed_model_id=emb_result.model_id,
    )


@router.get("", response_model=list[schemas.DetectionRead])
def list_detections(
    horse_id: int | None = Query(default=None),
    location_id: int | None = Query(default=None),
    date: str | None = Query(default=None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Detection)
    if horse_id is not None:
        query = query.filter(models.Detection.horse_id == horse_id)
    if location_id is not None:
        query = query.filter(models.Detection.location_id == location_id)
    if date:
        try:
            parsed = datetime.strptime(date, "%Y-%m-%d")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD") from exc
        day_start = parsed.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
        query = query.filter(
            models.Detection.timestamp >= day_start,
            models.Detection.timestamp <= day_end,
        )

    rows = query.order_by(models.Detection.timestamp.desc()).limit(200).all()
    return [_detection_to_read(d) for d in rows]


@router.get("/{horse_id}/timeline", response_model=list[schemas.DetectionRead])
def horse_timeline(horse_id: int, db: Session = Depends(get_db)):
    horse = db.query(models.Horse).filter(models.Horse.id == horse_id).first()
    if not horse:
        raise HTTPException(status_code=404, detail="Horse not found.")

    rows = (
        db.query(models.Detection)
        .filter(models.Detection.horse_id == horse_id)
        .order_by(models.Detection.timestamp.desc())
        .limit(500)
        .all()
    )
    return [_detection_to_read(d) for d in rows]
