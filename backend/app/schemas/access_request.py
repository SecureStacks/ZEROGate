from pydantic import BaseModel, ConfigDict
from typing import Optional
import datetime
from app.models.enums import IPReputation, NetworkType
from app.schemas.user import UserRead
from app.schemas.device import DeviceRead
from app.schemas.resource import ResourceRead

class AccessRequestCreate(BaseModel):
    user_id: str
    device_id: str
    resource_id: str
    source_ip: str = "10.0.4.15"
    ip_reputation: IPReputation = IPReputation.TRUSTED
    network_type: NetworkType = NetworkType.CORPORATE
    is_vpn: bool = False
    is_tor: bool = False
    is_known_network: bool = True
    country: str = "India"
    city: str = "Bengaluru"
    unusual_time: bool = False
    unusual_location: bool = False
    unusual_resource: bool = False
    failed_attempts: int = 0
    recent_resource_count: int = 1
    source_segment: str = "Development"
    user_agent: Optional[str] = "ZeroGate-Client/1.0 (macOS; arm64)"

class AccessRequestRead(BaseModel):
    id: str
    user_id: str
    device_id: str
    resource_id: str
    source_ip: str
    ip_reputation: IPReputation
    network_type: NetworkType
    is_vpn: bool
    is_tor: bool
    is_known_network: bool
    country: str
    city: str
    unusual_time: bool
    unusual_location: bool
    unusual_resource: bool
    failed_attempts: int
    recent_resource_count: int
    source_segment: str
    request_time: datetime.datetime
    user_agent: str
    session_id: str
    created_at: datetime.datetime
    
    # Optional nested details if eager loaded
    user: Optional[UserRead] = None
    device: Optional[DeviceRead] = None
    resource: Optional[ResourceRead] = None

    model_config = ConfigDict(from_attributes=True)
