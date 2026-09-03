import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "City-Wide ANPR Intelligence Platform"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./anpr_platform.db")
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]
    # Default city center coordinates (New Delhi as prototype benchmark)
    DEFAULT_CITY_LAT: float = 28.6139
    DEFAULT_CITY_LNG: float = 77.2090
    SPEED_LIMIT_ANOMALY_KMH: float = 140.0  # Impossible speed threshold indicating cloned plates / errors

settings = Settings()
