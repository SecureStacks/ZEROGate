import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from app.core.database import Base

class EnforcementEvent(Base):
    __tablename__ = "enforcement_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    access_request_id = Column(String(36), nullable=False, index=True)
    decision = Column(String(50), nullable=False)
    access_granted = Column(Boolean, nullable=False)
    policy_id = Column(String(36), nullable=True)
    segment_rule_id = Column(String(36), nullable=True)
    source_segment = Column(String(100), nullable=True)
    destination_segment = Column(String(100), nullable=True)
    reason = Column(String(500), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False, index=True)

    def __repr__(self):
        return f"<EnforcementEvent(req_id='{self.access_request_id}', granted={self.access_granted})>"
