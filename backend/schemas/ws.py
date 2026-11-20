from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WSEvent(BaseModel):
    type: str  # SETTINGS_UPDATED, JOB_STARTED, JOB_PROGRESS, JOB_COMPLETED, JOB_FAILED
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    payload: Any = None
