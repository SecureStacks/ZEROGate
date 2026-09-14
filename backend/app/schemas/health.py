from pydantic import BaseModel
from typing import Optional

class HealthResponse(BaseModel):
    status: str
    database: str
    version: str
    environment: str
    timestamp: str
