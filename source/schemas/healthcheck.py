from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum
from typing import Optional

class HealthStatus(str, Enum):
    ok = "ok"
    degraded = "degraded"
    fail = "fail"

class HealthCheckSchema(BaseModel):
    """Ответ на проверку состояния API/сервиса."""
    status: HealthStatus = Field(default=HealthStatus.ok, example="ok")
    time: datetime = Field(default_factory=datetime.now, example="2024-01-01T12:00:00Z")
    model_config = ConfigDict(from_attributes=True)