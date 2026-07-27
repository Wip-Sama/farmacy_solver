import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, date, timedelta

from core.config import DATA_DIR, SCHEDULES_DIR, SETTINGS_FILE, PROJECT_ROOT
from core.csv_utils import read_csv_schedule, get_week_date
from core.runner_core import get_italian_holidays, get_week_start_date, get_summer_weeks
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
    """Lists all available CSV schedules in data/schedules and schedules/ with metadata."""
    SCHEDULES_DIR.mkdir(parents=True, exist_ok=True)
    schedules = []
    seen_years = set()

    search_dirs = [SCHEDULES_DIR, PROJECT_ROOT / "schedules"]
    for s_dir in search_dirs:
        if not s_dir.exists():
            continue
        for csv_file in s_dir.glob("*.csv"):
            m = re.search(r'(\d{4})', csv_file.name)
            if not m:
                continue
            file_year = int(m.group(1))

            meta_file = csv_file.with_suffix(".meta.json")
            meta = {
                "year": file_year,
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

            if file_year not in seen_years:
                seen_years.add(file_year)
                schedules.append(meta)

    return sorted(schedules, key=lambda x: x["year"])

def get_schedule_rows(year: int, mode: str = "compact") -> List[Dict[str, Any]]:
    """Parses a schedule CSV and returns structured week rows for the frontend."""
    search_paths = [
        SCHEDULES_DIR / f"schedule_{year}.csv",
        SCHEDULES_DIR / f"test_{year}.csv",
        SCHEDULES_DIR / f"{year}.csv",
        PROJECT_ROOT / "schedules" / f"schedule_{year}.csv",
        PROJECT_ROOT / "schedules" / f"{year}.csv",
    ]
    csv_file = None
    for p in search_paths:
        if p.exists():
            csv_file = p
            break

    if not csv_file:
        return []

    schedule, metadata, pharmacy_map, past_festivities, raw_rows = read_csv_schedule(str(csv_file))
    current_year = date.today().year
    current_week = date.today().isocalendar()[1]

    settings = get_settings()
    settings_pharm_map = {p.id: p.name for p in settings.pharmacies}
    settings_loc_map = {p.id: p.location for p in settings.pharmacies}

    # Resolve festivities dictionary (Italian national + custom)
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

    rows = []
    first_dow = settings.first_day_of_week or "sunday"
    sum_start_w, sum_end_w = get_summer_weeks(year, first_dow)

    for week_num, farmacie_ids in sorted(schedule.items()):
        status = "future"
        if year < current_year or (year == current_year and week_num < current_week):
            status = "past"
        elif year == current_year and week_num == current_week:
            status = "current"

        is_summer = (sum_start_w <= week_num <= sum_end_w)
        week_start_date = get_week_start_date(week_num, year=year, first_day_of_week=first_dow)
        week_date_str = week_start_date.strftime("%Y-%m-%d")

        # Find any festivities within this week
        week_festivities = []
        for day_offset in range(7):
            curr_date = week_start_date + timedelta(days=day_offset)
            if curr_date in festivities_dict:
                fest_name = festivities_dict[curr_date]
                if fest_name not in week_festivities:
                    week_festivities.append(fest_name)

        festivity_str = ", ".join(week_festivities) if week_festivities else None

        pharmacies = []
        for fid in farmacie_ids:
            name = settings_pharm_map.get(fid) or (pharmacy_map.get(fid) if pharmacy_map.get(fid) and not (str(pharmacy_map.get(fid)).startswith("F") and str(pharmacy_map.get(fid))[1:].isdigit()) else None) or f"F{fid}"
            location = settings_loc_map.get(fid) or ("centro" if fid in [1, 2, 3, 4, 10] else "marina")
            pharmacies.append({"id": fid, "name": name, "location": location})

        rows.append({
            "week": week_num,
            "date": week_date_str,
            "festivity": festivity_str,
            "pharmacies": pharmacies,
            "status": status,
            "is_summer": is_summer,
        })

    return rows


def save_schedule_metadata(year: int, meta: ScheduleMetaSchema):
    """Saves metadata companion JSON for a generated schedule CSV."""
    SCHEDULES_DIR.mkdir(parents=True, exist_ok=True)
    meta_file = SCHEDULES_DIR / f"schedule_{year}.meta.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta.model_dump(), f, indent=2, ensure_ascii=False)
