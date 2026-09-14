from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.mfa import MFAChallengeStatus

class MFAChallengeCreateRequest(BaseModel):
    access_request_id: str

class MFAChallengeVerifyRequest(BaseModel):
    challenge_id: str
    code: str

class MFAChallengeResponse(BaseModel):
    id: str
    request_id: str
    user_id: str
    challenge_type: str
    status: MFAChallengeStatus
    attempts: int
    max_attempts: int
    expires_at: datetime
    verified_at: Optional[datetime] = None
    created_at: datetime
    
    demo_otp: Optional[str] = None # FOR DEMONSTRATION PURPOSES ONLY

    model_config = ConfigDict(from_attributes=True)
