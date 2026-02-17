from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.database import get_db
from app.horse_identifier import serialize_embedding
from app.ml_client import ml_client
from app.routes.detections import _detection_to_read

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/horses", tags=["horses"])


def _save_upload(upload: UploadFile, subdir: str) -> tuple[str, str]:
    """Save upload and return (absolute_path, relative_path)."""
    destination_dir = Path(settings.uploads_dir) / subdir
    destination_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(upload.filename or "upload.jpg").suffix or ".jpg"
    filename = f"{uuid4().hex}{ext}"
    destination = destination_dir / filename
    destination.write_bytes(upload.file.read())
    return str(destination.resolve()), f"{subdir}/{filename}"


@router.post("", response_model=schemas.HorseRead, status_code=201)
def create_horse(
    name: str = Form(...),
    description: str | None = Form(default=None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    existing = db.query(models.Horse).filter(models.Horse.name == name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Horse with this name already exists.")

    abs_path, rel_path = _save_upload(image, "horses")

    # Generate reference embedding for future identification
    embedding_json: str | None = None
    try:
        emb = ml_client.generate_embedding(abs_path)
        embedding_json = serialize_embedding(emb.embedding)
    except Exception as exc:
        # Non-fatal: horse is created without an embedding; use /reembed later
        logger.warning("Could not generate embedding for horse '%s': %s", name, exc)

    horse = models.Horse(
        name=name,
        description=description,
        reference_image_path=rel_path,
        embedding=embedding_json,
    )
    db.add(horse)
    db.commit()
    db.refresh(horse)
    return horse


@router.get("", response_model=list[schemas.HorseRead])
def list_horses(db: Session = Depends(get_db)):
    return db.query(models.Horse).order_by(models.Horse.created_at.desc()).all()


@router.get("/{horse_id}", response_model=schemas.HorseDetail)
def get_horse(horse_id: int, db: Session = Depends(get_db)):
    horse = db.query(models.Horse).filter(models.Horse.id == horse_id).first()
    if not horse:
        raise HTTPException(status_code=404, detail="Horse not found.")

    detections = (
        db.query(models.Detection)
        .filter(models.Detection.horse_id == horse_id)
        .order_by(models.Detection.timestamp.desc())
        .limit(20)
        .all()
    )
    return schemas.HorseDetail(
        horse=horse,
        recent_detections=[_detection_to_read(d) for d in detections],
    )


@router.post("/{horse_id}/reembed", response_model=schemas.HorseRead)
def reembed_horse(horse_id: int, db: Session = Depends(get_db)):
    """Regenerate the embedding for a single horse using the current ML service model.

    Call this after deploying a new EMBED_MODEL_ID and restarting the ML service
    to bring this horse's embedding up to date.
    """
    horse = db.query(models.Horse).filter(models.Horse.id == horse_id).first()
    if not horse:
        raise HTTPException(status_code=404, detail="Horse not found.")
    if not horse.reference_image_path:
        raise HTTPException(status_code=422, detail="Horse has no reference image.")

    abs_path = str((Path(settings.uploads_dir) / horse.reference_image_path).resolve())
    if not Path(abs_path).is_file():
        raise HTTPException(status_code=422, detail="Reference image not found on disk.")

    try:
        emb = ml_client.generate_embedding(abs_path)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"ML service error: {exc}") from exc

    horse.embedding = serialize_embedding(emb.embedding)
    db.commit()
    db.refresh(horse)
    return horse


@router.post("/reembed-all", response_model=list[schemas.HorseRead])
def reembed_all_horses(db: Session = Depends(get_db)):
    """Regenerate embeddings for every registered horse.

    Use this after deploying a new EMBED_MODEL_ID to the ML service.
    Horses whose reference image is missing from disk are skipped.
    """
    horses = db.query(models.Horse).all()
    updated: list[models.Horse] = []
    errors: list[str] = []

    for horse in horses:
        if not horse.reference_image_path:
            errors.append(f"{horse.name}: no reference image path")
            continue
        abs_path = str((Path(settings.uploads_dir) / horse.reference_image_path).resolve())
        if not Path(abs_path).is_file():
            errors.append(f"{horse.name}: image file missing from disk")
            continue
        try:
            emb = ml_client.generate_embedding(abs_path)
            horse.embedding = serialize_embedding(emb.embedding)
            updated.append(horse)
        except Exception as exc:
            errors.append(f"{horse.name}: {exc}")

    if updated:
        db.commit()
        for h in updated:
            db.refresh(h)

    if errors:
        logger.warning("reembed-all partial errors: %s", "; ".join(errors))

    return updated


@router.delete("/{horse_id}", status_code=204)
def delete_horse(horse_id: int, db: Session = Depends(get_db)):
    horse = db.query(models.Horse).filter(models.Horse.id == horse_id).first()
    if not horse:
        raise HTTPException(status_code=404, detail="Horse not found.")

    db.query(models.Detection).filter(models.Detection.horse_id == horse_id).update(
        {models.Detection.horse_id: None}
    )

    if horse.reference_image_path:
        img = Path(settings.uploads_dir) / horse.reference_image_path
        if img.is_file():
            img.unlink()

    db.delete(horse)
    db.commit()
    return Response(status_code=204)
