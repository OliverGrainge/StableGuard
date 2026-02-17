from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine, run_migrations
from app.routes import detections, horses, locations

# Ensure uploads dir exists before StaticFiles is instantiated at import time
Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api = settings.api_prefix
    app.include_router(horses.router, prefix=api)
    app.include_router(locations.router, prefix=api)
    app.include_router(detections.router, prefix=api)

    @app.get("/health")
    def healthcheck():
        return {"status": "ok"}

    app.mount("/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")

    return app


app = create_app()
