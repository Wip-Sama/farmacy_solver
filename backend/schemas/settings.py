from pydantic import BaseModel, Field
from typing import List, Optional

class CustomFestivity(BaseModel):
    name: str
    date: str  # Format YYYY-MM-DD

class PharmacyPreference(BaseModel):
    pharmacy_id: int
    date: str  # Format YYYY-MM-DD
    state: str = "Closed"

class SettingsSchema(BaseModel):
    year: int = Field(default=2026, description="Scheduling year")
    use_previous_year: bool = Field(default=True, description="Extract past festivity assignments from previous year CSV")
    first_day_of_week: str = Field(default="sunday", description="First day of week (sunday, monday, etc.)")
    auto_festivities: bool = Field(default=True, description="Auto-generate Italian national holidays")
    time_limit: int = Field(default=60, description="ASP solver time limit in seconds")
    regenerate_from: Optional[str] = Field(default=None, description="Start date/week for rescheduling")
    custom_festivities: List[CustomFestivity] = Field(default_factory=list)
    pharmacy_preferences: List[PharmacyPreference] = Field(default_factory=list)
