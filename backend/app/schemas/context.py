from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.models.enums import IPReputation, NetworkType

class NetworkContextSchema(BaseModel):
    source_ip: str = "10.0.4.15"
    ip_reputation: IPReputation = IPReputation.TRUSTED
    network_type: NetworkType = NetworkType.CORPORATE
    is_vpn: bool = False
    is_tor: bool = False
    is_known_network: bool = True
    source_segment: str = "Development"
    country: str = "India"
    city: str = "Bengaluru"

class BehavioralContextSchema(BaseModel):
    unusual_time: bool = False
    unusual_location: bool = False
    unusual_resource: bool = False
    failed_attempts: int = 0
    recent_resource_count: int = 1

class DemoScenarioSchema(BaseModel):
    id: str
    name: str
    description: str
    user_id: Optional[str] = None
    username: str
    user_role: str
    device_id: Optional[str] = None
    device_name: str
    device_posture: str
    resource_id: Optional[str] = None
    resource_name: str
    network: NetworkContextSchema
    behavior: BehavioralContextSchema
