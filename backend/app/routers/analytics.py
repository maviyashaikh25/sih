from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import TrafficAnalyticsResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/macro", response_model=TrafficAnalyticsResponse)
def get_macro_traffic_analytics(db: Session = Depends(get_db)):
    """
    Computes city-wide macro traffic dynamics:
    - Real-time GIS density heatmap data across all camera nodes
    - Origin-Destination (O-D) matrix between city zones
    - Congestion bottlenecks and anomaly flags
    - Hourly volume series and corridor speeds
    """
    return AnalyticsService.get_macro_analytics(db)
