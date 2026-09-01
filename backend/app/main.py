import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import Camera, Detection, Blacklist, Alert
from app.services.simulation_service import SimulationService
from app.websocket_manager import ws_manager

import os
from fastapi.staticfiles import StaticFiles

# Import API routers
from app.routers import cameras, detections, trajectories, analytics, alerts, simulation, feed_upload

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup: Create DB schema and seed initial data
    logger.info("Creating database tables if not present...")
    Base.metadata.create_all(bind=engine)

    logger.info("Checking and seeding initial city cameras, hotlist, and sample trajectories...")
    db = SessionLocal()
    try:
        SimulationService.seed_initial_data(db)
    finally:
        db.close()

    logger.info(f"{settings.PROJECT_NAME} backend started successfully.")
    yield
    # 2. Shutdown
    logger.info("Shutting down backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Centralized AI Platform for City-Wide ANPR Intelligence, Trajectory Tracking & Macro Traffic Analytics",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for user-uploaded camera feeds
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "uploaded_feeds"))
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploaded_feeds", StaticFiles(directory=UPLOAD_DIR), name="uploaded_feeds")

# Include Routers with API v1 prefix
app.include_router(cameras.router, prefix=settings.API_V1_STR)
app.include_router(detections.router, prefix=settings.API_V1_STR)
app.include_router(trajectories.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(alerts.router, prefix=settings.API_V1_STR)
app.include_router(simulation.router, prefix=settings.API_V1_STR)
app.include_router(feed_upload.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time live telemetry, new plate detections, 
    traffic density updates, and instant security alerts.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep-alive receive loop
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client error: {e}")
        ws_manager.disconnect(websocket)
