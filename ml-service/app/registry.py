from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LoadedModel:
    """Metadata and handles for a single loaded HuggingFace model."""
    model_id: str
    role: str           # "vlm" | "embedder"
    model: Any          # HuggingFace model object
    processor: Any      # Associated processor / tokenizer
    loaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    revision: str | None = None     # HuggingFace commit sha
    device: str = "cpu"


class ModelRegistry:
    """Singleton that holds all loaded models, keyed by role.

    In an MLOps workflow, models are swapped by changing the model_id in
    config (env var), restarting the service, and then re-embedding any
    stored reference data via the /reembed endpoints on the backend.
    """

    def __init__(self) -> None:
        self._models: dict[str, LoadedModel] = {}

    def register(self, role: str, loaded: LoadedModel) -> None:
        self._models[role] = loaded
        logger.info(
            "Registered model  role=%-10s  model_id=%s  device=%s",
            role, loaded.model_id, loaded.device,
        )

    def get(self, role: str) -> LoadedModel:
        if role not in self._models:
            raise RuntimeError(
                f"Model role '{role}' is not loaded. "
                "Ensure the service started successfully (or disable MOCK_MODE)."
            )
        return self._models[role]

    @property
    def all_models(self) -> list[LoadedModel]:
        return list(self._models.values())

    @property
    def is_loaded(self) -> bool:
        return bool(self._models)


# Module-level singleton — importable anywhere without needing the request context
registry = ModelRegistry()
