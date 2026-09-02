from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import TrajectoryResponse
from app.services.trajectory_service import TrajectoryService

router = APIRouter(prefix="/trajectories", tags=["Trajectories"])

@router.get("/query", response_model=TrajectoryResponse)
def query_trajectory(plate: str = Query(..., description="Vehicle license plate to search"), db: Session = Depends(get_db)):
    """
    Reconstructs spatial-temporal travel history of a vehicle across all cameras chronologically.
    Returns ordered waypoint coordinates, timestamps, travel duration, and computed speeds.
    """
    trajectory = TrajectoryService.get_vehicle_trajectory(db, plate)
    if not trajectory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sightings recorded for vehicle license plate '{plate.upper()}'"
        )
    return trajectory

@router.get("/active_plates", response_model=List[str])
def get_active_plates(limit: int = 10, db: Session = Depends(get_db)):
    """Returns a list of recently active plates for auto-complete and quick inspection."""
    return TrajectoryService.get_recent_active_plates(db, limit)

@router.post("/simulate", response_model=TrajectoryResponse)
def simulate_plate_trajectory(plate: str = Query(..., description="Vehicle license plate to simulate"), db: Session = Depends(get_db)):
    """Generates and ingests a realistic 5-node city corridor trajectory for the given plate."""
    return TrajectoryService.generate_sample_route_for_plate(db, plate)

