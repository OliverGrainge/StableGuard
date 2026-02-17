from datetime import timezone

from fastapi import APIRouter

from app.config import settings
from app.registry import registry
from app.schemas import HealthResponse, ModelInfo

router = APIRouter(tags=["ops"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        models_loaded=registry.is_loaded or settings.mock_mode,
        vlm_model_id=settings.vlm_model_id if not settings.mock_mode else "mock",
        embed_model_id=settings.embed_model_id if not settings.mock_mode else "mock",
        device=settings.resolved_device,
        mock_mode=settings.mock_mode,
    )


@router.get("/models", response_model=list[ModelInfo])
def list_models() -> list[ModelInfo]:
    """Return metadata for all currently loaded models.

    Use this to verify which model version is active in production,
    and to confirm a model swap after restarting with a new MODEL_ID.
    """
    if settings.mock_mode:
        return [
            ModelInfo(model_id="mock", role="vlm", loaded_at="n/a", revision=None, device="cpu"),
            ModelInfo(model_id="mock", role="embedder", loaded_at="n/a", revision=None, device="cpu"),
        ]
    return [
        ModelInfo(
            model_id=m.model_id,
            role=m.role,
            loaded_at=m.loaded_at.astimezone(timezone.utc).isoformat(),
            revision=m.revision,
            device=m.device,
        )
        for m in registry.all_models
    ]
