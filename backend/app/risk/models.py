from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class RiskFactor(BaseModel):
    name: str = Field(..., description="Machine-readable identifier of the signal")
    category: str = Field(..., description="Category of signal (device, network, ip, geo, behavior, resource)")
    value: str = Field(..., description="Raw observed value of the signal")
    points: int = Field(..., description="Points contributed by this factor to the raw score")
    reason: str = Field(..., description="Human-readable explanation of why risk was applied")

class RiskAssessment(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Normalized composite risk score capped between 0 and 100")
    level: RiskLevel = Field(..., description="Risk classification: LOW (0-39), MEDIUM (40-69), HIGH (70-100)")
    raw_score: int = Field(..., ge=0, description="Uncapped sum of all contributing signal weights")
    factors: List[RiskFactor] = Field(default_factory=list, description="Detailed list of contributing risk factors")
    summary: str = Field(..., description="Executive explanation of the overall risk assessment")
