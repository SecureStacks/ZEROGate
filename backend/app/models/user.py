import uuid
from sqlalchemy import Column, String, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import UserRole, UserStatus

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, index=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True) # Made nullable true for existing data, should be false eventually
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.DEVELOPER)
    department = Column(String(100), nullable=False, default="Engineering")
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE)

    # Relationships
    devices = relationship("Device", back_populates="owner", cascade="all, delete-orphan")
    access_requests = relationship("AccessRequest", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role.value}', status='{self.status.value}')>"
