from __future__ import annotations

import hashlib
import io
import logging
import math

from PIL import Image

from app.config import settings
from app.registry import LoadedModel, registry
from app.schemas import EmbedResponse

logger = logging.getLogger(__name__)

# SigLIP so400m-patch14-384 produces 1152-dimensional embeddings
_SIGLIP_DIM = 1152


def load_embedder() -> LoadedModel:
    """Load SigLIP (or any vision encoder) and its processor. Called once at startup."""
    from transformers import AutoImageProcessor, AutoModel
    import torch

    model_id = settings.embed_model_id
    device = settings.resolved_device
    logger.info("Loading embedder %s → %s ...", model_id, device)

    model = AutoModel.from_pretrained(
        model_id,
        torch_dtype=torch.float32,
        **({"token": settings.hf_token} if settings.hf_token else {}),
    ).to(device)
    model.eval()

    # Use AutoImageProcessor — SigLIP embedder only needs image preprocessing.
    # AutoProcessor tries to load a tokenizer and fails (tokenizer mapping bug in transformers).
    processor = AutoImageProcessor.from_pretrained(
        model_id,
        **({"token": settings.hf_token} if settings.hf_token else {}),
    )

    revision = _fetch_revision(model_id)
    return LoadedModel(
        model_id=model_id,
        role="embedder",
        model=model,
        processor=processor,
        revision=revision,
        device=device,
    )


def generate_embedding(image_bytes: bytes) -> EmbedResponse:
    if settings.mock_mode:
        return _mock_embed(image_bytes)

    loaded = registry.get("embedder")
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    inputs = loaded.processor(images=image, return_tensors="pt").to(loaded.model.device)

    import torch
    with torch.no_grad():
        outputs = loaded.model(**inputs)

    # pooler_output is the [CLS] token embedding: shape (1, hidden_dim)
    pooled = outputs.pooler_output[0]   # → (hidden_dim,)

    # L2-normalise to a unit vector so cosine similarity == dot product
    norm = pooled.norm()
    if norm > 0:
        pooled = pooled / norm

    embedding = pooled.cpu().tolist()
    return EmbedResponse(
        embedding=embedding,
        dim=len(embedding),
        model_id=loaded.model_id,
        model_revision=loaded.revision,
    )


# ── Mock ───────────────────────────────────────────────────────────────────


def _mock_embed(image_bytes: bytes) -> EmbedResponse:
    """Return a deterministic L2-normalised fake embedding (same dim as SigLIP so400m)."""
    digest = hashlib.sha256(image_bytes[:512]).hexdigest()
    dim = _SIGLIP_DIM
    seed = int(digest[:8], 16)

    # Simple LCG to generate reproducible floats
    state = seed
    values: list[float] = []
    for _ in range(dim):
        state = (state * 1664525 + 1013904223) & 0xFFFFFFFF
        values.append((state / 0xFFFFFFFF) * 2.0 - 1.0)

    # Normalise to unit vector
    magnitude = math.sqrt(sum(v * v for v in values))
    unit = [v / magnitude for v in values] if magnitude > 0 else values

    return EmbedResponse(
        embedding=unit,
        dim=dim,
        model_id="mock",
        model_revision=None,
    )


# ── Helpers ────────────────────────────────────────────────────────────────


def _fetch_revision(model_id: str) -> str | None:
    try:
        from huggingface_hub import model_info as hf_model_info
        info = hf_model_info(model_id)
        return info.sha
    except Exception:
        return None
