from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MicrosegmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    sensitivity: Optional[str] = None

class MicrosegmentCreate(MicrosegmentBase):
    pass

class MicrosegmentSchema(MicrosegmentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SegmentRuleBase(BaseModel):
    source_segment: str
    destination_segment: str
    allowed: bool
    description: Optional[str] = None
    priority: int = 100
    enabled: bool = True

class SegmentRuleCreate(SegmentRuleBase):
    pass

class SegmentRuleUpdate(BaseModel):
    source_segment: Optional[str] = None
    destination_segment: Optional[str] = None
    allowed: Optional[bool] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None

class SegmentRuleSchema(SegmentRuleBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SegmentDecision(BaseModel):
    allowed: bool
    source_segment: str
    destination_segment: str
    matched_rule: Optional[str] = None
    reason: str
