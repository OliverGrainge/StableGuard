from fastapi import FastAPI

from server.ingestion.api import router as ingestion_router

app = FastAPI(title="StableGuard API", version="0.1.0")
app.include_router(ingestion_router)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "stableguard-api"}
