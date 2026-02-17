from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.vlm import analyze_action
from app.schemas import ActionResponse

router = APIRouter(tags=["inference"])

_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.post("/action", response_model=ActionResponse)
def run_action(image: UploadFile = File(...)) -> ActionResponse:
    if image.content_type and image.content_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type: {image.content_type}. Expected JPEG, PNG, or WebP.",
        )
    image_bytes = image.file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image upload.")
    try:
        return analyze_action(image_bytes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference error: {exc}") from exc
