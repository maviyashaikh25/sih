from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import json
from sqlalchemy.orm import Session
from geopy.distance import geodesic

from app.models import Blacklist, Alert, Detection, Camera
from app.config import settings

class AlertService:
    @staticmethod
    def check_and_generate_alerts(db: Session, detection: Detection) -> list[Alert]:
        """
        Runs real-time rule engine on incoming detection:
        1. Hotlist / Blacklist match
        2. Impossible-speed teleportation anomaly (cloned plates)
        3. Frequent zone circling / loitering anomaly
        """
        generated_alerts = []

        # 1. Hotlist / Blacklist Match Check
        blacklist_entry = (
            db.query(Blacklist)
            .filter(Blacklist.plate_number == detection.plate_number, Blacklist.is_active == True)
            .first()
        )

        if blacklist_entry:
            alert = Alert(
                alert_type="BLACKLIST_MATCH",
                plate_number=detection.plate_number,
                camera_id=detection.camera_id,
                timestamp=detection.timestamp,
                severity=blacklist_entry.severity,
                message=f"Hotlist Alert: {detection.plate_number} detected at {detection.camera_id} - Reason: {blacklist_entry.reason}",
                details_json=json.dumps({
                    "reason": blacklist_entry.reason,
                    "owner": blacklist_entry.owner_name,
                    "vehicle_details": blacklist_entry.vehicle_details,
                    "confidence": detection.confidence
                })
            )
            db.add(alert)
            generated_alerts.append(alert)

        # 2. Impossible Speed / Cloned Plate Detection
        previous_detection = (
            db.query(Detection)
            .join(Camera, Detection.camera_id == Camera.id)
            .filter(
                Detection.plate_number == detection.plate_number,
                Detection.id != detection.id,
                Detection.timestamp < detection.timestamp
            )
            .order_by(Detection.timestamp.desc())
            .first()
        )

        if previous_detection and previous_detection.camera_id != detection.camera_id:
            curr_cam = db.query(Camera).filter(Camera.id == detection.camera_id).first()
            prev_cam = previous_detection.camera

            if curr_cam and prev_cam:
                coord1 = (prev_cam.latitude, prev_cam.longitude)
                coord2 = (curr_cam.latitude, curr_cam.longitude)
                dist_km = geodesic(coord1, coord2).kilometers
                time_delta_sec = (detection.timestamp - previous_detection.timestamp).total_seconds()

                if time_delta_sec > 0:
                    speed_kmh = dist_km / (time_delta_sec / 3600.0)
                    if speed_kmh > settings.SPEED_LIMIT_ANOMALY_KMH:
                        alert = Alert(
                            alert_type="IMPOSSIBLE_SPEED",
                            plate_number=detection.plate_number,
                            camera_id=detection.camera_id,
                            timestamp=detection.timestamp,
                            severity="CRITICAL",
                            message=f"Possible Cloned Plate: {detection.plate_number} traversed {dist_km:.1f} km in {time_delta_sec:.0f}s ({speed_kmh:.0f} km/h)",
                            details_json=json.dumps({
                                "prev_camera": prev_cam.id,
                                "prev_time": str(previous_detection.timestamp),
                                "calculated_speed_kmh": round(speed_kmh, 1),
                                "distance_km": round(dist_km, 2)
                            })
                        )
                        db.add(alert)
                        generated_alerts.append(alert)

        # 3. Suspicious Loitering / Zone Circling Detection
        ten_mins_ago = detection.timestamp - timedelta(minutes=15)
        recent_hits_same_cam = (
            db.query(Detection)
            .filter(
                Detection.plate_number == detection.plate_number,
                Detection.camera_id == detection.camera_id,
                Detection.timestamp >= ten_mins_ago
            )
            .count()
        )

        if recent_hits_same_cam >= 3:
            # Check if alert already raised in last 15 min to prevent spam
            existing_loiter_alert = (
                db.query(Alert)
                .filter(
                    Alert.alert_type == "ZONE_LOITERING",
                    Alert.plate_number == detection.plate_number,
                    Alert.camera_id == detection.camera_id,
                    Alert.timestamp >= ten_mins_ago
                )
                .first()
            )
            if not existing_loiter_alert:
                alert = Alert(
                    alert_type="ZONE_LOITERING",
                    plate_number=detection.plate_number,
                    camera_id=detection.camera_id,
                    timestamp=detection.timestamp,
                    severity="MEDIUM",
                    message=f"Loitering Alert: {detection.plate_number} spotted {recent_hits_same_cam} times in 15 mins at {detection.camera_id}",
                    details_json=json.dumps({
                        "sightings_in_window": recent_hits_same_cam,
                        "time_window_minutes": 15
                    })
                )
                db.add(alert)
                generated_alerts.append(alert)

        if generated_alerts:
            db.commit()
            for a in generated_alerts:
                db.refresh(a)

        return generated_alerts
