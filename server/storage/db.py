from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("data/stableguard.db")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_conn(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | None = None) -> None:
    conn = get_conn(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS ingestion_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_id TEXT NOT NULL,
                captured_at TEXT,
                received_at TEXT NOT NULL,
                frame_path TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'received',
                last_error TEXT
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                event_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                attempts INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_error TEXT,
                FOREIGN KEY(event_id) REFERENCES ingestion_events(id)
            );

            CREATE INDEX IF NOT EXISTS idx_jobs_type_status ON jobs(type, status, id);
            CREATE INDEX IF NOT EXISTS idx_ingestion_events_status ON ingestion_events(status, id);

            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                detection_type TEXT NOT NULL DEFAULT 'object',
                label TEXT NOT NULL,
                horse_id INTEGER,
                confidence REAL NOT NULL,
                features_json TEXT NOT NULL DEFAULT '{}',
                class_name TEXT,
                bbox_x REAL,
                bbox_y REAL,
                bbox_w REAL,
                bbox_h REAL,
                detected_at TEXT NOT NULL,
                FOREIGN KEY(event_id) REFERENCES ingestion_events(id)
            );
            """
        )
        _migrate_detections_table(conn)
        conn.commit()
    finally:
        conn.close()


def _migrate_detections_table(conn: sqlite3.Connection) -> None:
    columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(detections)").fetchall()
    }
    if "detection_type" not in columns:
        conn.execute(
            "ALTER TABLE detections ADD COLUMN detection_type TEXT NOT NULL DEFAULT 'object'"
        )
    if "label" not in columns:
        conn.execute("ALTER TABLE detections ADD COLUMN label TEXT NOT NULL DEFAULT ''")
        conn.execute("UPDATE detections SET label = COALESCE(class_name, '') WHERE label = ''")
    if "features_json" not in columns:
        conn.execute(
            "ALTER TABLE detections ADD COLUMN features_json TEXT NOT NULL DEFAULT '{}'"
        )
    if "horse_id" not in columns:
        conn.execute("ALTER TABLE detections ADD COLUMN horse_id INTEGER")


def insert_ingestion_event(
    camera_id: str,
    captured_at: str | None,
    frame_path: str,
    size_bytes: int,
    db_path: Path | None = None,
) -> int:
    received_at = utc_now_iso()
    conn = get_conn(db_path)
    try:
        cur = conn.execute(
            """
            INSERT INTO ingestion_events (
                camera_id, captured_at, received_at, frame_path, size_bytes, status
            ) VALUES (?, ?, ?, ?, ?, 'received')
            """,
            (camera_id, captured_at, received_at, frame_path, size_bytes),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def insert_job(job_type: str, event_id: int, db_path: Path | None = None) -> int:
    now = utc_now_iso()
    conn = get_conn(db_path)
    try:
        cur = conn.execute(
            """
            INSERT INTO jobs (type, event_id, status, attempts, created_at, updated_at)
            VALUES (?, ?, 'pending', 0, ?, ?)
            """,
            (job_type, event_id, now, now),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def get_event(event_id: int, db_path: Path | None = None) -> sqlite3.Row | None:
    conn = get_conn(db_path)
    try:
        cur = conn.execute("SELECT * FROM ingestion_events WHERE id = ?", (event_id,))
        return cur.fetchone()
    finally:
        conn.close()


def list_detections_for_event(
    event_id: int, db_path: Path | None = None
) -> list[sqlite3.Row]:
    conn = get_conn(db_path)
    try:
        cur = conn.execute(
            "SELECT * FROM detections WHERE event_id = ? ORDER BY id ASC", (event_id,)
        )
        return cur.fetchall()
    finally:
        conn.close()


def claim_pending_job(
    job_type: str, db_path: Path | None = None
) -> sqlite3.Row | None:
    conn = get_conn(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.execute(
            """
            SELECT * FROM jobs
            WHERE type = ? AND status = 'pending'
            ORDER BY id ASC
            LIMIT 1
            """,
            (job_type,),
        )
        row = cur.fetchone()
        if row is None:
            conn.rollback()
            return None

        conn.execute(
            """
            UPDATE jobs
            SET status = 'processing', attempts = attempts + 1, updated_at = ?
            WHERE id = ?
            """,
            (utc_now_iso(), row["id"]),
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM jobs WHERE id = ?", (row["id"],)).fetchone()
        return updated
    finally:
        conn.close()


def mark_job_done(job_id: int, db_path: Path | None = None) -> None:
    conn = get_conn(db_path)
    try:
        conn.execute(
            "UPDATE jobs SET status = 'done', updated_at = ?, last_error = NULL WHERE id = ?",
            (utc_now_iso(), job_id),
        )
        conn.commit()
    finally:
        conn.close()


def mark_job_failed(job_id: int, error: str, db_path: Path | None = None) -> None:
    conn = get_conn(db_path)
    try:
        conn.execute(
            "UPDATE jobs SET status = 'failed', updated_at = ?, last_error = ? WHERE id = ?",
            (utc_now_iso(), error, job_id),
        )
        conn.commit()
    finally:
        conn.close()


def mark_event_status(
    event_id: int, status: str, error: str | None = None, db_path: Path | None = None
) -> None:
    conn = get_conn(db_path)
    try:
        conn.execute(
            """
            UPDATE ingestion_events
            SET status = ?, last_error = ?
            WHERE id = ?
            """,
            (status, error, event_id),
        )
        conn.commit()
    finally:
        conn.close()


def insert_detection(
    event_id: int,
    detection_type: str,
    label: str,
    confidence: float,
    horse_id: int | None = None,
    features: dict | None = None,
    db_path: Path | None = None,
) -> int:
    conn = get_conn(db_path)
    try:
        feature_payload = json.dumps(features or {}, separators=(",", ":"))
        cur = conn.execute(
            """
            INSERT INTO detections (
                event_id,
                detection_type,
                label,
                horse_id,
                confidence,
                features_json,
                class_name,
                bbox_x,
                bbox_y,
                bbox_w,
                bbox_h,
                detected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                detection_type,
                label,
                horse_id,
                confidence,
                feature_payload,
                label,
                0.0,
                0.0,
                1.0,
                1.0,
                utc_now_iso(),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()
