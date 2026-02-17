import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_migrations(bind_engine) -> None:
    """Apply additive schema changes that create_all won't handle.

    Each statement is wrapped in its own try/except so that columns which
    already exist (e.g. on a fresh DB where create_all added them) are
    silently skipped. Safe to call on every startup.
    """
    migrations = [
        "ALTER TABLE horses ADD COLUMN embedding TEXT",
        "ALTER TABLE detections ADD COLUMN vlm_model_id VARCHAR(255)",
        "ALTER TABLE detections ADD COLUMN embed_model_id VARCHAR(255)",
    ]
    with bind_engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
                logger.info("Migration applied: %s", sql)
            except Exception:
                conn.rollback()  # column already exists — expected on repeated startups

