from pydantic import BaseModel, Field
from typing import List, Optional

class CustomFestivity(BaseModel):
    name: str
    date: Optional[str] = ""

class PharmacyPreference(BaseModel):
    pharmacy_id: int
    date: Optional[str] = ""
    state: str = "Closed"

class PharmacySchema(BaseModel):
    id: int
    name: str
    location: str

def default_pharmacies():
    return [
        {"id": 1, "name": "MONTORO", "location": "centro"},
        {"id": 2, "name": "BUCCARELLI", "location": "centro"},
        {"id": 3, "name": "CENTRALE", "location": "centro"},
        {"id": 4, "name": "DE PINO", "location": "centro"},
        {"id": 5, "name": "DAVID", "location": "centro"},
        {"id": 6, "name": "SAN MICHELE", "location": "centro"},
        {"id": 7, "name": "MARCELLINI", "location": "marina"},
        {"id": 8, "name": "PHARMADUO", "location": "marina"},
        {"id": 9, "name": "IORFIDA", "location": "marina"},
        {"id": 10, "name": "SAN LEONARDO", "location": "marina"},
    ]

class SettingsSchema(BaseModel):
    year: int = Field(default=2026, description="Scheduling year")
    use_previous_year: bool = Field(default=True, description="Extract past festivity assignments from previous year CSV")
    first_day_of_week: str = Field(default="monday", description="First day of week (sunday, monday, etc.)")
    auto_festivities: bool = Field(default=True, description="Auto-generate Italian national holidays")
    time_limit: int = Field(default=55, description="ASP solver time limit in seconds")
    regenerate_from: Optional[str] = Field(default=None, description="Start date/week for rescheduling")
    pharmacies: List[PharmacySchema] = Field(default_factory=default_pharmacies)
    custom_festivities: List[CustomFestivity] = Field(default_factory=list)
    pharmacy_preferences: List[PharmacyPreference] = Field(default_factory=list)
