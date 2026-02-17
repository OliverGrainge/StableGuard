from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.database import get_db
from app.embedding_service import generate_embedding, serialize_embedding
from app.routes.detections import _detection_to_read

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
    embedding = generate_embedding(abs_path)
    horse = models.Horse(
        name=name,
        description=description,
        reference_image_path=rel_path,
        visual_embedding=serialize_embedding(embedding),
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
    return schemas.HorseDetail(horse=horse, recent_detections=[_detection_to_read(d) for d in detections])


@router.delete("/{horse_id}", status_code=204)
def delete_horse(horse_id: int, db: Session = Depends(get_db)):
    horse = db.query(models.Horse).filter(models.Horse.id == horse_id).first()
    if not horse:
        raise HTTPException(status_code=404, detail="Horse not found.")

    # Nullify horse_id on related detections
    db.query(models.Detection).filter(models.Detection.horse_id == horse_id).update(
        {models.Detection.horse_id: None}
    )

    # Delete reference image from disk
    if horse.reference_image_path:
        img = Path(settings.uploads_dir) / horse.reference_image_path
        if img.is_file():
            img.unlink()

    db.delete(horse)
    db.commit()
    return Response(status_code=204)

