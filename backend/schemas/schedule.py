from typing import Any

from pydantic import BaseModel

from backend.schemas.settings import CustomFestivity, PharmacyPreference, PharmacySchema


class ScheduleMetaSchema(BaseModel):
    year: int
    filename: str
    generated_at: str
    solver: str = "clingo"
    execution_time_seconds: float | None = None
    cost_value: str | None = None
    is_locked: bool = False


class ScheduleGenerateRequest(BaseModel):
    year: int = 2026
    time_limit: int | None = None
    auto_festivities: bool | None = None
    base: str | None = "choice"
    opt: str | None = "penalita_esponenziale"
    reschedule_from: Any | None = None
    regenerate_from: Any | None = None
    use_previous_year: bool | None = None
    first_day_of_week: str | None = None
    custom_pharmacies: list[PharmacySchema] | None = None
    custom_festivities: list[CustomFestivity] | None = None
    pharmacy_preferences: list[PharmacyPreference] | None = None


class ScheduleRowSchema(BaseModel):
    week: int
    date: str
    festivity: str | None = None
    pharmacies: list[dict[str, Any]]  # List of {"id": 1, "name": "F1", "location": "centro"}
    status: str = "future"  # "past", "current", "future"
    is_summer: bool = False
