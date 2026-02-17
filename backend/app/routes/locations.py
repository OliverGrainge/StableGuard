from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/locations", tags=["locations"])


@router.post("", response_model=schemas.LocationRead, status_code=201)
def create_location(payload: schemas.LocationCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Location).filter(models.Location.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Location with this name already exists.")

    location = models.Location(name=payload.name, description=payload.description)
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@router.get("", response_model=list[schemas.LocationRead])
def list_locations(db: Session = Depends(get_db)):
    return db.query(models.Location).order_by(models.Location.id.asc()).all()


@router.delete("/{location_id}", status_code=204)
def delete_location(location_id: int, db: Session = Depends(get_db)):
    location = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found.")

    detection_count = (
        db.query(models.Detection).filter(models.Detection.location_id == location_id).count()
    )
    if detection_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete location with {detection_count} associated detection(s). Remove detections first.",
        )

    db.delete(location)
    db.commit()
    return Response(status_code=204)

