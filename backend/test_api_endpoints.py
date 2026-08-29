import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

from fastapi.testclient import TestClient
from app.main import app

def test_api():
    with TestClient(app) as client:
        print("1. Testing Root & Health...")
        r = client.get("/")
        assert r.status_code == 200
        print("  GET / ->", r.json())

        r = client.get("/health")
        assert r.status_code == 200
        print("  GET /health ->", r.json())

        print("\n2. Testing Cameras API...")
        r = client.get("/api/v1/cameras/")
        assert r.status_code == 200
        cameras = r.json()
        print(f"  GET /api/v1/cameras/ -> {len(cameras)} cameras registered")

        print("\n3. Testing Trajectory Query API...")
        r = client.get("/api/v1/trajectories/query?plate=DL01AB1234")
        assert r.status_code == 200
        traj = r.json()
        print(f"  GET /api/v1/trajectories/query -> Plate: {traj['plate_number']}, Distance: {traj['total_distance_km']} km, Points: {len(traj['points'])}")

        print("\n4. Testing Macro Analytics API...")
        r = client.get("/api/v1/analytics/macro")
        assert r.status_code == 200
        analytics = r.json()
        print(f"  GET /api/v1/analytics/macro -> Total Detections: {analytics['total_detections_today']}, Heatmap Nodes: {len(analytics['heatmap'])}, OD Pairs: {len(analytics['od_matrix'])}")

        print("\n5. Testing Alerts & Blacklist API...")
        r = client.get("/api/v1/alerts/")
        assert r.status_code == 200
        alerts = r.json()
        print(f"  GET /api/v1/alerts/ -> {len(alerts)} alerts retrieved")

        r = client.get("/api/v1/alerts/blacklist")
        assert r.status_code == 200
        bl = r.json()
        print(f"  GET /api/v1/alerts/blacklist -> {len(bl)} blacklisted vehicles")

        print("\n6. Testing Detection Ingestion API...")
        ingest_payload = {
            "camera_id": "CAM_CP_01",
            "plate_number": "DL01AB1234",
            "raw_plate": "DL01AB1234",
            "confidence": 0.98,
            "vehicle_type": "SUV",
            "vehicle_color": "Black",
            "direction": "Northbound",
            "speed_estimate_kmh": 46.5
        }
        r = client.post("/api/v1/detections/ingest", json=ingest_payload)
        assert r.status_code == 201
        print(f"  POST /api/v1/detections/ingest -> ID: {r.json()['id']}, Plate: {r.json()['plate_number']}")

        print("\n7. Testing Simulation Trigger...")
        r = client.post("/api/v1/simulation/trigger_step")
        assert r.status_code == 200
        print("  POST /api/v1/simulation/trigger_step ->", r.json()['status'])

        print("\n[SUCCESS] All FastAPI REST Endpoints & Lifespan Hooks verified successfully!")

if __name__ == "__main__":
    test_api()
