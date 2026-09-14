from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.pep import EnforcementEvent
from app.models.access_request import AccessRequest
from app.models.user import User
from app.models.device import Device
from app.models.resource import Resource

from app.api.dependencies import get_current_user, require_admin
from app.models.enums import UserRole

router = APIRouter(prefix="/logs", tags=["Logs"])

class LogEntry(BaseModel):
    id: str
    timestamp: Optional[datetime]
    access_request_id: str
    decision: str
    access_granted: bool
    reason: str
    source_segment: Optional[str]
    destination_segment: Optional[str]
    user_id: Optional[str]
    username: Optional[str]
    resource_id: Optional[str]
    resource_name: Optional[str]

class LogDetail(LogEntry):
    device_id: Optional[str]
    device_name: Optional[str]
    ip_address: Optional[str]
    network_type: Optional[str]

@router.get("", response_model=List[LogEntry])
def get_logs(
    limit: int = Query(50, le=100),
    decision: Optional[str] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(EnforcementEvent).order_by(desc(EnforcementEvent.timestamp))
    
    if decision:
        query = query.filter(EnforcementEvent.decision == decision)
        
    events = query.limit(limit).all()
    
    results = []
    for event in events:
        req = db.query(AccessRequest).filter(AccessRequest.id == event.access_request_id).first()
        if not req:
            continue
            
        if current_user.role != UserRole.ADMIN and req.user_id != current_user.id:
            continue
            
        if user_id and current_user.role == UserRole.ADMIN and req.user_id != user_id:
            continue
            
        user = db.query(User).filter(User.id == req.user_id).first()
        resource = db.query(Resource).filter(Resource.id == req.resource_id).first()
        
        results.append(LogEntry(
            id=event.id,
            timestamp=event.timestamp,
            access_request_id=event.access_request_id,
            decision=event.decision,
            access_granted=event.access_granted,
            reason=event.reason,
            source_segment=event.source_segment,
            destination_segment=event.destination_segment,
            user_id=req.user_id,
            username=user.username if user else "Unknown",
            resource_id=req.resource_id,
            resource_name=resource.name if resource else "Unknown"
        ))
        
    return results

@router.get("/{log_id}", response_model=LogDetail)
def get_log_detail(log_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event = db.query(EnforcementEvent).filter(EnforcementEvent.id == log_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Log entry not found")
        
    req = db.query(AccessRequest).filter(AccessRequest.id == event.access_request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Associated access request not found")
        
    if current_user.role != UserRole.ADMIN and req.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    user = db.query(User).filter(User.id == req.user_id).first()
    device = db.query(Device).filter(Device.id == req.device_id).first()
    resource = db.query(Resource).filter(Resource.id == req.resource_id).first()
    
    return LogDetail(
        id=event.id,
        timestamp=event.timestamp,
        access_request_id=event.access_request_id,
        decision=event.decision,
        access_granted=event.access_granted,
        reason=event.reason,
        source_segment=event.source_segment,
        destination_segment=event.destination_segment,
        user_id=req.user_id,
        username=user.username if user else "Unknown",
        resource_id=req.resource_id,
        resource_name=resource.name if resource else "Unknown",
        device_id=req.device_id,
        device_name=device.device_name if device else "Unknown",
        ip_address=req.source_ip,
        network_type=req.network_type
    )
