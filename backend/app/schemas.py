from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# --- Camera Schemas ---
class CameraBase(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    zone: str
    road_name: Optional[str] = None
    camera_type: Optional[str] = "ANPR_4K_PTZ"
    is_active: Optional[bool] = True
    fps: Optional[int] = 30

class CameraCreate(CameraBase):
    pass

class CameraResponse(CameraBase):
    created_at: datetime
    class Config:
        from_attributes = True

# --- Detection Schemas ---
class DetectionBase(BaseModel):
    camera_id: str
    plate_number: str
    raw_plate: Optional[str] = None
    confidence: float = 0.95
    vehicle_type: Optional[str] = "Car"
    vehicle_color: Optional[str] = "White"
    direction: Optional[str] = "Northbound"
    speed_estimate_kmh: Optional[float] = 45.0
    crop_image_url: Optional[str] = None
    timestamp: Optional[datetime] = None

class DetectionCreate(DetectionBase):
    pass

class DetectionResponse(DetectionBase):
    id: int
    timestamp: datetime
    class Config:
        from_attributes = True

# --- Trajectory Schemas ---
class TrajectoryPoint(BaseModel):
    camera_id: str
    camera_name: str
    latitude: float
    longitude: float
    zone: str
    timestamp: datetime
    speed_estimate_kmh: float
    vehicle_type: str
    vehicle_color: str
    confidence: float

class TrajectorySegment(BaseModel):
    from_camera_id: str
    to_camera_id: str
    from_coords: List[float]
    to_coords: List[float]
    distance_km: float
    duration_seconds: float
    computed_speed_kmh: float
    road_polyline: Optional[List[List[float]]] = None

class TrajectoryResponse(BaseModel):
    plate_number: str
    total_sightings: int
    first_seen: datetime
    last_seen: datetime
    total_distance_km: float
    average_speed_kmh: float
    origin_zone: str
    destination_zone: str
    points: List[TrajectoryPoint]
    segments: List[TrajectorySegment]

# --- Alert Schemas ---
class AlertBase(BaseModel):
    alert_type: str
    plate_number: str
    camera_id: str
    severity: str = "HIGH"
    message: str
    details_json: Optional[str] = None

class AlertCreate(AlertBase):
    pass

class AlertResponse(AlertBase):
    id: int
    timestamp: datetime
    is_resolved: bool
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    camera: Optional[CameraResponse] = None
    class Config:
        from_attributes = True

# --- Blacklist Schemas ---
class BlacklistBase(BaseModel):
    plate_number: str
    reason: str
    severity: str = "HIGH"
    owner_name: Optional[str] = None
    vehicle_details: Optional[str] = None
    is_active: Optional[bool] = True

class BlacklistCreate(BlacklistBase):
    pass

class BlacklistResponse(BlacklistBase):
    id: int
    added_at: datetime
    class Config:
        from_attributes = True

# --- Analytics Schemas ---
class DensityHeatmapPoint(BaseModel):
    camera_id: str
    camera_name: str
    latitude: float
    longitude: float
    vehicle_count: int
    intensity: float # normalized 0.0 to 1.0
    congestion_level: str # LOW, MEDIUM, HIGH, CRITICAL

class ODMatrixItem(BaseModel):
    origin_zone: str
    destination_zone: str
    trip_count: int
    avg_travel_time_min: float
    avg_speed_kmh: float

class BottleneckAlert(BaseModel):
    camera_id: str
    camera_name: str
    zone: str
    current_count_per_min: int
    threshold: int
    severity: str
    status: str

class TrafficAnalyticsResponse(BaseModel):
    total_detections_today: int
    active_cameras_count: int
    active_alerts_count: int
    average_city_speed: float
    heatmap: List[DensityHeatmapPoint]
    od_matrix: List[ODMatrixItem]
    bottlenecks: List[BottleneckAlert]
    hourly_volume_series: List[dict]
    vehicle_breakdown: Optional[Dict[str, int]] = None
