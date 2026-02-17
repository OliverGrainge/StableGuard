from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = "EquiGuard API"
    api_prefix: str = "/api"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./equiguard.db")
    uploads_dir: str = os.getenv("UPLOADS_DIR", "./uploads")
    vlm_provider: str = os.getenv("VLM_PROVIDER", "mock")
    vlm_model: str = os.getenv("VLM_MODEL", "claude-3-5-sonnet-latest")
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    use_mock_vlm: bool = os.getenv("USE_MOCK_VLM", "true").lower() == "true"
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.35"))
    clip_model_name: str = os.getenv("CLIP_MODEL_NAME", "clip-ViT-B-32")
    use_mock_embeddings: bool = os.getenv("USE_MOCK_EMBEDDINGS", "true").lower() == "true"


settings = Settings()
