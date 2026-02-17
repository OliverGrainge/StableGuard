from __future__ import annotations

import hashlib
import io
import json
import logging

from PIL import Image

from app.config import settings
from app.registry import LoadedModel, registry
from app.schemas import ActionResponse

logger = logging.getLogger(__name__)

KNOWN_ACTIONS = settings.known_actions

ACTION_PROMPT = (
    "You are analyzing a scene from a horse monitoring camera. "
    "Identify the PRIMARY action of the horse in this image. "
    f"You MUST choose exactly one action from this list: {KNOWN_ACTIONS}. "
    "Respond ONLY with a JSON object (no markdown, no code fences) with these keys: "
    '"action" (string, exactly one of the listed actions), '
    '"confidence" (float between 0 and 1), '
    '"description" (string, one concise sentence).'
)


def load_vlm() -> LoadedModel:
    """Load Qwen2-VL and its processor. Called once during service startup."""
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

    model_id = settings.vlm_model_id
    device = settings.resolved_device
    logger.info("Loading VLM %s → %s ...", model_id, device)

    load_kwargs: dict = {"torch_dtype": "auto", "device_map": device}
    if settings.hf_token:
        load_kwargs["token"] = settings.hf_token

    model = Qwen2VLForConditionalGeneration.from_pretrained(model_id, **load_kwargs)
    processor = AutoProcessor.from_pretrained(
        model_id,
        **({"token": settings.hf_token} if settings.hf_token else {}),
    )

    revision = _fetch_revision(model_id)
    return LoadedModel(
        model_id=model_id,
        role="vlm",
        model=model,
        processor=processor,
        revision=revision,
        device=device,
    )


def analyze_action(image_bytes: bytes) -> ActionResponse:
    if settings.mock_mode:
        return _mock_analyze(image_bytes)

    loaded = registry.get("vlm")
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": ACTION_PROMPT},
            ],
        }
    ]

    from qwen_vl_utils import process_vision_info

    text = loaded.processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = loaded.processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to(loaded.model.device)

    import torch
    with torch.no_grad():
        output_ids = loaded.model.generate(**inputs, max_new_tokens=200)

    # Strip input tokens from the generated output
    trimmed = [out[len(inp):] for inp, out in zip(inputs.input_ids, output_ids)]
    raw_text = loaded.processor.batch_decode(trimmed, skip_special_tokens=True)[0]

    return _parse_vlm_output(raw_text, loaded.model_id, loaded.revision)


# ── Parsing ────────────────────────────────────────────────────────────────


def _parse_vlm_output(raw: str, model_id: str, revision: str | None) -> ActionResponse:
    """Extract JSON from raw VLM output; fall back gracefully on parse failure."""
    text = raw.strip()

    # Strip markdown code fences (``` or ```json ... ```)
    if text.startswith("```"):
        lines = text.splitlines()
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[1:end])

    try:
        data = json.loads(text)
        action = str(data.get("action", "standing")).lower().strip()
        if action not in KNOWN_ACTIONS:
            action = _closest_action(action)
        confidence = _clamp_confidence(data.get("confidence", 0.5))
        description = str(data.get("description", raw[:200]))
    except (json.JSONDecodeError, ValueError, TypeError):
        action = _closest_action(raw)
        confidence = 0.5
        description = raw[:200]

    return ActionResponse(
        action=action,
        confidence=confidence,
        description=description,
        model_id=model_id,
        model_revision=revision,
    )


def _closest_action(text: str) -> str:
    """Return the first known action found in text, else the first action."""
    lower = text.lower()
    for candidate in KNOWN_ACTIONS:
        if candidate in lower:
            return candidate
    return KNOWN_ACTIONS[0]


def _clamp_confidence(value) -> float:
    try:
        v = float(value)
        if v > 1.0:
            v /= 100.0
        return max(0.0, min(1.0, v))
    except (TypeError, ValueError):
        return 0.5


# ── Mock ───────────────────────────────────────────────────────────────────


def _mock_analyze(image_bytes: bytes) -> ActionResponse:
    digest = hashlib.sha256(image_bytes[:512]).hexdigest()
    bucket = int(digest[:4], 16)
    action = KNOWN_ACTIONS[bucket % len(KNOWN_ACTIONS)]
    confidence = round(min(0.55 + (bucket % 40) / 100.0, 0.95), 3)
    return ActionResponse(
        action=action,
        confidence=confidence,
        description=f"[mock] Horse appears to be {action}.",
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
