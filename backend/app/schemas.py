from datetime import datetime
from pydantic import BaseModel, ConfigDict


class HorseBase(BaseModel):
    name: str
    description: str | None = None


class HorseRead(HorseBase):
    id: int
    reference_image_path: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LocationBase(BaseModel):
    name: str
    description: str | None = None


class LocationCreate(LocationBase):
    pass


class LocationRead(LocationBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class HorseScore(BaseModel):
    horse_id: int | None
    horse_name: str
    probability: float


class DetectionBase(BaseModel):
    horse_id: int | None
    location_id: int
    image_path: str
    timestamp: datetime
    action: str
    confidence: float
    raw_vlm_response: str | None = None


class DetectionRead(DetectionBase):
    id: int
    created_at: datetime
    horse_scores: list[HorseScore] | None = None

    model_config = ConfigDict(from_attributes=True)


class AnalyzeResponse(BaseModel):
    detection_id: int
    horse_id: int | None
    horse_name: str | None
    location_id: int
    action: str
    confidence: float
    kept: bool
    timestamp: datetime
    image_path: str
    raw_vlm_response: str | None = None
    horse_scores: list[HorseScore] = []


class HorseDetail(BaseModel):
    horse: HorseRead
    recent_detections: list[DetectionRead]

