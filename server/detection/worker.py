from __future__ import annotations

import argparse
import time
from pathlib import Path

from server.detection.pipeline import run_detection_pipeline
from server.storage.db import (
    claim_pending_job,
    get_event,
    init_db,
    insert_detection,
    mark_event_status,
    mark_job_done,
    mark_job_failed,
)


def process_one_detection_job() -> bool:
    init_db()
    job = claim_pending_job("detect")
    if job is None:
        return False

    event_id = int(job["event_id"])
    event = get_event(event_id)
    if event is None:
        error = f"Missing event for job {job['id']}: event_id={event_id}"
        mark_job_failed(int(job["id"]), error)
        return True

    try:
        frame_path = Path(event["frame_path"])
        detections = run_detection_pipeline(frame_path)
        for det in detections:
            insert_detection(
                event_id=event_id,
                detection_type=det.detection_type,
                label=det.label,
                confidence=det.confidence,
                horse_id=det.horse_id,
                features=det.features,
            )
        mark_event_status(event_id, status="detected")
        mark_job_done(int(job["id"]))
    except Exception as exc:
        mark_event_status(event_id, status="failed", error=str(exc))
        mark_job_failed(int(job["id"]), str(exc))
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="StableGuard detection worker")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process at most one pending detection job and exit",
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=1.0,
        help="Polling interval while waiting for jobs",
    )
    args = parser.parse_args()

    if args.once:
        processed = process_one_detection_job()
        if not processed:
            print("No pending detection jobs")
        return

    while True:
        processed = process_one_detection_job()
        if not processed:
            time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()
