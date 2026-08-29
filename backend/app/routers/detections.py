from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Detection, Camera
from app.schemas import DetectionCreate, DetectionResponse
from app.services.alert_service import AlertService
from app.websocket_manager import ws_manager

router = APIRouter(prefix="/detections", tags=["Detections"])

@router.post("/ingest", response_model=DetectionResponse, status_code=status.HTTP_201_CREATED)
async def ingest_detection(payload: DetectionCreate, db: Session = Depends(get_db)):
    """
    Ingestion endpoint for AI Video Pipeline / ANPR cameras to send detected plates.
    Executes real-time alert checks and broadcasts over WebSockets.
    """
    cam = db.query(Camera).filter(Camera.id == payload.camera_id).first()
    if not cam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Camera {payload.camera_id} not registered")

    norm_plate = payload.plate_number.replace(" ", "").upper()
    detection = Detection(
        camera_id=payload.camera_id,
        plate_number=norm_plate,
        raw_plate=payload.raw_plate or payload.plate_number,
        confidence=payload.confidence,
        vehicle_type=payload.vehicle_type or "Car",
        vehicle_color=payload.vehicle_color or "Unknown",
        direction=payload.direction or "Northbound",
        speed_estimate_kmh=payload.speed_estimate_kmh or 45.0,
        crop_image_url=payload.crop_image_url,
        timestamp=payload.timestamp.replace(tzinfo=None) if payload.timestamp else datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db.add(detection)
    db.commit()
    db.refresh(detection)

    # Trigger rule checks for alerts
    alerts = AlertService.check_and_generate_alerts(db, detection)

    # Broadcast detection via WebSocket
    det_event = {
        "id": detection.id,
        "camera_id": detection.camera_id,
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
        "timestamp": detection.timestamp.isoformat()
    }
    await ws_manager.broadcast("DETECTION", det_event)

    # Broadcast alerts if any
    for alert in alerts:
        alert_event = {
            "id": alert.id,
            "alert_type": alert.alert_type,
            "plate_number": alert.plate_number,
            "camera_id": alert.camera_id,
            "camera_name": cam.name,
            "zone": cam.zone,
            "severity": alert.severity,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat()
        }
        await ws_manager.broadcast("ALERT", alert_event)

    return detection

@router.get("/recent", response_model=List[DetectionResponse])
def get_recent_detections(limit: int = 25, db: Session = Depends(get_db)):
    return (
        db.query(Detection)
        .order_by(Detection.timestamp.desc())
        .limit(limit)
        .all()
    )
