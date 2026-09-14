from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.models.pep import EnforcementEvent
from app.models.access_request import AccessRequest
from app.models.user import User
from app.models.resource import Resource

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

from app.api.dependencies import get_current_user, require_admin

@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db), current_user = Depends(require_admin)):
    total_users = db.query(User).count()
    active_devices = db.query(AccessRequest).distinct(AccessRequest.device_id).count() # simplistic proxy
    protected_resources = db.query(Resource).count()
    
    total_requests = db.query(EnforcementEvent).count()
    allowed_requests = db.query(EnforcementEvent).filter(EnforcementEvent.access_granted == True).count()
    mfa_challenges = db.query(EnforcementEvent).filter(EnforcementEvent.decision == "MFA_REQUIRED").count()
    blocked_requests = total_requests - allowed_requests
    
    return {
        "metrics": {
            "total_users": total_users,
            "active_devices": active_devices,
            "protected_resources": protected_resources,
            "total_requests": total_requests,
            "allowed_requests": allowed_requests,
            "mfa_challenges": mfa_challenges,
            "blocked_requests": blocked_requests,
            "high_risk_requests": 0 # Would require risk join, keeping simple for demo
        }
    }

@router.get("/recent-activity")
def get_recent_activity(db: Session = Depends(get_db), current_user = Depends(require_admin)):
    events = db.query(EnforcementEvent).order_by(desc(EnforcementEvent.timestamp)).limit(10).all()
    
    activity = []
    for event in events:
        req = db.query(AccessRequest).filter(AccessRequest.id == event.access_request_id).first()
        if not req:
            continue
            
        user = db.query(User).filter(User.id == req.user_id).first()
        resource = db.query(Resource).filter(Resource.id == req.resource_id).first()
        
        activity.append({
            "id": event.id,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "user": user.username if user else "Unknown",
            "resource": resource.name if resource else "Unknown",
            "decision": event.decision,
            "access_granted": event.access_granted,
            "reason": event.reason,
            "source_segment": event.source_segment,
            "destination_segment": event.destination_segment
        })
        
    return activity
