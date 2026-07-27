from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

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
    reschedule_from: Optional[str] = None

class ScheduleRowSchema(BaseModel):
    week: int
    date: str
    festivity: Optional[str] = None
    pharmacies: List[Dict[str, Any]]  # List of {"id": 1, "name": "F1", "location": "centro"}
    status: str = "future"  # "past", "current", "future"
