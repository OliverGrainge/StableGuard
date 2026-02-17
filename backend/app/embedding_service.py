from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from app.config import settings

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(settings.clip_model_name)
    return _model


def generate_embedding(image_path: str) -> list[float]:
    """Encode an image to a CLIP embedding vector.

    In mock mode, returns a deterministic 512-dim unit vector derived from
    the filename hash. No model download required.
    """
    if settings.use_mock_embeddings:
        return _mock_embedding(image_path)

    from PIL import Image

    model = _get_model()
    img = Image.open(image_path)
    embedding = model.encode(img)
    return embedding.tolist()


def match_horses(
    query_embedding: list[float],
    horses: list[dict],
) -> dict[str, float]:
    """Compute cosine similarity between query embedding and each horse.

    Args:
        query_embedding: CLIP embedding of the detection image.
        horses: List of dicts with "name" and "embedding" keys.
            Horses with None embeddings are skipped.

    Returns:
        Dict mapping horse name to normalised similarity score (sums to ~1.0).
    """
    raw_scores: list[tuple[str, float]] = []
    for h in horses:
        emb = h.get("embedding")
        if emb is None:
            continue
        sim = cosine_similarity(query_embedding, emb)
        # Clamp to [0, 1] — negative similarity means very dissimilar
        raw_scores.append((h["name"], max(0.0, sim)))

    if not raw_scores:
        return {}

    total = sum(s for _, s in raw_scores)
    if total == 0:
        # All scores zero — distribute evenly
        n = len(raw_scores)
        return {name: round(1.0 / n, 3) for name, _ in raw_scores}

    return {name: round(score / total, 3) for name, score in raw_scores}


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors. Pure Python, no numpy."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def serialize_embedding(embedding: list[float]) -> str:
    """Serialize embedding to JSON string for DB storage."""
    return json.dumps(embedding)


def deserialize_embedding(text: str | None) -> list[float] | None:
    """Deserialize embedding from DB storage.

    Returns None for missing data or old-format text descriptions
    (graceful migration from VLM-based visual_embedding strings).
    """
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
        return data
    return None


def _mock_embedding(image_path: str) -> list[float]:
    """Deterministic 512-dim unit vector from filename hash."""
    digest = hashlib.sha256(Path(image_path).name.encode("utf-8")).hexdigest()
    dim = 512
    raw = []
    for i in range(dim):
        # Use rolling 8-char hex windows for variety
        start = (i * 2) % len(digest)
        val = int(digest[start : start + 2], 16) / 255.0
        raw.append(val - 0.5)  # Center around 0

    # Normalise to unit vector
    norm = math.sqrt(sum(x * x for x in raw))
    return [round(x / norm, 6) for x in raw]
