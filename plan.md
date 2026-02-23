# StableGuard MVP — System Design

## Overview

A backyard MVP using a **desktop PC as the server** and **Raspberry Pi units as edge camera nodes** deployed across your yard. The goal is to prove the core detection pipeline end-to-end: capture video → detect horses → classify behaviour → generate alerts.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          YOUR YARD                                  │
│                                                                     │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐          │
│   │  Pi Node 01  │   │  Pi Node 02  │   │  Pi Node 03  │   ...    │
│   │  (Stable)    │   │  (Field)     │   │  (Pen)       │          │
│   │              │   │              │   │              │          │
│   │ • Pi 4/5     │   │ • Pi 4/5     │   │ • Pi 4/5     │          │
│   │ • Pi Camera  │   │ • Pi Camera  │   │ • Pi Camera  │          │
│   │   Module v3  │   │   Module v3  │   │   Module v3  │          │
│   │ • IR LEDs    │   │ • IR LEDs    │   │ • IR LEDs    │          │
│   │ • Weatherproof│  │ • Weatherproof│  │ • Weatherproof│          │
│   │   enclosure  │   │   enclosure  │   │   enclosure  │          │
│   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘          │
│          │                  │                   │                   │
│          │       Wi-Fi (local network)          │                   │
│          └──────────────────┼───────────────────┘                   │
│                             │                                       │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   DESKTOP SERVER   │
                    │   (Your PC)        │
                    │                    │
                    │ ┌────────────────┐ │
                    │ │ Ingestion API  │ │  ← receives frames/clips
                    │ │ (FastAPI)      │ │     from Pi nodes
                    │ └───────┬────────┘ │
                    │         │          │
                    │ ┌───────▼────────┐ │
                    │ │  CV Pipeline   │ │  ← YOLO detection,
                    │ │  (Python)      │ │     pose estimation,
                    │ │                │ │     behaviour classification
                    │ └───────┬────────┘ │
                    │         │          │
                    │ ┌───────▼────────┐ │
                    │ │  Analysis &    │ │  ← baseline tracking,
                    │ │  Alert Engine  │ │     anomaly scoring,
                    │ └───────┬────────┘ │     colic risk engine
                    │         │          │
                    │ ┌───────▼────────┐ │
                    │ │  Database      │ │  ← SQLite / PostgreSQL
                    │ │  (events, logs)│ │
                    │ └───────┬────────┘ │
                    │         │          │
                    │ ┌───────▼────────┐ │
                    │ │  Web Dashboard │ │  ← local React/Flask UI
                    │ │  + Alert API   │ │     + push notifications
                    │ └────────────────┘ │
                    └────────────────────┘
