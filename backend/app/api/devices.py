from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.device import Device
from app.schemas.device import DeviceRead

from app.api.dependencies import get_current_user, require_admin
from app.models.enums import UserRole
from app.models.user import User

router = APIRouter(prefix="/devices", tags=["Devices"])

@router.get("", response_model=List[DeviceRead])
def list_devices(
    owner_user_id: Optional[str] = None,
    posture: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all simulated devices with optional owner and posture filters."""
    query = db.query(Device)
    
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Device.owner_user_id == current_user.id)
    else:
        if owner_user_id:
            query = query.filter(Device.owner_user_id == owner_user_id)
            
    if posture:
        query = query.filter(Device.posture_status == posture)
        
    return query.order_by(Device.device_name).all()

@router.get("/{device_id}", response_model=DeviceRead)
def get_device(device_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve a single device by ID."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID '{device_id}' not found"
        )
        
    if current_user.role != UserRole.ADMIN and device.owner_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
    return device
