from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime

class WSEvent(BaseModel):
    type: str  # SETTINGS_UPDATED, JOB_STARTED, JOB_PROGRESS, JOB_COMPLETED, JOB_FAILED
    timestamp: str = datetime.now().isoformat()
    payload: Any = None
