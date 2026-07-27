import os
from fastapi import APIRouter, HTTPException, BackgroundTasks, Response
from fastapi.responses import FileResponse
from typing import List, Dict, Any

from backend.schemas.settings import SettingsSchema
from backend.schemas.schedule import ScheduleGenerateRequest, ScheduleRowSchema
from backend.schemas.ws import WSEvent
from backend.services.storage import (
    get_settings,
    save_settings,
    list_schedules,
    get_schedule_rows,
)
from backend.services.job_manager import job_manager, ws_manager
from core.config import SCHEDULES_DIR

router = APIRouter()

# --- Settings Endpoints ---

@router.get("/settings", response_model=SettingsSchema)
async def fetch_settings():
    """Returns current user preferences and configuration."""
    return get_settings()

@router.put("/settings", response_model=SettingsSchema)
async def update_settings(settings: SettingsSchema):
    """Updates settings and broadcasts SETTINGS_UPDATED to all connected WebSocket clients."""
    updated = save_settings(settings)
    await ws_manager.broadcast(WSEvent(type="SETTINGS_UPDATED", payload=updated.model_dump()))
    return updated

# --- Schedule Endpoints ---

@router.get("/schedules")
async def fetch_schedules_list():
    """Lists available schedule files and companion metadata."""
    return list_schedules()

@router.get("/schedules/{year}", response_model=List[ScheduleRowSchema])
async def fetch_schedule_rows(year: int, mode: str = "compact"):
    """Returns parsed weekly schedule rows for grid rendering."""
    rows = get_schedule_rows(year, mode)
    return rows

@router.post("/schedules/generate", status_code=202)
async def trigger_schedule_generation(req: ScheduleGenerateRequest):
    """Triggers an ASP solver job. Enforces the single-job concurrency lock."""
    if job_manager.is_running:
        raise HTTPException(
            status_code=409,
            detail=f"A scheduling job is already running (Job ID: {job_manager.current_job_id})."
        )

    try:
        job_id = await job_manager.start_job(
            year=req.year,
            time_limit=req.time_limit or 60,
            auto_festivities=req.auto_festivities if req.auto_festivities is not None else True,
            base=req.base or "choice",
            opt=req.opt or "penalita_esponenziale"
        )
        return {"status": "job_started", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schedules/{year}/export")
async def export_schedule_csv(year: int):
    """Downloads the generated CSV schedule for the given year."""
    csv_file = SCHEDULES_DIR / f"schedule_{year}.csv"
    if not csv_file.exists():
        csv_file = SCHEDULES_DIR / f"test_{year}.csv"
    if not csv_file.exists():
        raise HTTPException(status_code=404, detail=f"Schedule file for year {year} not found.")

    return FileResponse(
        path=str(csv_file),
        filename=f"schedule_{year}.csv",
        media_type="text/csv"
    )
