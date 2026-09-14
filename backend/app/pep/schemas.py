from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.segmentation.schemas import SegmentDecision

class EnforcementResult(BaseModel):
    request_id: str
    decision: str
    enforced: bool
    access_granted: bool
    resource: str
    policy_id: Optional[str] = None
    policy_name: Optional[str] = None
    reason: str
    segment_check: Optional[SegmentDecision] = None
