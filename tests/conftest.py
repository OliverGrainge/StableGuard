from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.api.main import app
from server.ingestion import api as ingestion_api
from server.storage import db as storage_db


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    db_path = tmp_path / "stableguard.db"

    monkeypatch.setattr(ingestion_api, "FRAMES_DIR", frames_dir)
    monkeypatch.setattr(storage_db, "DB_PATH", db_path)
    storage_db.init_db()

    return TestClient(app)
