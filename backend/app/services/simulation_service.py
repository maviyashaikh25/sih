import asyncio
import random
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models import Camera, Detection, Blacklist, Alert
from app.services.alert_service import AlertService
from app.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

DEFAULT_CAMERAS = [
    {"id": "CAM_CP_01", "name": "Connaught Place Radial 1", "latitude": 28.6315, "longitude": 77.2167, "zone": "Central Delhi", "road_name": "Janpath Road"},
    {"id": "CAM_CP_02", "name": "Connaught Place Outer Circle", "latitude": 28.6340, "longitude": 77.2195, "zone": "Central Delhi", "road_name": "Barakhamba Road"},
    {"id": "CAM_IG_01", "name": "India Gate C-Hexagon", "latitude": 28.6129, "longitude": 77.2295, "zone": "Central Delhi", "road_name": "Rajpath / Kartavya Path"},
    {"id": "CAM_ITO_01", "name": "ITO Crossing Junction", "latitude": 28.6291, "longitude": 77.2410, "zone": "Central Delhi", "road_name": "Vikas Marg"},
    {"id": "CAM_AIIMS_01", "name": "Ring Road - AIIMS Flyover", "latitude": 28.5672, "longitude": 77.2100, "zone": "South Delhi", "road_name": "Mahatma Gandhi Marg"},
    {"id": "CAM_LP_01", "name": "Lajpat Nagar Central Market Entry", "latitude": 28.5700, "longitude": 77.2370, "zone": "South Delhi", "road_name": "Feroze Gandhi Marg"},
    {"id": "CAM_HK_01", "name": "Hauz Khas Outer Ring Road", "latitude": 28.5494, "longitude": 77.2001, "zone": "South Delhi", "road_name": "Gamal Abdel Nasser Marg"},
    {"id": "CAM_NP_01", "name": "Nehru Place Commercial Node", "latitude": 28.5480, "longitude": 77.2510, "zone": "South Delhi", "road_name": "Lala Lajpat Rai Marg"},
    {"id": "CAM_DK_01", "name": "Dhaula Kuan Interchange", "latitude": 28.5910, "longitude": 77.1610, "zone": "South-West Delhi", "road_name": "National Highway 48"},
    {"id": "CAM_AERO_01", "name": "Aerocity Terminal Approach", "latitude": 28.5520, "longitude": 77.1210, "zone": "South-West Delhi", "road_name": "Northern Access Road"},
    {"id": "CAM_KB_01", "name": "Karol Bagh Pusa Road", "latitude": 28.6465, "longitude": 77.1915, "zone": "West Delhi", "road_name": "Pusa Road"},
    {"id": "CAM_KG_01", "name": "Kashmere Gate ISBT", "latitude": 28.6665, "longitude": 77.2285, "zone": "North Delhi", "road_name": "Lothian Road"},
]

DEFAULT_BLACKLIST = [
    {
        "plate_number": "DL01AB1234",
        "reason": "Vehicle involved in armed robbery (FIR #412/2026)",
        "severity": "CRITICAL",
        "owner_name": "Unknown / Forged Reg",
        "vehicle_details": "Black Mahindra Scorpio N"
    },
    {
        "plate_number": "HR26DQ9988",
        "reason": "Reported Stolen from Sector 29 Gurgaon",
        "severity": "HIGH",
        "owner_name": "Rajesh Kumar Sharma",
        "vehicle_details": "White Hyundai Creta SX"
    },
    {
        "plate_number": "UP16AX5544",
        "reason": "Over 18 Pending Speeding & Signal Violations",
        "severity": "MEDIUM",
        "owner_name": "Vikas Choudhary",
        "vehicle_details": "Silver Maruti Swift Dzire"
    }
]