```

---

## Component Breakdown

### 1. Edge Nodes (Raspberry Pi Units)

Each Pi acts as a dumb-ish camera node. For the MVP, keep processing minimal on the edge — let the server do the heavy lifting.

| Component | Recommendation | Notes |
|---|---|---|
| **Board** | Raspberry Pi 4 (4GB) or Pi 5 | Pi 5 preferred if you plan to do any on-device inference later |
| **Camera** | Pi Camera Module 3 (wide) | 120° FoV, autofocus, good low-light. Wide angle covers more of the stable |
| **Night vision** | Pi NoIR Camera + IR LED board | Or use Camera Module 3 + separate IR illuminator panel |
| **Enclosure** | IP65 weatherproof CCTV housing | Cheap on Amazon/eBay. Mount with adjustable bracket |
| **Power** | PoE hat + PoE switch, or weatherproof mains adapter | PoE is cleaner — single cable for power + network |
| **Storage** | 32GB microSD | Only needs OS + scripts; video streams to server |

**What each Pi does:**

- Captures frames at a configurable interval (e.g. 1 FPS for baseline, 5 FPS when motion detected)
- Runs lightweight motion detection locally (OpenCV frame differencing) to avoid flooding the network with static frames
- Sends JPEG frames or short H.264 clips to the server over HTTP/MQTT
- Reports health metrics (CPU temp, uptime, connectivity) to the server

**Software stack on the Pi:**

```
Raspberry Pi OS Lite (64-bit)
├── picamera2          — camera control
├── OpenCV (headless)  — motion detection
├── MQTT client        — lightweight messaging to server
└── systemd service    — auto-start on boot, watchdog restart
```

---

### 2. Network Layer

For a yard MVP, keep it simple:

| Approach | When to use |
|---|---|
| **Wi-Fi (2.4GHz)** | Pis within ~30m of your router. Cheapest option. |
| **Wi-Fi + mesh extender** | If field cameras are further out. A weatherproof mesh node extends range. |
| **Ethernet + PoE switch** | Most reliable. Run outdoor-rated Cat6 to each Pi. Power + data in one cable. |

**Protocol between Pi → Server:**

- **MQTT** (via Mosquitto broker on the server) for lightweight event messages (motion detected, heartbeat, metadata)
- **HTTP POST** (to FastAPI on the server) for frame/clip uploads — simpler to debug in MVP than streaming protocols
- **Alternative for later:** RTSP streaming if you want continuous video, but overkill for MVP

---

### 3. Server (Desktop PC)

This is the brain. Your desktop handles all the compute-intensive CV and ML work.

**Minimum specs for MVP:**

| Resource | Minimum | Ideal |
|---|---|---|
| **CPU** | Modern quad-core (i5/Ryzen 5) | 8+ cores for parallel processing |
| **RAM** | 16GB | 32GB if running multiple camera feeds |
| **GPU** | NVIDIA GTX 1060 / RTX 2060+ | Any CUDA-capable GPU massively accelerates YOLO inference |
| **Storage** | 500GB SSD | 1TB+ if retaining video clips for training data |
| **OS** | Ubuntu 22.04 / 24.04 LTS | Easiest for Python ML stack + Docker |

---

### 4. Server Software Architecture

```
Desktop Server
│
├── /ingestion                    ← Receives data from Pi nodes
│   ├── FastAPI app               — HTTP endpoint for frame uploads
│   ├── MQTT subscriber           — Listens for motion events, heartbeats
│   └── Frame buffer / queue      — Redis or in-memory queue
│
├── /detection                    ← Computer vision pipeline
│   ├── Horse detector            — YOLOv8/v11 trained on horse dataset
│   ├── Horse re-ID module        — Identify individual horses (MVP: colour/marking heuristics)
│   ├── Pose estimator            — Detect posture: standing, lying, rolling
│   ├── Behaviour classifier      — Classify: eating, drinking, pawing, pacing, etc.
│   └── Object detector           — Detect: rugs, water troughs, hay, droppings
│
├── /analysis                     ← Intelligence layer
│   ├── Baseline engine           — Per-horse behavioural baselines (rolling averages)
│   ├── Anomaly scorer            — Deviation from baseline → risk score
│   ├── Colic risk engine         — Multi-factor scoring (rolling + not eating + pacing etc.)
│   └── Alert generator           — Amber / Red / Critical classification
│
├── /storage                      ← Data persistence
│   ├── PostgreSQL / SQLite       — Events, baselines, horse profiles, alert history
│   ├── File storage              — Saved clips and snapshots (evidence for alerts)
│   └── Time-series store         — Optional: InfluxDB for metrics (activity levels over time)
│
├── /api                          ← Backend API
│   └── FastAPI / Flask           — REST API serving the dashboard and mobile app
│
└── /dashboard                    ← Frontend
    └── React app (or simple      — Live camera views, alert feed, horse profiles,
        Flask templates)             historical charts, colic risk panel
