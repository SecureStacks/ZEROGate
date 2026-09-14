import uuid
from sqlalchemy import Column, String, Integer, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import ResourceSensitivity

class Resource(Base, TimestampMixin):
    __tablename__ = "resources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, index=True, nullable=False)
    resource_type = Column(String(50), nullable=False, default="Application")
    sensitivity = Column(SQLEnum(ResourceSensitivity), nullable=False, default=ResourceSensitivity.MEDIUM)
    network_segment = Column(String(50), nullable=False, default="General")
    host = Column(String(100), nullable=False, default="internal.zerogate.local")
    port = Column(Integer, nullable=False, default=443)
    protocol = Column(String(20), nullable=False, default="HTTPS")
    description = Column(String(255), nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)

    # Relationships
    access_requests = relationship("AccessRequest", back_populates="resource", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Resource(name='{self.name}', segment='{self.network_segment}', sensitivity='{self.sensitivity.value}')>"
