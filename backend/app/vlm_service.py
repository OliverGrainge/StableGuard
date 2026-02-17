from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.config import settings

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:  # pragma: no cover - optional dependency
    ChatAnthropic = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - optional dependency
    ChatOpenAI = None

try:
    from langchain_ollama import ChatOllama
except ImportError:  # pragma: no cover - optional dependency
    ChatOllama = None


KNOWN_ACTIONS = [
    "standing",
    "walking",
    "running",
    "rolling",
    "eating",
    "drinking",
    "ridden",
]

ActionType = Literal["standing", "walking", "running", "rolling", "eating", "drinking", "ridden"]


class SceneAnalysisSchema(BaseModel):
    action: ActionType = Field(description="Primary horse action in this image.")
    confidence: float = Field(ge=0.0, le=1.0, description="Model confidence between 0 and 1.")
    description: str = Field(description="Short scene description for downstream horse identification.")


class HorseReferenceSchema(BaseModel):
    distinctive_features: list[str] = Field(description="Distinctive visual horse features.")
    coat_color: str | None = Field(default=None, description="Approximate coat color.")
    markings: str | None = Field(default=None, description="Visible face or leg markings.")
    notes: str | None = Field(default=None, description="Any additional identification notes.")


@dataclass
class VLMAnalysisResult:
    action: str
    confidence: float
    description: str
    raw_response: str


class VLMService:
    def __init__(self) -> None:
        self.provider = settings.vlm_provider.lower().strip()
        self.model_name = settings.vlm_model
        self.use_mock = settings.use_mock_vlm or self.provider == "mock"
        self._chat_model = None

        if not self.use_mock:
            self._chat_model = self._build_model()
            if self._chat_model is None:
                self.use_mock = True

    def describe_reference_image(self, image_path: str) -> str:
        if self.use_mock:
            stem = Path(image_path).stem
            return f"Reference profile extracted for horse image '{stem}'."

        model = self._chat_model.with_structured_output(HorseReferenceSchema)
        payload = self._build_vision_payload(
            image_path=image_path,
            prompt=(
                "Describe distinctive horse features for future identification. "
                "Focus on coat, markings, body shape, and visual cues."
            ),
        )
        result: HorseReferenceSchema = model.invoke(payload)
        return result.model_dump_json()

    def analyze_scene(self, image_path: str) -> VLMAnalysisResult:
        if self.use_mock:
            action, confidence, description = self._mock_analyze(image_path)
            raw = f"mock: action={action}; confidence={confidence:.2f}; description={description}"
            return VLMAnalysisResult(
                action=action,
                confidence=confidence,
                description=description,
                raw_response=raw,
            )

        model = self._chat_model.with_structured_output(SceneAnalysisSchema)
        payload = self._build_vision_payload(
            image_path=image_path,
            prompt=(
                "Analyze horse behavior from this frame. "
                f"Return action as one of {KNOWN_ACTIONS}, plus confidence and a brief description."
            ),
        )
        result: SceneAnalysisSchema = model.invoke(payload)
        raw = result.model_dump_json()
        return VLMAnalysisResult(
            action=result.action,
            confidence=result.confidence,
            description=result.description,
            raw_response=raw,
        )

    def _mock_analyze(self, image_path: str) -> tuple[str, float, str]:
        digest = hashlib.sha256(Path(image_path).name.encode("utf-8")).hexdigest()
        bucket = int(digest[:4], 16)
        action = KNOWN_ACTIONS[bucket % len(KNOWN_ACTIONS)]
        confidence = 0.55 + ((bucket % 40) / 100.0)
        confidence = min(confidence, 0.95)
        description = f"Horse appears {action} in the captured area."
        return action, confidence, description

    def _build_model(self):
        if self.provider == "anthropic":
            if ChatAnthropic is None or not settings.anthropic_api_key:
                return None
            return ChatAnthropic(model=self.model_name, anthropic_api_key=settings.anthropic_api_key, max_tokens=400)

        if self.provider == "openai":
            if ChatOpenAI is None or not settings.openai_api_key:
                return None
            return ChatOpenAI(model=self.model_name, api_key=settings.openai_api_key, max_tokens=400)

        if self.provider == "ollama":
            if ChatOllama is None:
                return None
            return ChatOllama(model=self.model_name, base_url=settings.ollama_base_url)

        return None

    def _build_vision_payload(self, image_path: str, prompt: str) -> list[dict]:
        image_b64 = base64.b64encode(Path(image_path).read_bytes()).decode("utf-8")
        image_data_url = f"data:image/jpeg;base64,{image_b64}"

        # OpenAI-compatible multimodal content format used by LangChain chat models.
        return [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ],
            }
        ]
