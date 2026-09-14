from pydantic import BaseModel, ConfigDict
from typing import Optional
import datetime
from app.models.enums import DeviceType, DevicePosture

class DeviceBase(BaseModel):
    device_name: str
    device_type: DeviceType = DeviceType.LAPTOP
    operating_system: str = "macOS Sonoma"
    owner_user_id: str
    posture_status: DevicePosture = DevicePosture.HEALTHY
    managed: bool = True
    encrypted: bool = True
    compromised: bool = False

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    device_type: Optional[DeviceType] = None
    operating_system: Optional[str] = None
    posture_status: Optional[DevicePosture] = None
    managed: Optional[bool] = None
    encrypted: Optional[bool] = None
    compromised: Optional[bool] = None

class DeviceRead(DeviceBase):
    id: str
    last_seen_at: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