```

---

### 5. CV / ML Pipeline Detail

This is the core of StableGuard. Here's how to approach it for MVP:

#### Stage 1 — Horse Detection

- **Model:** YOLOv8n or YOLOv11n (nano variants — fast, accurate enough)
- **Training data:** Start with COCO pre-trained weights (horses are a COCO class). Fine-tune on your own horses with ~200-500 labelled images from your yard cameras.
- **Output:** Bounding boxes around each horse in frame

#### Stage 2 — Horse Identification (Re-ID)

For MVP, keep this simple:

- **Approach 1 (easiest):** If you have one horse per camera (e.g. individual stables), just assign identity by camera location
- **Approach 2 (moderate):** Use colour histograms + marking templates. Crop the detected horse, extract dominant colours, compare against enrolled profiles
- **Approach 3 (later):** Train a re-identification embedding network (triplet loss) on your horses

#### Stage 3 — Posture / Behaviour Classification

- **Pose estimation:** Use a keypoint model (YOLOv8-pose fine-tuned on horses, or a custom DeepLabCut model) to get body landmark positions
- **Classification:** A simple rule-based classifier to start:
  - Horse bounding box aspect ratio wide + low → **lying down**
  - Keypoints show head near ground → **eating/grazing**
  - Repeated lateral rolling motion → **rolling**
  - Head turned toward flank → **flank-watching**
  - High step frequency, small displacement → **pawing**
  - High displacement over time → **pacing**
- **Later:** Replace rules with a trained temporal classifier (LSTM or Transformer on keypoint sequences)

#### Stage 4 — Object Detection (Environment)

- Fine-tune YOLO to also detect: water troughs, hay nets, feed buckets, droppings, rugs
- This can be a single model with horse + environment classes, or a separate lightweight model

---

### 6. Alert & Baseline System

```
  Per-Horse Data Flow:
  
  Raw detections (every frame)
       │
       ▼
  Rolling aggregation (5-min windows)
       │
       ▼
  Behavioural state log
  ┌──────────────────────────────────┐
  │ Horse: Bella                     │
  │ 22:00-22:05: Standing (resting)  │
  │ 22:05-22:10: Lying (lateral)     │
  │ 22:10-22:12: Rolling (×3)        │
  │ 22:12-22:15: Standing (agitated) │
  │ 22:15-22:20: Pawing              │
  └──────────────┬───────────────────┘
                 │
                 ▼
  Baseline comparison
  ┌──────────────────────────────────┐
  │ Bella's 7-day avg at this hour:  │
  │ • Lying: 40min/hr                │
  │ • Rolling: 0.5×/hr              │
  │ • Pawing: 0×/hr                 │
  │                                  │
  │ Current hour:                    │
  │ • Rolling: 3×  ← 6× baseline ⚠  │
  │ • Pawing: YES  ← unusual     ⚠  │
  │ • Not eaten for 2hrs         ⚠  │
  └──────────────┬───────────────────┘
                 │
                 ▼
  Colic Risk Score: 7.2 / 10  →  🔴 RED ALERT
  ┌──────────────────────────────────┐
  │ Alert: Colic risk — Bella        │
  │ Severity: RED                    │
  │ Factors:                         │
  │  • Repeated rolling (3× in 10m) │
  │  • Pawing behaviour detected     │
  │  • No feeding observed (2hrs)    │
  │ Action: Check horse immediately  │
  │ Clip: [30s video attached]       │
  └──────────────────────────────────┘
```

**Alert delivery for MVP:**

- Web dashboard notification (WebSocket push)
- Email alert (SMTP — easy to set up)
- SMS via Twilio API (cheap, reliable)
- Later: mobile push notifications via a proper app

---

### 7. Data Model (Simplified)

```sql
-- Core entities
horses (id, name, profile_photo, enrolled_date, notes)
cameras (id, location_name, pi_hostname, ip_address, status)
camera_horse_assignments (camera_id, horse_id)  -- which horse is where

-- Detection events
detections (
    id, timestamp, camera_id, horse_id,
    bbox_x, bbox_y, bbox_w, bbox_h,
    confidence, frame_path
)

