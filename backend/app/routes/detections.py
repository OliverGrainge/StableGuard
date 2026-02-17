import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.database import get_db
from app.embedding_service import deserialize_embedding, generate_embedding, match_horses
from app.horse_identifier import identify_from_scores
from app.vlm_service import VLMService

router = APIRouter(prefix="/detections", tags=["detections"])
vlm_service = VLMService()


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

    # Step 1: Action classification (VLM)
    analysis = vlm_service.analyze_scene(abs_path)

    # Step 2: Horse identification (CLIP embeddings)
    horses = db.query(models.Horse).all()
    query_embedding = generate_embedding(abs_path)
    horses_with_embeddings = [
        {"name": h.name, "embedding": deserialize_embedding(h.visual_embedding)}
        for h in horses
    ]
    horse_scores = match_horses(query_embedding, horses_with_embeddings)

    horse_id, best_prob, all_scores = identify_from_scores(horse_scores, horses)
    combined_confidence = round((analysis.confidence + best_prob) / 2.0, 3) if horse_id else analysis.confidence
    kept = combined_confidence >= settings.confidence_threshold

    horse_scores_json = json.dumps(all_scores) if all_scores else None

    detection = models.Detection(
        horse_id=horse_id,
        location_id=location_id,
        image_path=rel_path,
        timestamp=datetime.now(timezone.utc),
        action=analysis.action,
        confidence=combined_confidence,
        raw_vlm_response=analysis.raw_response,
        horse_scores_json=horse_scores_json,
    )
    db.add(detection)
    db.commit()
    db.refresh(detection)

    horse_name = None
    if horse_id:
        horse = db.query(models.Horse).filter(models.Horse.id == horse_id).first()
        horse_name = horse.name if horse else None

    response_scores = [
        schemas.HorseScore(horse_id=s["horse_id"], horse_name=s["horse_name"], probability=s["probability"])
        for s in all_scores
    ]

    return schemas.AnalyzeResponse(
        detection_id=detection.id,
        horse_id=horse_id,
        horse_name=horse_name,
        location_id=location_id,
        action=analysis.action,
        confidence=combined_confidence,
        kept=kept,
        timestamp=detection.timestamp,
        image_path=detection.image_path,
        raw_vlm_response=detection.raw_vlm_response,
        horse_scores=response_scores,
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
        query = query.filter(models.Detection.timestamp >= day_start, models.Detection.timestamp <= day_end)

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
