from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from geopy.distance import geodesic

from app.models import Detection, Camera
from app.schemas import TrajectoryResponse, TrajectoryPoint, TrajectorySegment

def compute_distance_km(coord1: tuple[float, float], coord2: tuple[float, float]) -> float:
    """Computes geodesic distance between two (lat, lon) coordinates in kilometers."""
    return geodesic(coord1, coord2).kilometers

def generate_interpolated_route(coord1: list[float], coord2: list[float], steps: int = 5) -> list[list[float]]:
    """
    Generates a realistic smooth polyline between two camera points 
    simulating intermediate road path steps.
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    points = []
    for i in range(steps + 1):
        ratio = i / float(steps)
        # Slight jitter/bezier curvature to mimic real urban road curves
        jitter_lat = (0.0005 if i % 2 == 1 else -0.0003) * (1 - abs(2 * ratio - 1))
        jitter_lon = (0.0004 if i % 2 == 0 else -0.0004) * (1 - abs(2 * ratio - 1))
        inter_lat = lat1 + (lat2 - lat1) * ratio + jitter_lat
        inter_lon = lon1 + (lon2 - lon1) * ratio + jitter_lon
        points.append([round(inter_lat, 6), round(inter_lon, 6)])
    return points

class TrajectoryService:
    @staticmethod
    def get_vehicle_trajectory(db: Session, plate_number: str) -> Optional[TrajectoryResponse]:
        plate_normalized = plate_number.replace(" ", "").upper()

        detections = (
            db.query(Detection)
            .join(Camera, Detection.camera_id == Camera.id)
            .filter(Detection.plate_number == plate_normalized)
            .order_by(Detection.timestamp.asc())
            .all()
        )

        if not detections:
            return None

        points: List[TrajectoryPoint] = []
        for det in detections:
            cam = det.camera
            points.append(
                TrajectoryPoint(
                    camera_id=cam.id,
                    camera_name=cam.name,
                    latitude=cam.latitude,
                    longitude=cam.longitude,
                    zone=cam.zone,
                    timestamp=det.timestamp,
                    speed_estimate_kmh=det.speed_estimate_kmh or 40.0,
                    vehicle_type=det.vehicle_type or "Car",
                    vehicle_color=det.vehicle_color or "Unknown",
                    confidence=det.confidence
                )
            )

        segments: List[TrajectorySegment] = []
        total_distance = 0.0
        total_duration_sec = 0.0

        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]

            coord1 = (p1.latitude, p1.longitude)
            coord2 = (p2.latitude, p2.longitude)
            dist_km = compute_distance_km(coord1, coord2)
            time_delta = (p2.timestamp - p1.timestamp).total_seconds()

            if time_delta > 0:
                speed_kmh = (dist_km / (time_delta / 3600.0))
            else:
                speed_kmh = p1.speed_estimate_kmh

            total_distance += dist_km
            total_duration_sec += max(time_delta, 1.0)

            polyline = generate_interpolated_route([p1.latitude, p1.longitude], [p2.latitude, p2.longitude])

            segments.append(
                TrajectorySegment(
                    from_camera_id=p1.camera_id,
                    to_camera_id=p2.camera_id,
                    from_coords=[p1.latitude, p1.longitude],
                    to_coords=[p2.latitude, p2.longitude],
                    distance_km=round(dist_km, 2),
                    duration_seconds=round(time_delta, 1),
                    computed_speed_kmh=round(speed_kmh, 1),
                    road_polyline=polyline
                )
            )

        avg_speed = (
            (total_distance / (total_duration_sec / 3600.0))
            if total_duration_sec > 0
            else (points[0].speed_estimate_kmh if points else 0.0)
        )

        return TrajectoryResponse(
            plate_number=plate_normalized,
            total_sightings=len(points),
            first_seen=points[0].timestamp,
            last_seen=points[-1].timestamp,
            total_distance_km=round(total_distance, 2),
            average_speed_kmh=round(min(avg_speed, 120.0), 1),
            origin_zone=points[0].zone,
            destination_zone=points[-1].zone,
            points=points,
            segments=segments
        )

    @staticmethod
    def get_recent_active_plates(db: Session, limit: int = 15) -> List[str]:
        results = (
            db.query(Detection.plate_number)
            .order_by(Detection.timestamp.desc())
            .distinct()
            .limit(limit)
            .all()
        )
        return [r[0] for r in results]
