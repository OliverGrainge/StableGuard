from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.registry import registry
from app.routes import action, embed, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.mock_mode:
        logger.info("MOCK_MODE=true — skipping model loading, returning deterministic fakes")
    else:
        logger.info("Loading models (this may take a while on first run / cold cache)...")
        from app.models.vlm import load_vlm
        from app.models.embedder import load_embedder

        vlm_loaded = load_vlm()
        registry.register("vlm", vlm_loaded)

        embedder_loaded = load_embedder()
        registry.register("embedder", embedder_loaded)

        logger.info("All models loaded and ready")

    yield
    # PyTorch releases GPU memory when the process exits — nothing to clean up


def create_app() -> FastAPI:
    app = FastAPI(
        title="StableGuard ML Service",
        description=(
            "Inference endpoints for horse action recognition (VLM) and "
            "visual embedding generation (SigLIP). "
            "Swap models by changing VLM_MODEL_ID / EMBED_MODEL_ID and restarting."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(action.router)
    app.include_router(embed.router)
    app.include_router(health.router)

    return app


app = create_app()
