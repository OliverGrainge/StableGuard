from pathlib import Path

from server.detection.worker import process_one_detection_job


def test_api_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True, "service": "stableguard-api"}


def test_ingestion_health(client):
    response = client.get("/ingestion/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True, "service": "ingestion"}


def test_upload_frame_success(client):
    payload = b"\xff\xd8\xfffakejpg"

    response = client.post(
        "/ingestion/frame",
        data={
            "camera_id": "stable_01",
            "timestamp": "2026-02-23T20:00:00Z",
        },
        files={"frame": ("frame.jpg", payload, "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert isinstance(body["event_id"], int)
    assert isinstance(body["job_id"], int)
    assert body["camera_id"] == "stable_01"
    assert body["timestamp"] == "2026-02-23T20:00:00Z"
    assert body["size_bytes"] == len(payload)

    saved_path = Path(body["saved_path"])
    assert saved_path.exists()
    assert saved_path.read_bytes() == payload

    event_response = client.get(f"/ingestion/events/{body['event_id']}")
    assert event_response.status_code == 200
    event = event_response.json()
    assert event["id"] == body["event_id"]
    assert event["status"] == "received"
    assert event["camera_id"] == "stable_01"


def test_detection_worker_processes_pending_job(client):
    payload = b"\xff\xd8\xffanotherfakejpg"
    upload_response = client.post(
        "/ingestion/frame",
        data={"camera_id": "field_01"},
        files={"frame": ("frame.jpg", payload, "image/jpeg")},
    )
    assert upload_response.status_code == 200
    event_id = upload_response.json()["event_id"]

    processed = process_one_detection_job()
    assert processed is True

    event_response = client.get(f"/ingestion/events/{event_id}")
    assert event_response.status_code == 200
    assert event_response.json()["status"] == "detected"

    detections_response = client.get(f"/ingestion/events/{event_id}/detections")
    assert detections_response.status_code == 200
    detections = detections_response.json()["detections"]
    assert len(detections) == 1
    assert detections[0]["detection_type"] == "activity"
    assert detections[0]["label"] in {"standing", "walking", "eating"}
    assert detections[0]["horse_id"] is None
    assert 0.65 <= detections[0]["confidence"] <= 0.72
    assert detections[0]["features"]["frame_size_bytes"] == len(payload)
    assert detections[0]["features"]["pipeline_version"] == "v0"


def test_upload_frame_rejects_empty_payload(client):
    response = client.post(
        "/ingestion/frame",
        data={"camera_id": "stable_01"},
        files={"frame": ("empty.jpg", b"", "image/jpeg")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Empty frame payload"


def test_upload_frame_requires_camera_id(client):
    response = client.post(
        "/ingestion/frame",
        files={"frame": ("frame.jpg", b"abc", "image/jpeg")},
    )

    assert response.status_code == 422


def test_upload_frame_requires_valid_file_part(client):
    response = client.post(
        "/ingestion/frame",
        data={"camera_id": "stable_01"},
        files={"frame": ("", b"abc", "application/octet-stream")},
    )

    # FastAPI validation rejects this request before endpoint logic runs.
    assert response.status_code == 422
