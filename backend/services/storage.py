import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, date

from core.config import DATA_DIR, SCHEDULES_DIR, SETTINGS_FILE
from core.csv_utils import read_csv_schedule, get_week_date
from backend.schemas.settings import SettingsSchema
from backend.schemas.schedule import ScheduleMetaSchema

def get_settings() -> SettingsSchema:
    """Reads settings.json or returns default settings if file does not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return SettingsSchema(**data)
        except Exception as e:
            logging.error(f"Failed to load settings.json: {e}")
    return SettingsSchema()

def save_settings(settings: SettingsSchema) -> SettingsSchema:
    """Atomically writes settings to settings.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = SETTINGS_FILE.with_suffix(".tmp")
    data = settings.model_dump()
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    temp_path.replace(SETTINGS_FILE)
    return settings

def list_schedules() -> List[Dict[str, Any]]:
    """Lists all available CSV schedules in data/schedules with metadata."""
    SCHEDULES_DIR.mkdir(parents=True, exist_ok=True)
    schedules = []
    for csv_file in SCHEDULES_DIR.glob("*.csv"):
        meta_file = csv_file.with_suffix(".meta.json")
        meta = {
            "year": 2026,
            "filename": csv_file.name,
            "generated_at": datetime.fromtimestamp(csv_file.stat().st_mtime).isoformat(),
            "solver": "clingo",
            "execution_time_seconds": None,
            "cost_value": None,
        }
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta.update(json.load(f))
            except Exception as e:
                logging.warning(f"Failed to load metadata {meta_file}: {e}")
        schedules.append(meta)
    return sorted(schedules, key=lambda x: x["filename"])

def get_schedule_rows(year: int, mode: str = "compact") -> List[Dict[str, Any]]:
    """Parses a schedule CSV and returns structured week rows for the frontend."""
    csv_file = SCHEDULES_DIR / f"schedule_{year}.csv"
    if not csv_file.exists():
        csv_file = SCHEDULES_DIR / f"test_{year}.csv"
    if not csv_file.exists():
        return []

    schedule, metadata, pharmacy_map, past_festivities, raw_rows = read_csv_schedule(str(csv_file))
    current_year = date.today().year
    current_week = date.today().isocalendar()[1]

    rows = []
    for week_num, farmacie_ids in sorted(schedule.items()):
        status = "future"
        if year < current_year or (year == current_year and week_num < current_week):
            status = "past"
        elif year == current_year and week_num == current_week:
            status = "current"

        week_date_str = get_week_date(week_num, year=year)
        pharmacies = []
        for fid in farmacie_ids:
            name = pharmacy_map.get(fid, f"F{fid}")
            location = "centro" if fid <= 6 else "marina"
            pharmacies.append({"id": fid, "name": name, "location": location})

        rows.append({
            "week": week_num,
            "date": week_date_str,
            "festivity": None,
            "pharmacies": pharmacies,
            "status": status,
        })

    return rows

def save_schedule_metadata(year: int, meta: ScheduleMetaSchema):
    """Saves metadata companion JSON for a generated schedule CSV."""
    SCHEDULES_DIR.mkdir(parents=True, exist_ok=True)
    meta_file = SCHEDULES_DIR / f"schedule_{year}.meta.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta.model_dump(), f, indent=2, ensure_ascii=False)
