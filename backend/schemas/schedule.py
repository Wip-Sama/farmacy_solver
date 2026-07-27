from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from backend.schemas.settings import PharmacySchema

class CustomFestivity(BaseModel):
    name: str
    date: Optional[str] = ""

class PharmacyPreference(BaseModel):
    pharmacy_id: int
    date: Optional[str] = ""
    state: str = Field(default="Closed", description="Availability state: Closed, Force Open, Force Closed, Preferably Open, Preferably Closed")

class ScheduleMetaSchema(BaseModel):
    year: int
    filename: str
    generated_at: str
    solver: str = "clingo"
    execution_time_seconds: Optional[float] = None
    cost_value: Optional[str] = None
    is_locked: bool = False

class ScheduleGenerateRequest(BaseModel):
    year: int = 2026
    time_limit: Optional[int] = 60
    auto_festivities: Optional[bool] = True
    base: Optional[str] = "choice"
    opt: Optional[str] = "penalita_esponenziale"
    reschedule_from: Optional[Any] = None
    regenerate_from: Optional[Any] = None
    use_previous_year: Optional[bool] = True
    first_day_of_week: Optional[str] = "sunday"
    custom_pharmacies: Optional[List[PharmacySchema]] = None
    custom_festivities: Optional[List[CustomFestivity]] = None
    pharmacy_preferences: Optional[List[PharmacyPreference]] = None

class ScheduleRowSchema(BaseModel):
    week: int
    date: str
    festivity: Optional[str] = None
    pharmacies: List[Dict[str, Any]]  # List of {"id": 1, "name": "F1", "location": "centro"}
    status: str = "future"  # "past", "current", "future"
