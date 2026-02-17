from __future__ import annotations

import json
import math

from app import models


# ── Embedding serialization ────────────────────────────────────────────────


def serialize_embedding(embedding: list[float]) -> str:
    """JSON-encode a float list for storage in the Text DB column."""
    return json.dumps(embedding)


def deserialize_embedding(text: str | None) -> list[float] | None:
    """Decode a stored embedding string.

    Returns None if the value is missing, empty, or not a valid float list
    (e.g. old text descriptions from a prior VLM-based approach).
    """
    if not text:
        return None
    try:
        data = json.loads(text)
        if isinstance(data, list) and data and isinstance(data[0], (int, float)):
            return [float(v) for v in data]
    except (json.JSONDecodeError, TypeError, ValueError, IndexError):
        pass
    return None


# ── Cosine similarity (pure Python, no numpy) ──────────────────────────────


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two equal-length float vectors."""
    if len(a) != len(b):
        raise ValueError(f"Vector dimension mismatch: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


# ── Horse matching ─────────────────────────────────────────────────────────


def match_horses(
    query_embedding: list[float],
    horses: list[models.Horse],
) -> tuple[int | None, float, list[dict]]:
    """Rank registered horses by cosine similarity to the query embedding.

    Horses with no stored embedding or a mismatched dimension are silently
    skipped — this is the expected state after deploying a new embedding
    model before re-embedding has been run.

    Returns:
        (best_horse_id, best_similarity, all_scores)
        all_scores is a list of dicts: {horse_id, horse_name, probability}
        sorted descending by probability.
        best_horse_id is None when no horses have embeddings.
    """
    if not horses or not query_embedding:
        return None, 0.0, []

    all_scores: list[dict] = []
    best_id: int | None = None
    best_sim = 0.0

    for horse in horses:
        ref_embedding = deserialize_embedding(horse.embedding)
        if ref_embedding is None:
            continue
        try:
            sim = cosine_similarity(query_embedding, ref_embedding)
        except ValueError:
            # Dimension mismatch — model was swapped without re-embedding this horse
            continue
        all_scores.append({
            "horse_id": horse.id,
            "horse_name": horse.name,
            "probability": round(sim, 4),
        })
        if sim > best_sim:
            best_sim = sim
            best_id = horse.id

    all_scores.sort(key=lambda s: s["probability"], reverse=True)
    return best_id, round(best_sim, 4), all_scores
