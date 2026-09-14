import uuid
import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import IPReputation, NetworkType

class AccessRequest(Base, TimestampMixin):
    __tablename__ = "access_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(String(36), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(String(36), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)

    # Network / IP Context (Simulated)
    source_ip = Column(String(45), nullable=False, default="10.0.4.15")
    ip_reputation = Column(SQLEnum(IPReputation), nullable=False, default=IPReputation.TRUSTED)
    network_type = Column(SQLEnum(NetworkType), nullable=False, default=NetworkType.CORPORATE)
    is_vpn = Column(Boolean, default=False, nullable=False)
    is_tor = Column(Boolean, default=False, nullable=False)
    is_known_network = Column(Boolean, default=True, nullable=False)
    source_segment = Column(String(50), nullable=False)

    # Geographic Context (Simulated)
    country = Column(String(100), nullable=False, default="India")
    city = Column(String(100), nullable=False, default="Bengaluru")

    # Behavioral Context (Simulated)
    unusual_time = Column(Boolean, default=False, nullable=False)
    unusual_location = Column(Boolean, default=False, nullable=False)
    unusual_resource = Column(Boolean, default=False, nullable=False)
    failed_attempts = Column(Integer, default=0, nullable=False)
    recent_resource_count = Column(Integer, default=1, nullable=False)

    # Session / Telemetry
    request_time = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    user_agent = Column(String(255), nullable=False, default="ZeroGate-Client/1.0 (macOS; arm64)")
    session_id = Column(String(64), nullable=False, default=lambda: str(uuid.uuid4())[:16])

    # Relationships
    user = relationship("User", back_populates="access_requests")
    device = relationship("Device", back_populates="access_requests")
    resource = relationship("Resource", back_populates="access_requests")

    def __repr__(self):
        return f"<AccessRequest(id='{self.id}', user_id='{self.user_id}', resource_id='{self.resource_id}', ip_rep='{self.ip_reputation.value}')>"
