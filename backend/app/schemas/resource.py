from pydantic import BaseModel, ConfigDict
from typing import Optional
import datetime
from app.models.enums import ResourceSensitivity

class ResourceBase(BaseModel):
    name: str
    resource_type: str = "Application"
    sensitivity: ResourceSensitivity = ResourceSensitivity.MEDIUM
    network_segment: str = "General"
    host: str = "internal.zerogate.local"
    port: int = 443
    protocol: str = "HTTPS"
    description: Optional[str] = None
    enabled: bool = True

class ResourceCreate(ResourceBase):
    pass

class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    resource_type: Optional[str] = None
    sensitivity: Optional[ResourceSensitivity] = None
    network_segment: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None

class ResourceRead(ResourceBase):
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
