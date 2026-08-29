# City-Wide ANPR Intelligence & Trajectory Tracking Platform
## Smart India Hackathon (SIH) Prototype Plan

---

## 1. Problem Statement & Background
Modern urban centers deploy vast networks of CCTV and Automatic Number Plate Recognition (ANPR) cameras. However, most existing systems process feeds in isolated silos without linking data across space and time. 

### Core Objectives:
1. **High-Accuracy ANPR & OCR Engine**: Achieve >90% recognition accuracy across diverse conditions (lighting, rain/fog, motion blur, angled views, dirty/damaged plates).
2. **Single-Plate Spatial-Temporal Trajectory Tracking**: Reconstruct the complete travel trajectory of any specific vehicle across the city network with timestamps, directions, speed estimation, and GIS map plotting.
3. **Macro Traffic Flow & Movement Analytics**: Measure traffic density, generate Origin-Destination (O-D) matrices, detect congestion bottlenecks, and render real-time GIS heatmaps.
4. **Security Alert & Anomaly Detection System**: Flag blacklisted/stolen vehicles, detect cloned plates (impossible-speed teleportation), and identify suspicious loitering/circling patterns.

---

## 2. End-to-End System Workflow

```
[ Multi-Camera Feeds / RTSP / City Simulator ]
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 AI Vision & ANPR Pipeline                   │
├─────────────────────────────────────────────────────────────┤
│ 1. Vehicle Detection (YOLOv8/v11)                           │
│ 2. License Plate Localization (YOLO-Nano)                   │
│ 3. 4-Corner Perspective Rectification & Image Enhancement   │
│ 4. OCR Engine (PaddleOCR / CRNN / Transformer)              │
│ 5. Multi-Frame Temporal Voting (Per-Camera Consensus)       │
│ 6. Fuzzy / Edit-Distance Plate Resolver (Cross-Camera)      │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│             FastAPI Central Event & Stream Hub              │
├─────────────────────────────────────────────────────────────┤
│ • Ingestion & Telemetry Processing                          │
│ • Geospatial & Time-Series DB (SQLite/PostgreSQL + PostGIS) │
│ • Blacklist Cache & Anomaly Detection Rules                 │
│ • WebSocket Broadcaster (Sub-100ms Latency)                 │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│             Command & Control GIS Dashboard                 │
├─────────────────────────────────────────────────────────────┤
│ • Live Multi-Camera Grid (4-9 feeds with live ANPR cards)   │
│ • Trajectory Investigation (Search, path animation, speed)  │
│ • City Flow Analytics (Deck.gl Heatmaps, O-D Matrix, Trends)│
│ • Real-Time Alert Center (Blacklist popups, audio alarms)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

| Layer | Technology | Purpose & Rationale |
| :--- | :--- | :--- |
| **Frontend Framework** | **React (Vite) + Tailwind CSS** | Lightning fast, clean dark-mode command center UI. |
| **GIS & Mapping** | **Leaflet / Mapbox GL + Deck.gl** | 60 FPS interactive camera nodes, road-snapped vehicle animations, dynamic heatmaps. |
| **UI Components & Icons** | **Lucide Icons + Framer Motion + Recharts** | High-polish animations, analytics graphs, modern operational look. |
| **Backend API** | **Python FastAPI + Uvicorn + WebSockets** | Async high-throughput event processing and live updates. |
| **Database** | **SQLite + Spatialite** *(or PostgreSQL + PostGIS)* | Spatial distance calculations, fast time-series queries, zero-friction local setup. |
| **Vision & ANPR** | **Ultralytics YOLOv8/v11 + OpenCV + PaddleOCR** | Staged vehicle $\to$ plate $\to$ warp $\to$ OCR pipeline with >90% precision. |
| **Data Resolution & Analytics** | **Levenshtein Fuzzy Matcher + NetworkX + Pandas** | Auto-corrects OCR typos across cameras, builds O-D routing matrices. |
| **City Simulator** | **Async Multi-Threaded Video & Telemetry Engine** | Simulates 15+ camera nodes with live traffic streams for realistic hackathon demos. |

---

## 4. Key Modules & Feature Breakdown

### Module 1: Staged High-Precision ANPR & Robust OCR
- **Vehicle + Plate Cascade**: Vehicle bounding box detection first, cropping before plate detection to eliminate background false positives.
- **Perspective Rectification**: 4-point perspective warp aligning angled plates flat prior to OCR.
- **Image Preprocessing Layer**: CLAHE (Contrast Limited Adaptive Histogram Equalization) and adaptive filtering for night, rain, and blur.
- **Multi-Frame Majority Voting**: Aggregates OCR results over multiple video frames to select highest-confidence plate text.
- **Indian Plate Format Validator**: Regex formatting for standard formats (`XX 00 XX 0000`, `BH` series, commercial, EV).
- **Edit-Distance Cross-Camera Resolver**: Levenshtein distance clustering to reconcile minor OCR misreads into a single vehicle identity.

### Module 2: Spatial-Temporal Trajectory Tracking
- **Plate Search & Autocomplete**: Instant search by license plate number.
- **Chronological Playback**: Animated timeline slider showing camera hit sequence, timestamps, interval durations, and calculated speeds.
- **Road-Snapped Map Route**: Animated glowing trail plotting the vehicle's exact path between camera nodes on the GIS map.
- **Dwell Time & Direction Vectors**: Visual flags for vehicle direction of travel and stopover points.

### Module 3: Macro Traffic Flow & Urban Analytics
- **Live GIS Density Heatmap**: Dynamic Deck.gl / Leaflet heatmap visualizing vehicle concentrations across all nodes.
- **Automated Origin-Destination (O-D) Matrix**: Calculates trip frequency between city zones/sectors.
- **Congestion Bottleneck Detection**: Statistical anomaly detection (Z-score / EWMA) flagging sudden traffic build-ups.
- **Corridor Speed & Volume Charts**: Real-time inflow/outflow metrics and average corridor velocities.

### Module 4: Real-time Alert & Security Engine
- **Hotlist / Blacklist Matching**: Instant audio and visual alert modal when a flagged/stolen vehicle is detected.
- **Impossible Speed / Teleportation Anomaly**: Detects cloned plates (e.g., same plate at distant cameras within physically impossible time windows).
- **Loitering & Circling Anomaly**: Flags vehicles repeatedly circling high-security zones or checkpoints.
- **Geofence Breach Notifications**: Triggers alerts when flagged vehicles enter restricted city zones.

### Module 5: Multi-Camera City Grid Simulator
- **Live Stream Viewer**: Multi-tile video player displaying concurrent CCTV camera feeds.
- **Interactive City Map**: 15–20 geo-tagged virtual camera nodes across a major metropolitan area (e.g. Delhi / Mumbai / Bengaluru).
- **Synthetic Traffic Replay Engine**: Simulates realistic city-wide vehicle flows to demonstrate macro analytics at scale.

---

## 5. Development Roadmap & Implementation Steps

```
Phase 1: Project Setup & Backend Architecture
 ├── Initialize FastAPI backend with REST & WebSocket endpoints
 ├── Configure SQLite/Spatialite schemas (cameras, detections, blacklist, trajectories)
 └── Build asynchronous event ingestion pipeline

