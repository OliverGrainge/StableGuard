from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Horse(Base):
    __tablename__ = "horses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    reference_image_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON-encoded float list
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    detections: Mapped[list["Detection"]] = relationship(back_populates="horse")


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    detections: Mapped[list["Detection"]] = relationship(back_populates="location")


class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    horse_id: Mapped[int | None] = mapped_column(ForeignKey("horses.id"), nullable=True, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False, index=True)
    image_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    raw_vlm_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    horse_scores_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    vlm_model_id: Mapped[str | None] = mapped_column(String(255), nullable=True)   # MLOps: which VLM produced this
    embed_model_id: Mapped[str | None] = mapped_column(String(255), nullable=True) # MLOps: which embedder produced this
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    horse: Mapped[Horse | None] = relationship(back_populates="detections")
    location: Mapped[Location] = relationship(back_populates="detections")
