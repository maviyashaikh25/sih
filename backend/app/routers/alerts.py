from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Alert, Blacklist, Camera
from app.schemas import AlertResponse, BlacklistCreate, BlacklistResponse

router = APIRouter(prefix="/alerts", tags=["Alerts & Blacklist"])

@router.get("/", response_model=List[AlertResponse])
def get_alerts(unresolved_only: bool = False, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(Alert).order_by(Alert.timestamp.desc())
    if unresolved_only:
        query = query.filter(Alert.is_resolved == False)
    return query.limit(limit).all()

@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: int, officer_name: str = "Admin", db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert {alert_id} not found")
    alert.is_resolved = True
    alert.resolved_by = officer_name
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "success", "message": f"Alert {alert_id} marked as resolved"}

# --- Blacklist / Hotlist Endpoints ---

@router.get("/blacklist", response_model=List[BlacklistResponse])
def list_blacklist(db: Session = Depends(get_db)):
    return db.query(Blacklist).order_by(Blacklist.added_at.desc()).all()

@router.post("/blacklist", response_model=BlacklistResponse, status_code=status.HTTP_201_CREATED)
def add_to_blacklist(payload: BlacklistCreate, db: Session = Depends(get_db)):
    norm_plate = payload.plate_number.replace(" ", "").upper()
    existing = db.query(Blacklist).filter(Blacklist.plate_number == norm_plate).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Plate {norm_plate} is already in the blacklist")

    bl = Blacklist(
        plate_number=norm_plate,
        reason=payload.reason,
        severity=payload.severity,
        owner_name=payload.owner_name,
        vehicle_details=payload.vehicle_details,
        is_active=payload.is_active
    )
    db.add(bl)
    db.commit()
    db.refresh(bl)
    return bl

@router.delete("/blacklist/{plate_number}")
def remove_from_blacklist(plate_number: str, db: Session = Depends(get_db)):
    norm_plate = plate_number.replace(" ", "").upper()
    bl = db.query(Blacklist).filter(Blacklist.plate_number == norm_plate).first()
    if not bl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plate {norm_plate} not in blacklist")
    db.delete(bl)
    db.commit()
    return {"status": "success", "message": f"Plate {norm_plate} removed from blacklist"}
