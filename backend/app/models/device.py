import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import DeviceType, DevicePosture

class Device(Base, TimestampMixin):
    __tablename__ = "devices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_name = Column(String(100), nullable=False)
    device_type = Column(SQLEnum(DeviceType), nullable=False, default=DeviceType.LAPTOP)
    operating_system = Column(String(100), nullable=False, default="macOS Sonoma")
    owner_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    posture_status = Column(SQLEnum(DevicePosture), nullable=False, default=DevicePosture.HEALTHY)
    managed = Column(Boolean, default=True, nullable=False)
    encrypted = Column(Boolean, default=True, nullable=False)
    compromised = Column(Boolean, default=False, nullable=False)
    last_seen_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="devices")
    access_requests = relationship("AccessRequest", back_populates="device", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Device(name='{self.device_name}', posture='{self.posture_status.value}', owner_id='{self.owner_user_id}')>"
