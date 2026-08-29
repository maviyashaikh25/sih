import asyncio
import logging
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.services.simulation_service import SimulationService

router = APIRouter(prefix="/simulation", tags=["City Simulation"])
logger = logging.getLogger(__name__)

simulation_running = False
simulation_task = None

async def simulation_loop():
    global simulation_running
    logger.info("Starting background city simulation loop...")
    while simulation_running:
        try:
            db = SessionLocal()
            await SimulationService.run_live_simulation_step(db)
            db.close()
        except Exception as e:
            logger.error(f"Error in simulation step: {e}")
        await asyncio.sleep(2.5) # Emit event every 2.5 seconds

@router.post("/start")
async def start_simulation():
    global simulation_running, simulation_task
    if not simulation_running:
        simulation_running = True
        simulation_task = asyncio.create_task(simulation_loop())
        return {"status": "started", "message": "City traffic simulation is now active"}
    return {"status": "running", "message": "Simulation was already running"}

@router.post("/stop")
async def stop_simulation():
    global simulation_running, simulation_task
    if simulation_running:
        simulation_running = False
        if simulation_task:
            simulation_task.cancel()
            simulation_task = None
        return {"status": "stopped", "message": "City traffic simulation stopped"}
    return {"status": "idle", "message": "Simulation is not currently running"}

@router.get("/status")
def get_simulation_status():
    return {"running": simulation_running}

@router.post("/trigger_step")
async def trigger_single_step(db: Session = Depends(get_db)):
    """Triggers a single live simulation event on demand."""
    det = await SimulationService.run_live_simulation_step(db)
    return {"status": "success", "detection": det}
