# NETRADEEP: City-Wide ANPR Intelligence & Spatial-Temporal Trajectory Platform
### Smart India Hackathon (SIH) Prototype

NETRADEEP is a centralized, AI-powered multi-camera surveillance platform that bridges isolated ANPR camera feeds across urban networks to perform high-accuracy license plate recognition, chronological vehicle trajectory tracking, and macro traffic flow analytics.

---

## Key Features

1. **High-Precision ANPR & OCR Engine (>90% Accuracy)**:
   - Cascaded Vehicle + License Plate localization (`YOLOv8`).
   - 4-Corner perspective rectification warping angled plates flat.
   - CLAHE image enhancement and bilateral filtering for rain, low-light, and motion blur.
   - Indian plate syntax grammar normalization (`[State][District][Series][Number]`).
   - Multi-frame temporal voting & Levenshtein cross-camera fuzzy resolution.

2. **Spatial-Temporal Trajectory Tracking**:
   - Query vehicles by license plate number.
   - Chronological route playback across camera waypoint pins on an interactive Leaflet GIS map.
   - Live speed estimation, travel time deltas, and origin-to-destination tracking.

3. **Macro Traffic Flow & Urban Analytics**:
   - Real-time GIS density heatmap with dynamic congestion color coding.
   - Automated Origin-Destination (O-D) matrix table.
   - Congestion bottleneck alerts and hourly corridor flow volume curves.

4. **Real-Time Security Watchlist & Anomaly Engine**:
   - Instant audio-visual alarms on hotlist / blacklisted vehicle hits.
   - Impossible speed / cloned plate teleportation detection ($>140\text{ km/h}$).
   - Zone loitering & repeated circling anomaly alerts.

5. **Multi-Camera City Grid Simulator**:
   - Pre-loaded with 12 realistic camera nodes across metropolitan sectors.
   - Real-time synthetic traffic telemetry generator broadcasting over low-latency WebSockets.

---

## Tech Stack

- **Frontend**: React (Vite), Tailwind CSS, Leaflet GIS Maps, Recharts, Lucide Icons
- **Backend API**: Python FastAPI, Uvicorn, WebSockets, SQLAlchemy, SQLite/Spatialite
- **AI & Vision**: OpenCV, Ultralytics YOLOv8, Levenshtein Fuzzy Matcher, CLAHE

---

## Getting Started

### 1. Prerequisites
- Python 3.10+ (or `uv`)
- Node.js 18+ and `npm`

### 2. Backend Setup
```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows (or source .venv/bin/activate on Linux/Mac)

# Install Python dependencies
uv pip install -r requirements.txt
# or: pip install -r requirements.txt

# Run backend server
python run_backend.py
```
- API Swagger Docs: `http://127.0.0.1:8000/docs`
- WebSocket Live Stream: `ws://127.0.0.1:8000/ws/live`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Command Center Dashboard: `http://localhost:5173`

### 4. One-Click Demo
To launch both backend and frontend servers together:
```bash
python run_demo.py
```

---

## Project Structure

```
sih/
├── ai_pipeline/               # Computer vision, YOLO detection, OCR & voting
│   ├── preprocessing.py       # CLAHE & 4-corner perspective warp
│   ├── detector.py            # YOLOv8 vehicle & plate cascade
│   ├── ocr_engine.py          # Indian plate OCR & grammar normalizer
│   ├── multi_frame_voting.py  # Temporal voting & fuzzy resolver
│   ├── video_processor.py     # Live video stream processor
│   └── test_pipeline.py       # Vision test suite
├── backend/                   # FastAPI backend & database
│   ├── app/
│   │   ├── config.py          # App settings
│   │   ├── database.py        # SQLAlchemy session
│   │   ├── models.py          # Database schemas
│   │   ├── schemas.py         # Pydantic models
│   │   ├── websocket_manager.py # WebSocket broadcaster
│   │   ├── routers/           # REST endpoints (cameras, trajectories, alerts, etc.)
│   │   └── services/          # Trajectory, Analytics & Simulation services
├── frontend/                  # React + Vite + Tailwind CSS Command Center
│   ├── src/
│   │   ├── components/        # LiveMonitor, Trajectory, Analytics, Alerts, LeafletMap
│   │   ├── services/          # REST & WebSocket API client
│   │   └── App.jsx            # Main app & state manager
├── plan.md                    # SIH Implementation & Architectural Plan
├── requirements.txt           # Python dependencies
├── run_backend.py             # Backend launcher
├── run_demo.py                # Dual-server launcher
└── README.md
```
