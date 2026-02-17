from __future__ import annotations

import hashlib
import logging
import math
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

KNOWN_ACTIONS = ["standing", "eating", "lying down", "trotting"]

# Matches the embedding dim of the default SigLIP so400m model
_MOCK_EMBED_DIM = 1152


@dataclass
class ActionResult:
    action: str
    confidence: float
    description: str
    model_id: str


@dataclass
class EmbeddingResult:
    embedding: list[float]
    dim: int
    model_id: str


class MLClient:
    """HTTP client for the StableGuard ML microservice.

    When USE_MOCK_ML=true the client returns deterministic fake results
    without making any network calls, so the backend works independently
    of the ML service (useful for frontend development and CI).
    """

    def __init__(self) -> None:
        self.base_url = settings.ml_service_url.rstrip("/")
        self.use_mock = settings.use_mock_ml
        # Sync client — matches the synchronous FastAPI route convention
        self._http = httpx.Client(
            timeout=httpx.Timeout(120.0, connect=5.0),
        )

    def analyze_action(self, image_path: str) -> ActionResult:
        if self.use_mock:
            return self._mock_action(image_path)

        image_bytes = Path(image_path).read_bytes()
        try:
            resp = self._http.post(
                f"{self.base_url}/action",
                files={"image": ("image.jpg", image_bytes, "image/jpeg")},
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"ML service /action call failed: {exc}") from exc

        data = resp.json()
        return ActionResult(
            action=data["action"],
            confidence=data["confidence"],
            description=data["description"],
            model_id=data["model_id"],
        )

    def generate_embedding(self, image_path: str) -> EmbeddingResult:
        if self.use_mock:
            return self._mock_embedding(image_path)

        image_bytes = Path(image_path).read_bytes()
        try:
            resp = self._http.post(
                f"{self.base_url}/embed",
                files={"image": ("image.jpg", image_bytes, "image/jpeg")},
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"ML service /embed call failed: {exc}") from exc

        data = resp.json()
        return EmbeddingResult(
            embedding=data["embedding"],
            dim=data["dim"],
            model_id=data["model_id"],
        )

    # ── Mock helpers ─────────────────────────────────────────────────────────

    def _mock_action(self, image_path: str) -> ActionResult:
        digest = hashlib.sha256(Path(image_path).name.encode()).hexdigest()
        bucket = int(digest[:4], 16)
        action = KNOWN_ACTIONS[bucket % len(KNOWN_ACTIONS)]
        confidence = round(min(0.55 + (bucket % 40) / 100.0, 0.95), 3)
        return ActionResult(
            action=action,
            confidence=confidence,
            description=f"Horse appears to be {action}.",
            model_id="mock",
        )

    def _mock_embedding(self, image_path: str) -> EmbeddingResult:
        """Deterministic L2-normalised embedding derived from the filename hash."""
        digest = hashlib.sha256(Path(image_path).name.encode()).hexdigest()
        dim = _MOCK_EMBED_DIM
        seed = int(digest[:8], 16)
        state = seed
        values: list[float] = []
        for _ in range(dim):
            state = (state * 1664525 + 1013904223) & 0xFFFFFFFF
            values.append((state / 0xFFFFFFFF) * 2.0 - 1.0)
        magnitude = math.sqrt(sum(v * v for v in values))
        unit = [v / magnitude for v in values] if magnitude > 0 else values
        return EmbeddingResult(embedding=unit, dim=dim, model_id="mock")


# Module-level singleton — one client per worker process
ml_client = MLClient()
