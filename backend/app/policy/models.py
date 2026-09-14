from typing import List, Optional
from pydantic import BaseModel
from app.models.enums import PolicyEffect
from app.risk.models import RiskLevel

class PolicyEvaluationTrace(BaseModel):
    policy_name: str
    matched: bool
    reason: str

class PolicyDecision(BaseModel):
    decision: PolicyEffect
    policy_id: Optional[str] = None
    policy_name: Optional[str] = None
    reason: str
    risk_score: Optional[int] = None
    risk_level: Optional[RiskLevel] = None
    evaluated_policies: List[PolicyEvaluationTrace] = []
