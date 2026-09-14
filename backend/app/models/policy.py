from sqlalchemy import Column, String, Integer, Boolean, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.enums import PolicyEffect, UserRole, DevicePosture, NetworkType, IPReputation

class Policy(Base):
    __tablename__ = "policies"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    priority = Column(Integer, index=True, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    effect = Column(Enum(PolicyEffect), nullable=False)

    # Conditions
    required_role = Column(Enum(UserRole), nullable=True)
    required_device_posture = Column(Enum(DevicePosture), nullable=True)
    min_risk_score = Column(Integer, nullable=True)
    max_risk_score = Column(Integer, nullable=True)
    resource_id = Column(String, ForeignKey("resources.id"), nullable=True)
    network_type = Column(Enum(NetworkType), nullable=True)
    ip_reputation = Column(Enum(IPReputation), nullable=True)
    require_managed_device = Column(Boolean, default=False)
    require_known_network = Column(Boolean, default=False)

    # Metadata
    created_at = Column(String, server_default=func.now())
    updated_at = Column(String, onupdate=func.now())

    resource = relationship("Resource")
