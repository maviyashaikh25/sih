from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(String(50), primary_key=True, index=True) # e.g. "CAM_CP_01"
    name = Column(String(100), nullable=False)             # e.g. "Connaught Place Radial 1"
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    zone = Column(String(50), nullable=False, index=True)  # e.g. "Central", "North", "South"
    road_name = Column(String(100), nullable=True)
    camera_type = Column(String(50), default="ANPR_4K_PTZ")
    is_active = Column(Boolean, default=True)
    fps = Column(Integer, default=30)
    created_at = Column(DateTime, default=utc_now)

    detections = relationship("Detection", back_populates="camera", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="camera")

class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(String(50), ForeignKey("cameras.id"), nullable=False, index=True)
    plate_number = Column(String(20), nullable=False, index=True) # Resolved normalized plate e.g. "DL01AB1234"
    raw_plate = Column(String(20), nullable=True)                 # Raw OCR output before fuzzy resolution
    confidence = Column(Float, default=0.95)                      # OCR / Detection confidence
    vehicle_type = Column(String(30), default="Car")             # Car, SUV, Bus, Truck, Bike, Auto
    vehicle_color = Column(String(30), default="White")
    direction = Column(String(20), default="Northbound")
    speed_estimate_kmh = Column(Float, default=45.0)
    crop_image_url = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=utc_now, index=True)

    camera = relationship("Camera", back_populates="detections")

    __table_args__ = (
        Index("idx_plate_time", "plate_number", "timestamp"),
        Index("idx_cam_time", "camera_id", "timestamp"),
    )

class Blacklist(Base):
    __tablename__ = "blacklist"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plate_number = Column(String(20), unique=True, nullable=False, index=True)
    reason = Column(String(255), nullable=False)                   # e.g. "Stolen Vehicle", "Wanted in FIR #204", "Unpaid Challans"
    severity = Column(String(20), default="HIGH")                  # CRITICAL, HIGH, MEDIUM
    owner_name = Column(String(100), nullable=True)
    vehicle_details = Column(String(255), nullable=True)           # e.g. "Red Hyundai Creta 2022"
    is_active = Column(Boolean, default=True)
    added_at = Column(DateTime, default=utc_now)

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_type = Column(String(50), nullable=False, index=True)   # BLACKLIST_MATCH, IMPOSSIBLE_SPEED, ZONE_LOITERING, GEOFENCE_BREACH
    plate_number = Column(String(20), nullable=False, index=True)
    camera_id = Column(String(50), ForeignKey("cameras.id"), nullable=False)
    timestamp = Column(DateTime, default=utc_now, index=True)
    severity = Column(String(20), default="HIGH")                  # CRITICAL, HIGH, MEDIUM, LOW
    message = Column(String(255), nullable=False)
    details_json = Column(Text, nullable=True)                    # JSON data for extra context
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    camera = relationship("Camera", back_populates="alerts")

class TrajectorySummary(Base):
    __tablename__ = "trajectory_summaries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plate_number = Column(String(20), nullable=False, index=True)
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    total_hops = Column(Integer, default=1)
    total_distance_km = Column(Float, default=0.0)
    avg_speed_kmh = Column(Float, default=0.0)
    origin_camera_id = Column(String(50), nullable=True)
    destination_camera_id = Column(String(50), nullable=True)
    updated_at = Column(DateTime, default=utc_now)

class HourlyTrafficStat(Base):
    __tablename__ = "hourly_traffic_stats"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(String(50), nullable=False, index=True)
    hour_timestamp = Column(DateTime, nullable=False, index=True)
    vehicle_count = Column(Integer, default=0)
    avg_speed = Column(Float, default=0.0)
    congestion_index = Column(Float, default=0.0) # 0.0 to 1.0
