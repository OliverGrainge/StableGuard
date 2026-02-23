from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DetectionRecord:
    detection_type: str
    label: str
    confidence: float
    horse_id: int | None
    features: dict


def _infer_activity_from_frame_size(size_bytes: int) -> tuple[str, float]:
    # Placeholder heuristic for MVP wiring. Replace with model inference later.
    idx = size_bytes % 3
    if idx == 0:
        return "standing", 0.72
    if idx == 1:
        return "walking", 0.68
    return "eating", 0.66


def run_detection_pipeline(frame_path: Path) -> list[DetectionRecord]:
    if not frame_path.exists():
        raise FileNotFoundError(f"Frame not found: {frame_path}")

    size_bytes = frame_path.stat().st_size
    if size_bytes == 0:
        return []

    activity_label, confidence = _infer_activity_from_frame_size(size_bytes)
    return [
        DetectionRecord(
            detection_type="activity",
            label=activity_label,
            confidence=confidence,
            horse_id=None,
            features={
                "frame_size_bytes": size_bytes,
                "pipeline_version": "v0",
            },
        )
    ]
