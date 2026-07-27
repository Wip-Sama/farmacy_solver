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
from backend.services.export_service import generate_schedule_png
from datetime import datetime, date
from core.config import SCHEDULES_DIR
from core.csv_utils import read_csv_schedule, generate_csv_report, parse_first_day_of_week
from core.runner_core import get_italian_holidays

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

    settings = get_settings()
    auto_fest = req.auto_festivities if req.auto_festivities is not None else settings.auto_festivities
    fest_list = req.custom_festivities if req.custom_festivities is not None else settings.custom_festivities

    # Enforce Requirement 3: If auto_festivities is OFF, all festivities must have non-empty dates
    if not auto_fest:
        for fest in fest_list:
            d_val = fest.date.strip() if fest.date else ""
            if not d_val:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot generate schedule: Festivity '{fest.name}' is missing a date while auto festivities is disabled."
                )

    try:
        reschedule_bound = req.reschedule_from or req.regenerate_from
        pref_list = req.pharmacy_preferences if req.pharmacy_preferences is not None else settings.pharmacy_preferences
        pharm_list = req.custom_pharmacies if req.custom_pharmacies is not None else settings.pharmacies
        job_id = await job_manager.start_job(
            year=req.year,
            time_limit=req.time_limit if req.time_limit is not None else settings.time_limit,
            auto_festivities=auto_fest,
            base=req.base or "choice",
            opt=req.opt or "penalita_esponenziale",
            reschedule_from=reschedule_bound,
            use_previous_year=req.use_previous_year if req.use_previous_year is not None else settings.use_previous_year,
            first_day_of_week=req.first_day_of_week or settings.first_day_of_week,
            custom_pharmacies=pharm_list,
            custom_festivities=fest_list,
            pharmacy_preferences=pref_list,
        )
        return {"status": "job_started", "job_id": job_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedules/cancel")
async def cancel_schedule_generation():
    """Cancels an ongoing scheduling job if one is running."""
    cancelled = await job_manager.cancel_current_job()
    if not cancelled:
        raise HTTPException(status_code=400, detail="No active scheduling job to cancel.")
    return {"status": "job_cancelled"}


import time
from pathlib import Path

def delete_file_safely(file_path: str):
    """Safely deletes a temporary exported file after background response delivery."""
    try:
        p = Path(file_path)
        if p.exists():
            p.unlink()
    except Exception as e:
        pass

def cleanup_old_export_files(schedules_dir: Path, max_age_seconds: int = 300):
    """Deletes any temporary export files (export_*) older than max_age_seconds."""
    try:
        if not schedules_dir.exists():
            return
        now = time.time()
        for f in schedules_dir.glob("export_*"):
            if f.is_file() and (now - f.stat().st_mtime) > max_age_seconds:
                try:
                    f.unlink()
                except Exception:
                    pass
    except Exception:
        pass


@router.get("/schedules/{year}/export")
async def export_schedule(
    year: int,
    background_tasks: BackgroundTasks,
    format: str = "csv",
    orientation: str = "horizontal",
    type: str = "normal",
    pharmacy_label: str = "names"
):
    """Downloads the generated CSV or PNG schedule for the given year, formatted according to orientation, type, and pharmacy_label. Automatically cleans up export files."""
    cleanup_old_export_files(SCHEDULES_DIR, max_age_seconds=300)

    csv_file = SCHEDULES_DIR / f"schedule_{year}.csv"
    if not csv_file.exists():
        csv_file = SCHEDULES_DIR / f"test_{year}.csv"
    if not csv_file.exists():
        raise HTTPException(status_code=404, detail=f"Schedule file for year {year} not found.")

    settings = get_settings()
    first_dow = settings.first_day_of_week or "monday"
    mode_val = type.lower() if type else "normal"
    orient_val = orientation.lower() if orientation else "horizontal"
    label_val = pharmacy_label.lower() if pharmacy_label else "names"
    pharm_map = {p.id: p.name for p in settings.pharmacies}

    if format.lower() == "png":
        png_file = SCHEDULES_DIR / f"export_{year}_{mode_val}_{orient_val}_{label_val}_{int(time.time()*1000)}.png"
        rows = get_schedule_rows(year, mode=mode_val)
        generate_schedule_png(
            year=year,
            rows=rows,
            output_path=str(png_file),
            mode=mode_val,
            orientation=orient_val,
            pharmacy_label=label_val,
            pharmacy_name_map=pharm_map
        )
        background_tasks.add_task(delete_file_safely, str(png_file))
        return FileResponse(
            path=str(png_file),
            filename=f"schedule_{year}_{mode_val}_{orient_val}_{label_val}.png",
            media_type="image/png"
        )

    # For CSV Export:
    csv_direction = "row" if orient_val in ["horizontal", "row"] else "column"
    schedule, metadata, pharmacy_map, past_festivities, raw_rows = read_csv_schedule(str(csv_file))
    
    festivities_dict = {}
    if settings.auto_festivities:
        festivities_dict.update(get_italian_holidays(year))
    for cust_fest in settings.custom_festivities:
        name = cust_fest.name
        d_str = cust_fest.date.strip()
        try:
            if "/" in d_str:
                parts = d_str.split("/")
                d_obj = date(year, int(parts[1]), int(parts[0]))
            elif "-" in d_str:
                d_obj = datetime.strptime(d_str, "%Y-%m-%d").date()
            else:
                continue
            festivities_dict[d_obj] = name
        except Exception:
            pass

    export_csv_file = SCHEDULES_DIR / f"export_{year}_{mode_val}_{orient_val}_{int(time.time()*1000)}.csv"
    generate_csv_report(
        schedule=schedule,
        filename=str(export_csv_file),
        run_info={"solver": "clingo", "time": metadata.get("execution_time_seconds", 0)},
        year=year,
        festivities_dict=festivities_dict,
        csv_mode=mode_val,
        csv_direction=csv_direction,
        csv_map_pharmacies={p.id: p.name for p in settings.pharmacies},
        first_day_of_week=parse_first_day_of_week(first_dow)
    )

    background_tasks.add_task(delete_file_safely, str(export_csv_file))
    return FileResponse(
        path=str(export_csv_file),
        filename=f"schedule_{year}_{mode_val}_{orient_val}.csv",
        media_type="text/csv"
    )
