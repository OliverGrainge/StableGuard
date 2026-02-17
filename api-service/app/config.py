import os
from pathlib import Path

from pydantic import BaseModel


def _load_dotenv() -> None:
    """Load key=value pairs from backend/.env without overriding real env vars."""
    dotenv_path = Path(__file__).resolve().parent.parent / ".env"
    if not dotenv_path.is_file():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

        os.environ.setdefault(key, value)


_load_dotenv()


class Settings(BaseModel):
    app_name: str = "EquiGuard API"
    api_prefix: str = "/api"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./equiguard.db")
    uploads_dir: str = os.getenv("UPLOADS_DIR", "./uploads")
    ml_service_url: str = os.getenv("ML_SERVICE_URL", "http://localhost:8001")
    use_mock_ml: bool = os.getenv("USE_MOCK_ML", "true").lower() == "true"
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.35"))


settings = Settings()
