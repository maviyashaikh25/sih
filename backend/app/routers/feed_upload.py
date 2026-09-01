import sys
import os
import shutil
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List
import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

# Add project root to sys.path so ai_pipeline can be imported reliably
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.database import get_db
from app.models import Camera, Detection
from app.services.alert_service import AlertService
from app.websocket_manager import ws_manager

# AI Pipeline imports (lazily loaded to keep startup instant)
_detector = None
_ocr_engine = None

def get_ai_engines():
    global _detector, _ocr_engine
    if _detector is None:
        from ai_pipeline.detector import VehicleDetector
        _detector = VehicleDetector()
    if _ocr_engine is None:
        from ai_pipeline.ocr_engine import PlateOCREngine
        _ocr_engine = PlateOCREngine(use_deep_ocr=True) # Real Deep Learning PyTorch EasyOCR
    return _detector, _ocr_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feed", tags=["Custom Feed Upload"])

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploaded_feeds"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_and_process_feed(
    file: UploadFile = File(...),
    camera_id: str = Form(...),
    camera_name: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    zone: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Ingest user-uploaded CCTV video clips or high-resolution camera images:
    1. Saves media to disk
    2. Registers or updates Camera Node in database
    3. Runs YOLO vehicle detection + Plate OCR pipeline
    4. Records timestamped events in database
    5. Evaluates real-time hotlist and anomaly alerts
    6. Broadcasts results via WebSocket
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_ext = os.path.splitext(file.filename)[1].lower()
    is_video = file_ext in [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    is_image = file_ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]

    if not is_video and not is_image:
        raise HTTPException(status_code=400, detail=f"Unsupported file format {file_ext}. Please upload a video (.mp4/.mov/.avi) or image (.jpg/.png).")

    unique_filename = f"{uuid.uuid4().hex[:8]}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 1. Register Camera if not present
    cam = db.query(Camera).filter(Camera.id == camera_id).first()
    if not cam:
        cam = Camera(
            id=camera_id,
            name=camera_name or f"User Camera {camera_id}",
            latitude=latitude if latitude is not None else 28.6139 + (len(camera_id) * 0.005),
            longitude=longitude if longitude is not None else 77.2090 + (len(camera_id) * 0.004),
            zone=zone or "Custom Zone",
            road_name="Custom Ingest Point",
            camera_type="User Upload Stream",
            status="ACTIVE"
        )
        db.add(cam)
        db.commit()
        db.refresh(cam)
    else:
        # Update details if provided
        if camera_name: cam.name = camera_name
        if latitude is not None: cam.latitude = latitude
        if longitude is not None: cam.longitude = longitude
        if zone: cam.zone = zone
        db.commit()

    detector, ocr_engine = get_ai_engines()
    processed_detections = []
    triggered_alerts = []
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

    overlay_boxes = []
    video_keyframes = []

    # 2. Process Image or Video
    if is_image:
        frame = cv2.imread(file_path)
        if frame is not None:
            fh, fw = frame.shape[:2]
            dets = detector.detect_vehicles(frame)
            for d in dets:
                plate_crop = d["plate_crop"]
                v_type = d["vehicle_type"]
                v_color = d["vehicle_color"]
                
                plate_str = None
                conf = 0.70
                raw_str = ""

                if plate_crop is not None and plate_crop.size > 0:
                    plate_str, ocr_conf, raw_str = ocr_engine.extract_text_from_plate(plate_crop)
                    if ocr_conf > 0:
                        conf = float(ocr_conf)

                bx1, by1, bx2, by2 = d["vehicle_bbox"]

                if plate_str and len(plate_str) >= 4:
                    norm_plate = plate_str.replace(" ", "").upper()

                    detection = Detection(
                        camera_id=cam.id,
                        plate_number=norm_plate,
                        raw_plate=raw_str or norm_plate,
                        confidence=min(0.99, max(0.50, conf)),
                        vehicle_type=v_type,
                        vehicle_color=v_color,
                        direction="Stationary/Ingest",
                        speed_estimate_kmh=0.0,
                        crop_image_url=f"/uploaded_feeds/{unique_filename}",
                        timestamp=now_utc
                    )
                    db.add(detection)
                    db.commit()
                    db.refresh(detection)

                    alerts = AlertService.check_and_generate_alerts(db, detection)
                    for a in alerts:
                        triggered_alerts.append(a.message)

                    is_hotlist = len(alerts) > 0

                    overlay_boxes.append({
                        "plate": detection.plate_number,
                        "conf": round(detection.confidence, 2),
                        "top": f"{round((by1 / fh) * 100, 1)}%",
                        "left": f"{round((bx1 / fw) * 100, 1)}%",
                        "width": f"{round(((bx2 - bx1) / fw) * 100, 1)}%",
                        "height": f"{round(((by2 - by1) / fh) * 100, 1)}%",
                        "type": f"{v_color} {v_type}",
                        "speed": "0 km/h",
                        "hotlist": is_hotlist
                    })

                    det_event = {
                        "id": detection.id,
                        "camera_id": cam.id,
                        "camera_name": cam.name,
                        "zone": cam.zone,
                        "latitude": cam.latitude,
                        "longitude": cam.longitude,
                        "plate_number": detection.plate_number,
                        "confidence": detection.confidence,
                        "vehicle_type": detection.vehicle_type,
                        "vehicle_color": detection.vehicle_color,
                        "speed_estimate_kmh": detection.speed_estimate_kmh,
                        "direction": detection.direction,
                        "hotlist": is_hotlist,
                        "timestamp": detection.timestamp.isoformat()
                    }
                    processed_detections.append(det_event)
                    await ws_manager.broadcast("DETECTION", det_event)
                else:
                    # Visual overlay without plate text (No fake data saved to database)
                    overlay_boxes.append({
                        "plate": "NO_PLATE_READ",
                        "conf": round(conf, 2),
                        "top": f"{round((by1 / fh) * 100, 1)}%",
                        "left": f"{round((bx1 / fw) * 100, 1)}%",
                        "width": f"{round(((bx2 - bx1) / fw) * 100, 1)}%",
                        "height": f"{round(((by2 - by1) / fh) * 100, 1)}%",
                        "type": f"{v_color} {v_type}",
                        "speed": "0 km/h",
                        "hotlist": False
                    })

    elif is_video:
        from ai_pipeline.multi_frame_voting import MultiFramePlateAggregator
        
        cap = cv2.VideoCapture(file_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        frame_idx = 0
        max_sample_frames = 250
        step = 5 # Sample every 5th frame for balanced coverage & speed

        aggregator = MultiFramePlateAggregator()
        active_tracks = {} # track_id -> {cx, cy, time}
        track_meta = {} # track_id -> {type, color, speeds, directions, bboxes}
        next_track_id = 1

        raw_keyframes = [] # list of (time, list of {box info, track_id})

        while cap.isOpened() and frame_idx < max_sample_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_idx += 1
            if frame_idx % step != 0:
                continue

            fh, fw = frame.shape[:2]
            current_time_sec = round(frame_idx / fps, 2)
            dets = detector.detect_vehicles(frame)
            current_frame_boxes = []

            for d in dets:
                bx1, by1, bx2, by2 = d["vehicle_bbox"]
                cx, cy = (bx1 + bx2) / 2.0, (by1 + by2) / 2.0
                v_type = d["vehicle_type"]
                v_color = d["vehicle_color"]
                plate_crop = d["plate_crop"]

                # Match with previous track
                matched_track_id = None
                min_dist = float("inf")
                for tid, tdata in list(active_tracks.items()):
                    dist = np.hypot(cx - tdata["cx"], cy - tdata["cy"])
                    if dist < min_dist and dist < (fw * 0.20):
                        min_dist = dist
                        matched_track_id = tid

                # Speed estimation
                dt = (step / fps)
                estimated_speed = 35.0
                direction_label = "Northbound"
                
                if matched_track_id is not None:
                    prev = active_tracks[matched_track_id]
                    dy = cy - prev["cy"]
                    dx = cx - prev["cx"]
                    pixel_dist = np.hypot(dx, dy)
                    speed_scale = (fh / 20.0)
                    speed_mps = (pixel_dist / max(0.01, dt)) / max(1.0, speed_scale)
                    computed_kmh = speed_mps * 3.6
                    estimated_speed = round(min(120.0, max(10.0, computed_kmh)), 1)
                    direction_label = "Southbound" if dy > 0 else "Northbound"
                    active_tracks[matched_track_id] = {"cx": cx, "cy": cy, "time": current_time_sec}
                else:
                    active_tracks[next_track_id] = {"cx": cx, "cy": cy, "time": current_time_sec}
                    matched_track_id = next_track_id
                    next_track_id += 1

                # Initialize or update track metadata
                if matched_track_id not in track_meta:
                    track_meta[matched_track_id] = {
                        "type": v_type,
                        "color": v_color,
                        "speeds": [estimated_speed],
                        "direction": direction_label,
                        "last_bbox": (bx1, by1, bx2, by2)
                    }
                else:
                    track_meta[matched_track_id]["speeds"].append(estimated_speed)
                    track_meta[matched_track_id]["direction"] = direction_label
                    track_meta[matched_track_id]["last_bbox"] = (bx1, by1, bx2, by2)
                    if v_color != "Unknown":
                        track_meta[matched_track_id]["color"] = v_color

                # Extract plate OCR on crop
                if plate_crop is not None and plate_crop.size > 0:
                    extracted_text, ocr_conf, raw_str = ocr_engine.extract_text_from_plate(plate_crop)
                    if extracted_text and len(extracted_text) >= 6 and ocr_conf >= 0.50:
                        aggregator.add_frame_read(matched_track_id, extracted_text, ocr_conf)

                current_frame_boxes.append({
                    "track_id": matched_track_id,
                    "top": f"{round((by1 / fh) * 100, 1)}%",
                    "left": f"{round((bx1 / fw) * 100, 1)}%",
                    "width": f"{round(((bx2 - bx1) / fw) * 100, 1)}%",
                    "height": f"{round(((by2 - by1) / fh) * 100, 1)}%",
                    "type": f"{v_color} {v_type}",
                    "speed": f"{int(estimated_speed)} km/h",
                    "hotlist": False
                })

            if current_frame_boxes:
                raw_keyframes.append({
                    "time": current_time_sec,
                    "boxes": current_frame_boxes
                })

        cap.release()

        # Resolve consensus detections per track
        track_to_plate = {}
        for tid, meta in track_meta.items():
            consensus = aggregator.resolve_consensus_plate(tid)
            if consensus:
                resolved_plate, consensus_conf, obs_count = consensus
                norm_plate = resolved_plate.replace(" ", "").upper()
                avg_speed = round(float(np.mean(meta["speeds"])), 1) if meta["speeds"] else 35.0

                detection = Detection(
                    camera_id=cam.id,
                    plate_number=norm_plate,
                    raw_plate=norm_plate,
                    confidence=min(0.99, max(0.60, consensus_conf)),
                    vehicle_type=meta["type"],
                    vehicle_color=meta["color"],
                    direction=meta["direction"],
                    speed_estimate_kmh=avg_speed,
                    crop_image_url=f"/uploaded_feeds/{unique_filename}",
                    timestamp=now_utc
                )
                db.add(detection)
                db.commit()
                db.refresh(detection)

                alerts = AlertService.check_and_generate_alerts(db, detection)
                for a in alerts:
                    triggered_alerts.append(a.message)

                is_hotlist = len(alerts) > 0
                track_to_plate[tid] = (norm_plate, consensus_conf, is_hotlist)

                det_event = {
                    "id": detection.id,
                    "camera_id": cam.id,
                    "camera_name": cam.name,
                    "zone": cam.zone,
                    "latitude": cam.latitude,
                    "longitude": cam.longitude,
                    "plate_number": detection.plate_number,
                    "confidence": detection.confidence,
                    "vehicle_type": detection.vehicle_type,
                    "vehicle_color": detection.vehicle_color,
                    "speed_estimate_kmh": detection.speed_estimate_kmh,
                    "direction": detection.direction,
                    "hotlist": is_hotlist,
                    "timestamp": detection.timestamp.isoformat()
                }
                processed_detections.append(det_event)
                await ws_manager.broadcast("DETECTION", det_event)

        # Update video keyframes with recognized plates
        for kf in raw_keyframes:
            resolved_boxes = []
            for b in kf["boxes"]:
                tid = b["track_id"]
                if tid in track_to_plate:
                    plate_str, conf, hotlist = track_to_plate[tid]
                    resolved_boxes.append({
                        "plate": plate_str,
                        "conf": round(conf, 2),
                        "top": b["top"],
                        "left": b["left"],
                        "width": b["width"],
                        "height": b["height"],
                        "type": b["type"],
                        "speed": b["speed"],
                        "hotlist": hotlist
                    })
                else:
                    resolved_boxes.append({
                        "plate": b["type"],
                        "conf": 0.80,
                        "top": b["top"],
                        "left": b["left"],
                        "width": b["width"],
                        "height": b["height"],
                        "type": b["type"],
                        "speed": b["speed"],
                        "hotlist": False
                    })
            video_keyframes.append({
                "time": kf["time"],
                "boxes": resolved_boxes
            })

    return {
        "success": True,
        "message": f"Successfully processed {file.filename} for Camera {cam.id}",
        "camera_id": cam.id,
        "camera_name": cam.name,
        "feed_url": f"/uploaded_feeds/{unique_filename}",
        "media_type": "video" if is_video else "image",
        "detections_count": len(processed_detections),
        "detections": processed_detections,
        "overlay_boxes": overlay_boxes,
        "video_keyframes": video_keyframes,
        "alerts_triggered": triggered_alerts
    }
