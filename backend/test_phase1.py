import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath("backend"))

from app.database import engine, Base, SessionLocal
from app.models import Camera, Detection, Blacklist, Alert
from app.services.simulation_service import SimulationService
from app.services.trajectory_service import TrajectoryService
from app.services.analytics_service import AnalyticsService

print("1. Creating database tables...")
Base.metadata.create_all(bind=engine)

print("2. Seeding initial data...")
db = SessionLocal()
SimulationService.seed_initial_data(db)

print(f"Total Cameras in DB: {db.query(Camera).count()}")
print(f"Total Detections in DB: {db.query(Detection).count()}")
print(f"Total Blacklist Entries: {db.query(Blacklist).count()}")
print(f"Total Alerts: {db.query(Alert).count()}")

print("\n3. Testing Trajectory Query for DL01AB1234 (Hotlist Scorpio)...")
traj = TrajectoryService.get_vehicle_trajectory(db, "DL01AB1234")
if traj:
    print(f"  Vehicle: {traj.plate_number}")
    print(f"  Sightings: {traj.total_sightings}")
    print(f"  Total Distance: {traj.total_distance_km} km")
    print(f"  Avg Speed: {traj.average_speed_kmh} km/h")
    print(f"  Origin: {traj.origin_zone} -> Dest: {traj.destination_zone}")
    print(f"  Camera Hops: {' -> '.join([p.camera_id for p in traj.points])}")
else:
    print("  Trajectory not found!")

print("\n4. Testing Macro Analytics...")
analytics = AnalyticsService.get_macro_analytics(db)
print(f"  Detections Today: {analytics.total_detections_today}")
print(f"  Heatmap Points Count: {len(analytics.heatmap)}")
print(f"  Top O-D Routes: {len(analytics.od_matrix)}")
print(f"  Bottleneck Alerts: {len(analytics.bottlenecks)}")

db.close()
print("\n[SUCCESS] All Phase 1 Backend Services and DB Queries passed successfully!")
