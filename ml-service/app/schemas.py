from pydantic import BaseModel


class ActionResponse(BaseModel):
    action: str
    confidence: float           # 0.0 – 1.0
    description: str
    model_id: str               # e.g. "Qwen/Qwen2-VL-2B-Instruct"
    model_revision: str | None = None   # HuggingFace commit sha


class EmbedResponse(BaseModel):
    embedding: list[float]
    dim: int                    # length of the embedding vector
    model_id: str               # e.g. "google/siglip-so400m-patch14-384"
    model_revision: str | None = None


class ModelInfo(BaseModel):
    model_id: str
    role: str                   # "vlm" or "embedder"
    loaded_at: str              # ISO 8601 datetime string
    revision: str | None = None
    device: str


class HealthResponse(BaseModel):
    status: str                 # "ok" or "degraded"
    models_loaded: bool
    vlm_model_id: str
    embed_model_id: str
    device: str
    mock_mode: bool
