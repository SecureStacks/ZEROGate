from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.core.database import get_db
from app.models.access_request import AccessRequest
from app.models.user import User
from app.models.device import Device
from app.models.resource import Resource
from app.schemas.access_request import AccessRequestCreate, AccessRequestRead

from app.api.dependencies import get_current_user
from app.models.enums import UserRole

router = APIRouter(prefix="/access-requests", tags=["Access Requests"])

@router.get("", response_model=List[AccessRequestRead])
def list_access_requests(
    user_id: Optional[str] = None,
    resource_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve simulated access requests context history."""
    query = db.query(AccessRequest).options(
        joinedload(AccessRequest.user),
        joinedload(AccessRequest.device),
        joinedload(AccessRequest.resource),
    )
    
    if current_user.role != UserRole.ADMIN:
        query = query.filter(AccessRequest.user_id == current_user.id)
    else:
        if user_id:
            query = query.filter(AccessRequest.user_id == user_id)
            
    if resource_id:
        query = query.filter(AccessRequest.resource_id == resource_id)
        
    return query.order_by(AccessRequest.created_at.desc()).limit(limit).all()

@router.get("/{request_id}", response_model=AccessRequestRead)
def get_access_request(request_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve a single access request context by ID."""
    req = db.query(AccessRequest).options(
        joinedload(AccessRequest.user),
        joinedload(AccessRequest.device),
        joinedload(AccessRequest.resource),
    ).filter(AccessRequest.id == request_id).first()
    
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Access Request with ID '{request_id}' not found"
        )
        
    if current_user.role != UserRole.ADMIN and req.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
    return req

@router.post("", response_model=AccessRequestRead, status_code=status.HTTP_201_CREATED)
def create_access_request(
    payload: AccessRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit and store a simulated access request context."""
    if current_user.role != UserRole.ADMIN and payload.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create requests for other users")
        
    # Validate user existence
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with ID '{payload.user_id}' does not exist"
        )

    # Validate device existence
    device = db.query(Device).filter(Device.id == payload.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device with ID '{payload.device_id}' does not exist"
        )

    # Validate resource existence
    resource = db.query(Resource).filter(Resource.id == payload.resource_id).first()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Resource with ID '{payload.resource_id}' does not exist"
        )

    access_req = AccessRequest(**payload.model_dump())
    db.add(access_req)
    db.commit()
    db.refresh(access_req)
    return access_req