-- Behavioural states (aggregated from detections)
behaviour_logs (
    id, horse_id, start_time, end_time,
    behaviour_type,  -- standing, lying, rolling, eating, drinking, pawing, pacing, flank_watching
    confidence, metadata_json
)

-- Baselines (computed daily)
baselines (
    id, horse_id, hour_of_day, day_type,  -- weekday/weekend
    avg_standing_mins, avg_lying_mins, avg_eating_mins,
    avg_rolling_count, avg_dropping_count,
    computed_date
)

-- Alerts
alerts (
    id, horse_id, timestamp, severity,  -- amber, red, critical
    alert_type,  -- colic_risk, inactivity, excessive_movement, etc.
    risk_score, contributing_factors_json,
    clip_path, acknowledged, acknowledged_by
)

-- Environment readings
environment_logs (
    id, camera_id, timestamp,
    water_trough_level, hay_present, dropping_count,
    rug_detected, rug_type, ambient_temp
)
```

---

### 8. Tech Stack Summary

| Layer | Technology | Why |
|---|---|---|
| **Edge OS** | Raspberry Pi OS Lite (64-bit) | Minimal, headless, stable |
| **Edge capture** | picamera2 + OpenCV | Native Pi camera support + motion detection |
| **Messaging** | MQTT (Mosquitto) | Lightweight pub/sub, perfect for IoT |
| **Frame transport** | HTTP POST (FastAPI) | Simple, debuggable, good enough for MVP |
| **Server OS** | Ubuntu 22.04/24.04 | Best Linux ML ecosystem support |
| **CV/ML** | YOLOv8/v11 (Ultralytics), PyTorch | State-of-the-art detection, huge community |
| **API** | FastAPI (Python) | Async, fast, auto-docs, great for ML serving |
| **Database** | SQLite (MVP) → PostgreSQL (scale) | Zero-config start, easy migration later |
| **Time-series** | InfluxDB (optional) | If you want rich activity-over-time queries |
| **Dashboard** | React + Vite (or Flask templates) | React for rich interactivity; Flask templates if you want faster MVP |
| **Alerts** | SMTP + Twilio | Email + SMS, easy to wire up |
| **Containers** | Docker Compose | Bundle server services, reproducible setup |
| **Model training** | Label Studio + Ultralytics CLI | Open-source labelling → YOLO training loop |

---

### 9. MVP Build Phases

#### Phase 1 — Camera + Capture (Week 1-2)

- Set up Pi with camera module, get frames streaming
- Implement motion detection on Pi (OpenCV frame diff)
- Set up MQTT broker on server
- Pi sends motion events + frames to server
- Verify: frames arrive and are stored on the server

#### Phase 2 — Horse Detection (Week 3-4)

- Install YOLOv8 on server with CUDA
- Run pre-trained COCO model — verify horse detections on your frames
- Collect ~200 images from your cameras, label with Label Studio
- Fine-tune YOLO on your yard data
- Verify: bounding boxes reliably track your horses

#### Phase 3 — Behaviour Classification (Week 5-7)

- Implement posture classification (rule-based on bbox aspect ratio + keypoints)
- Detect: standing, lying, rolling, eating
- Log behavioural states to database
- Build baseline aggregation (rolling 7-day averages per horse per hour)
- Verify: behaviour logs look sensible over 48hrs of data

#### Phase 4 — Alert Engine (Week 8-9)

- Implement colic risk scoring (multi-factor weighted score)
- Set alert thresholds (amber/red/critical)
- Wire up email alerts via SMTP
- Save 30-second evidence clips when alerts fire
- Verify: simulate colic-like patterns, confirm alerts fire correctly

#### Phase 5 — Dashboard (Week 10-12)

- Build simple web UI: live camera view, alert feed, horse profiles
- Show behavioural timelines per horse (bar chart of daily activity)
- Display current colic risk scores
- Allow alert acknowledgement
- Verify: usable daily by you to monitor your horses

---

### 10. Directory Structure (Server)

```
stableguard/
├── docker-compose.yml
├── .env
│
├── edge/                          # Code deployed to Raspberry Pis
│   ├── capture.py                 # Camera capture + motion detection
│   ├── transport.py               # MQTT + HTTP frame upload
│   ├── config.yaml                # Camera-specific settings
│   └── install.sh                 # Pi setup script
│
├── server/
│   ├── ingestion/
│   │   ├── api.py                 # FastAPI frame upload endpoint
│   │   └── mqtt_listener.py       # MQTT event subscriber
│   │
│   ├── detection/
│   │   ├── horse_detector.py      # YOLO horse detection
│   │   ├── horse_reid.py          # Individual identification
│   │   ├── pose_estimator.py      # Keypoint / posture estimation
│   │   ├── behaviour_classifier.py # Rule-based behaviour classification
│   │   └── environment_detector.py # Rugs, troughs, droppings
│   │
│   ├── analysis/
│   │   ├── baseline_engine.py     # Per-horse rolling baselines
│   │   ├── anomaly_scorer.py      # Deviation scoring
│   │   ├── colic_engine.py        # Multi-factor colic risk
│   │   └── alert_generator.py     # Alert classification + dispatch
│   │
│   ├── storage/
│   │   ├── models.py              # SQLAlchemy / DB models
│   │   ├── migrations/            # Alembic migrations
│   │   └── clip_manager.py        # Save / prune evidence clips
│   │
│   ├── api/
│   │   ├── main.py                # FastAPI app
│   │   ├── routes/                # REST endpoints
│   │   └── websocket.py           # Live dashboard push
│   │
│   └── dashboard/
│       ├── src/                   # React app
│       └── public/
│
├── models/                        # Trained model weights
│   ├── yolo_horse_v1.pt
│   └── pose_horse_v1.pt
│
├── data/
│   ├── frames/                    # Raw captured frames
│   ├── clips/                     # Alert evidence clips
│   └── training/                  # Labelled training data
│
└── scripts/
    ├── train_detector.py          # YOLO fine-tuning script
    ├── label_export.py            # Label Studio → YOLO format
    └── setup_pi.sh                # Automated Pi provisioning
