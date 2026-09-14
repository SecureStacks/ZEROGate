from pydantic import BaseModel, ConfigDict
from typing import Optional, List
import datetime
from app.models.enums import UserRole, UserStatus

class UserBase(BaseModel):
    username: str
    display_name: str
    email: str
    role: UserRole = UserRole.DEVELOPER
    department: str = "Engineering"
    status: UserStatus = UserStatus.ACTIVE

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    department: Optional[str] = None
    status: Optional[UserStatus] = None

class UserRead(UserBase):
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