SAMPLE_VEHICLES = [
    ("DL03CC8899", "Car", "Silver", 48.0),
    ("HR51BK4422", "SUV", "White", 52.0),
    ("UP14DT3311", "Car", "Blue", 40.0),
    ("DL09EF7711", "Truck", "Yellow", 35.0),
    ("DL01AB1234", "SUV", "Black", 55.0), # Hotlist Vehicle
    ("HR26DQ9988", "SUV", "White", 47.0), # Hotlist Vehicle
    ("DL08CA1020", "Bike", "Red", 42.0),
    ("DL10MZ6543", "Car", "Grey", 50.0),
    ("DL04JK9012", "Bus", "Green", 32.0),
    ("UP16AX5544", "Car", "Silver", 60.0), # Hotlist Vehicle
]

class SimulationService:
    @staticmethod
    def seed_initial_data(db: Session):
        # 1. Seed Cameras
        for cam_data in DEFAULT_CAMERAS:
            existing = db.query(Camera).filter(Camera.id == cam_data["id"]).first()
            if not existing:
                cam = Camera(**cam_data)
                db.add(cam)

        # 2. Seed Blacklist
        for bl_data in DEFAULT_BLACKLIST:
            existing = db.query(Blacklist).filter(Blacklist.plate_number == bl_data["plate_number"]).first()
            if not existing:
                bl = Blacklist(**bl_data)
                db.add(bl)

        db.commit()

        # 3. Seed Realistic Historical Trajectories if Detections Table is empty
        detection_count = db.query(Detection).count()
        if detection_count == 0:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            logger.info("Seeding initial realistic spatial-temporal vehicle trajectories...")

            # Corridor 1: North to South Cross-City Corridor (Kashmere Gate -> CP -> India Gate -> AIIMS -> Hauz Khas)
            corridor_1 = ["CAM_KG_01", "CAM_CP_01", "CAM_IG_01", "CAM_AIIMS_01", "CAM_HK_01"]
            plate_1 = "DL01AB1234" # Hotlist Scorpio
            for idx, cam_id in enumerate(corridor_1):
                timestamp = now - timedelta(minutes=(len(corridor_1) - idx) * 12 + 5)
                det = Detection(
                    camera_id=cam_id,
                    plate_number=plate_1,
                    raw_plate=plate_1,
                    confidence=0.96,
                    vehicle_type="SUV",
                    vehicle_color="Black",
                    direction="Southbound",
                    speed_estimate_kmh=52.0 + random.uniform(-4, 4),
                    timestamp=timestamp
                )
                db.add(det)
                db.flush()
                AlertService.check_and_generate_alerts(db, det)

            # Corridor 2: Airport Corridor (Dhaula Kuan -> Aerocity -> Hauz Khas -> Nehru Place)
            corridor_2 = ["CAM_DK_01", "CAM_AERO_01", "CAM_HK_01", "CAM_NP_01"]
            plate_2 = "HR26DQ9988" # Hotlist Creta
            for idx, cam_id in enumerate(corridor_2):
                timestamp = now - timedelta(minutes=(len(corridor_2) - idx) * 14 + 10)
                det = Detection(
                    camera_id=cam_id,
                    plate_number=plate_2,
                    raw_plate=plate_2,
                    confidence=0.94,
                    vehicle_type="SUV",
                    vehicle_color="White",
                    direction="Eastbound",
                    speed_estimate_kmh=48.0 + random.uniform(-3, 3),
                    timestamp=timestamp
                )
                db.add(det)
                db.flush()
                AlertService.check_and_generate_alerts(db, det)

            # Corridor 3: Normal Daily Commuter (West to Central: Karol Bagh -> CP -> ITO -> Lajpat Nagar)
            corridor_3 = ["CAM_KB_01", "CAM_CP_02", "CAM_ITO_01", "CAM_LP_01"]
            plate_3 = "DL03CC8899"
            for idx, cam_id in enumerate(corridor_3):
                timestamp = now - timedelta(minutes=(len(corridor_3) - idx) * 10 + 20)
                det = Detection(
                    camera_id=cam_id,
                    plate_number=plate_3,
                    raw_plate=plate_3,
                    confidence=0.98,
                    vehicle_type="Car",
                    vehicle_color="Silver",
                    direction="South-East",
                    speed_estimate_kmh=44.0 + random.uniform(-5, 5),
                    timestamp=timestamp
                )
                db.add(det)

            # Seed 50 background vehicle sightings across all cameras in the last 2 hours
            for _ in range(50):
                cam_choice = random.choice(DEFAULT_CAMERAS)["id"]
                veh_plate, v_type, v_color, v_spd = random.choice(SAMPLE_VEHICLES)
                t_offset = random.randint(5, 120)
                det = Detection(
                    camera_id=cam_choice,
                    plate_number=veh_plate,
                    raw_plate=veh_plate,
                    confidence=round(random.uniform(0.91, 0.99), 2),
                    vehicle_type=v_type,
                    vehicle_color=v_color,
                    direction=random.choice(["Northbound", "Southbound", "Eastbound", "Westbound"]),
                    speed_estimate_kmh=round(v_spd + random.uniform(-6, 8), 1),
                    timestamp=now - timedelta(minutes=t_offset)
                )
                db.add(det)

            db.commit()
            logger.info("Successfully seeded database with cameras, hotlist, and sample trajectories.")

    @staticmethod
    async def run_live_simulation_step(db: Session):
        """
        Generates 1 live synthetic detection event and broadcasts it over WebSocket.
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cam = random.choice(DEFAULT_CAMERAS)
        veh_plate, v_type, v_color, base_speed = random.choice(SAMPLE_VEHICLES)
        
        # Occasionally generate a random civilian vehicle
        if random.random() < 0.3:
            states = ["DL", "HR", "UP"]
            nums = f"{random.randint(1, 14):02d}{random.choice(['AB', 'BK', 'CZ', 'DM', 'EQ'])}{random.randint(1000, 9999)}"
            veh_plate = f"{random.choice(states)}{nums}"
            v_type = random.choice(["Car", "SUV", "Bike", "Auto", "Bus"])
            v_color = random.choice(["White", "Silver", "Grey", "Black", "Red", "Blue"])
            base_speed = 42.0

        detection = Detection(
            camera_id=cam["id"],
            plate_number=veh_plate,
            raw_plate=veh_plate,
            confidence=round(random.uniform(0.92, 0.99), 2),
            vehicle_type=v_type,
            vehicle_color=v_color,
            direction=random.choice(["Northbound", "Southbound", "Eastbound", "Westbound"]),
            speed_estimate_kmh=round(base_speed + random.uniform(-5, 7), 1),
            timestamp=now
        )
        db.add(detection)
        db.commit()
        db.refresh(detection)

        # Check alerts
        alerts = AlertService.check_and_generate_alerts(db, detection)

        # Broadcast real-time detection event
        det_data = {
            "id": detection.id,
            "camera_id": detection.camera_id,
            "camera_name": cam["name"],
            "zone": cam["zone"],
            "latitude": cam["latitude"],
            "longitude": cam["longitude"],
            "plate_number": detection.plate_number,
            "confidence": detection.confidence,
            "vehicle_type": detection.vehicle_type,
            "vehicle_color": detection.vehicle_color,
            "speed_estimate_kmh": detection.speed_estimate_kmh,
            "direction": detection.direction,
            "timestamp": detection.timestamp.isoformat()
        }
        await ws_manager.broadcast("DETECTION", det_data)

        # Broadcast alerts if any
        for alert in alerts:
            alert_data = {
                "id": alert.id,
                "alert_type": alert.alert_type,
                "plate_number": alert.plate_number,
                "camera_id": alert.camera_id,
                "camera_name": cam["name"],
                "zone": cam["zone"],
                "severity": alert.severity,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat()
            }
            await ws_manager.broadcast("ALERT", alert_data)

        return det_data
