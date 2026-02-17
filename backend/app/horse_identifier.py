from __future__ import annotations

from app import models


def identify_from_scores(
    horse_scores: dict[str, float] | None,
    horses: list[models.Horse],
) -> tuple[int | None, float, list[dict]]:
    """Pick best horse from embedding similarity scores.

    Returns (best_horse_id, best_probability, all_scores_with_ids).
    """
    if not horse_scores or not horses:
        return None, 0.0, []

    name_to_horse = {h.name.lower(): h for h in horses}
    all_scores: list[dict] = []
    best_id: int | None = None
    best_prob = 0.0

    for name, prob in horse_scores.items():
        horse = name_to_horse.get(name.lower())
        entry = {
            "horse_id": horse.id if horse else None,
            "horse_name": name,
            "probability": prob,
        }
        all_scores.append(entry)
        if horse and prob > best_prob:
            best_prob = prob
            best_id = horse.id

    all_scores.sort(key=lambda s: s["probability"], reverse=True)
    return best_id, best_prob, all_scores
