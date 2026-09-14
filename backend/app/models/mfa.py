from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
import uuid

from app.core.database import Base

class MFAChallengeStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"

class MFAChallenge(Base):
    __tablename__ = "mfa_challenges"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    request_id = Column(String, ForeignKey("access_requests.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    challenge_type = Column(String, default="SIMULATED_OTP", nullable=False)
    status = Column(SQLEnum(MFAChallengeStatus), default=MFAChallengeStatus.PENDING, nullable=False)
    
    code_hash = Column(String, nullable=False)
    
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    access_request = relationship("AccessRequest")
    user = relationship("User")