Phase 2: Computer Vision & ANPR Pipeline
 ├── Integrate YOLO vehicle + license plate detector
 ├── Implement 4-corner perspective rectification warp
 ├── Integrate PaddleOCR/EasyOCR with Indian plate format filters
 └── Implement multi-frame voting & Levenshtein resolution service

Phase 3: Command Center GIS Frontend (React + Vite)
 ├── Build Command Center Layout (Dark modern theme)
 ├── Multi-Camera Live Grid & Real-time detection ticker
 ├── Trajectory Reconstruction Center with route animation & speed timeline
 ├── Urban Analytics Dashboard (Deck.gl heatmap, O-D matrix, volume charts)
 └── Blacklist & Anomaly Alert Hub with live notification toast & sound

Phase 4: City Simulation & End-to-End Demo Setup
 ├── Pre-load sample CCTV clips & synthetic city-wide telemetry
 ├── Test end-to-end flow: Video -> Detection -> Trajectory -> Alert
 └── Final polish & demo rehearsal
```

---

## 6. Datasets & Model Training Strategy

| Dataset | Usage in Prototype |
| :--- | :--- |
| **CCPD (Chinese City Parking Dataset)** | Pre-training vehicle and plate localization under diverse angles & lighting. |
| **Roboflow Universe (Indian Plates)** | Fine-tuning plate localization and OCR on Indian font styles, colors, and layouts. |
| **UFPR-ALPR Dataset** | Robustness training on occluded, low-light, and motion-blurred plates. |
| **Synthetic Indian Plate Generator** | Generating programmatic edge cases (damaged plates, rain artifacts, high tilt). |