```

---

### 11. Key Risks & Mitigations (MVP)

| Risk | Impact | Mitigation |
|---|---|---|
| **Wi-Fi dropout to field cameras** | Missed detections | Buffer frames on Pi SD card; upload when reconnected. Consider PoE for critical cameras. |
| **Night-time image quality** | Poor detections in darkness | IR illuminator + NoIR camera. Test and adjust IR LED power. |
| **False positive alerts** | Alert fatigue, loss of trust | Conservative alert thresholds in MVP. Require multiple concurrent signals before firing. |
| **Horse Re-ID inaccuracy** | Wrong horse assigned behaviours | MVP: one horse per camera zone. Later: improve with embedding model. |
| **GPU bottleneck** | Can't process all cameras in real-time | Reduce FPS per camera; stagger processing; prioritise cameras with motion events. |
| **Weatherproofing failures** | Dead Pi nodes | IP65 enclosure + silicone seal. Check regularly. Have a spare Pi ready. |
| **Model drift** | Accuracy degrades over time (seasons, lighting) | Periodic re-labelling + re-training. Log confidence scores and review low-confidence detections. |

---

### 12. Future Enhancements (Post-MVP)

- **Cloud deployment** — move inference and dashboard to AWS/GCP for multi-yard support
- **Mobile app** — native iOS/Android with push notifications
- **On-device inference** — run lightweight models on Pi 5 / Coral TPU for lower latency
- **Audio detection** — add microphones for vocalisation analysis (distress calls, coughing)
- **Multi-camera tracking** — track a horse moving between field → stable → arena
- **Vet integration** — share reports directly with veterinary practice management systems
- **Insurance API** — provide monitoring evidence to equine insurers
- **Temperature sensors** — DHT22 / BME280 on each Pi for ambient conditions
f