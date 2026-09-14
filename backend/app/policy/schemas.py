from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import PolicyEffect, UserRole, DevicePosture, NetworkType, IPReputation

class PolicyBase(BaseModel):
    name: str
    description: Optional[str] = None
    priority: int
    enabled: bool = True
    effect: PolicyEffect

    required_role: Optional[UserRole] = None
    required_device_posture: Optional[DevicePosture] = None
    min_risk_score: Optional[int] = None
    max_risk_score: Optional[int] = None
    resource_id: Optional[str] = None
    network_type: Optional[NetworkType] = None
    ip_reputation: Optional[IPReputation] = None
    require_managed_device: bool = False
    require_known_network: bool = False

class PolicyCreate(PolicyBase):
    pass

class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None
    effect: Optional[PolicyEffect] = None
    required_role: Optional[UserRole] = None
    required_device_posture: Optional[DevicePosture] = None
    min_risk_score: Optional[int] = None
    max_risk_score: Optional[int] = None
    resource_id: Optional[str] = None
    network_type: Optional[NetworkType] = None
    ip_reputation: Optional[IPReputation] = None
    require_managed_device: Optional[bool] = None
    require_known_network: Optional[bool] = None

class PolicyRead(PolicyBase):
    id: str
    created_at: str
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
