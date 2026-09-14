import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer
from app.core.database import Base
from app.models.base import TimestampMixin

class Microsegment(Base, TimestampMixin):
    __tablename__ = "microsegments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    sensitivity = Column(String(50), nullable=True)
    
    def __repr__(self):
        return f"<Microsegment(name='{self.name}')>"

class SegmentRule(Base, TimestampMixin):
    __tablename__ = "segment_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_segment = Column(String(100), nullable=False, index=True)
    destination_segment = Column(String(100), nullable=False, index=True)
    allowed = Column(Boolean, nullable=False, default=False)
    description = Column(String(255), nullable=True)
    priority = Column(Integer, nullable=False, default=100, index=True)
    enabled = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<SegmentRule({self.source_segment} -> {self.destination_segment}, allowed={self.allowed})>"
