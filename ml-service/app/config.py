from __future__ import annotations

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Model identifiers — swap these and restart to deploy a new model
    vlm_model_id: str = "Qwen/Qwen2-VL-2B-Instruct"
    embed_model_id: str = "google/siglip-so400m-patch14-384"

    # Device selection
    device: str = "auto"  # "cuda", "cpu", or "auto"

    # When true, skip model loading and return deterministic fake results
    mock_mode: bool = False

    # HuggingFace token for gated / private models
    hf_token: str | None = None

    # Action classes the VLM classifies into
    known_actions: list[str] = ["standing", "eating", "lying down", "trotting"]

    @computed_field
    @property
    def resolved_device(self) -> str:
        if self.device != "auto":
            return self.device
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"


settings = Settings()
