from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.core.database import get_db
from app.risk.models import RiskAssessment, RiskLevel
from app.risk.service import RiskService
from app.risk.engine import RiskEngine
from app.models.enums import (
    DevicePosture,
    IPReputation,
    NetworkType,
    ResourceSensitivity,
)
from app.seed.seed_data import get_demo_scenarios
from app.models.resource import Resource

from app.api.dependencies import get_current_user
from app.models.enums import UserRole
from app.models.user import User

router = APIRouter(prefix="/risk", tags=["Risk Engine"])

class RiskEvaluateRequest(BaseModel):
    access_request_id: Optional[str] = None
    
    # Optional raw context parameters if evaluating dynamic simulation directly
    device_posture: Optional[DevicePosture] = None
    device_managed: Optional[bool] = True
    device_encrypted: Optional[bool] = True
    device_compromised: Optional[bool] = False
    ip_reputation: Optional[IPReputation] = None
    source_ip: Optional[str] = "10.0.4.15"
    network_type: Optional[NetworkType] = None
    is_vpn: Optional[bool] = False
    is_tor: Optional[bool] = False
    unusual_location: Optional[bool] = False
    country: Optional[str] = "India"
    city: Optional[str] = "Bengaluru"
    unusual_time: Optional[bool] = False
    unusual_resource: Optional[bool] = False
    failed_attempts: Optional[int] = 0
    recent_resource_count: Optional[int] = 1
    resource_sensitivity: Optional[ResourceSensitivity] = None
    resource_name: Optional[str] = "Protected Resource"

class ScenarioRiskResult(BaseModel):
    scenario_id: str
    scenario_name: str
    description: str
    risk: RiskAssessment

@router.post("/evaluate", response_model=RiskAssessment)
def evaluate_risk(
    payload: RiskEvaluateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Evaluate contextual Zero Trust risk for an access request.
    Calculates normalized score (0-100), classification (LOW/MEDIUM/HIGH), and contributing factors.
    """
    if payload.access_request_id:
        from app.models.access_request import AccessRequest
        req = db.query(AccessRequest).filter(AccessRequest.id == payload.access_request_id).first()
        if req and current_user.role != UserRole.ADMIN and req.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        return RiskService.evaluate_access_request_by_id(payload.access_request_id, db)
    
    # Fallback to direct context evaluation if access_request_id is not provided
    return RiskEngine.calculate_risk(
        device_posture=payload.device_posture or DevicePosture.HEALTHY,
        device_managed=payload.device_managed if payload.device_managed is not None else True,
        device_encrypted=payload.device_encrypted if payload.device_encrypted is not None else True,
        device_compromised=payload.device_compromised or False,
        ip_reputation=payload.ip_reputation or IPReputation.TRUSTED,
        source_ip=payload.source_ip or "10.0.4.15",
        network_type=payload.network_type or NetworkType.CORPORATE,
        is_vpn=payload.is_vpn or False,
        is_tor=payload.is_tor or False,
        unusual_location=payload.unusual_location or False,
        country=payload.country or "India",
        city=payload.city or "Bengaluru",
        unusual_time=payload.unusual_time or False,
        unusual_resource=payload.unusual_resource or False,
        failed_attempts=payload.failed_attempts or 0,
        recent_resource_count=payload.recent_resource_count or 1,
        resource_sensitivity=payload.resource_sensitivity or ResourceSensitivity.MEDIUM,
        resource_name=payload.resource_name or "Protected Resource",
    )

@router.get("/access-requests/{request_id}", response_model=RiskAssessment)
def get_access_request_risk(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Evaluate and retrieve risk assessment for a specific access request ID."""
    from app.models.access_request import AccessRequest
    req = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()
    if req and current_user.role != UserRole.ADMIN and req.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return RiskService.evaluate_access_request_by_id(request_id, db)

@router.get("/scenarios", response_model=List[ScenarioRiskResult])
def evaluate_demo_scenarios(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Evaluate all 3 deterministic demo scenarios and return their risk assessments."""
    scenarios = get_demo_scenarios(db)
    results = []

    for sc in scenarios:
        # Determine resource sensitivity
        res_sensitivity = ResourceSensitivity.HIGH
        if sc.resource_id:
            res_obj = db.query(Resource).filter(Resource.id == sc.resource_id).first()
            if res_obj:
                res_sensitivity = res_obj.sensitivity

        # Parse device posture
        posture = DevicePosture.HEALTHY
        if sc.device_posture == "Unknown":
            posture = DevicePosture.UNKNOWN
        elif sc.device_posture == "Compromised":
            posture = DevicePosture.COMPROMISED
        elif sc.device_posture == "Unhealthy":
            posture = DevicePosture.UNHEALTHY

        risk_assessment = RiskEngine.calculate_risk(
            device_posture=posture,
            device_managed=False if posture == DevicePosture.UNKNOWN else True,
            device_encrypted=False if posture == DevicePosture.COMPROMISED else True,
            device_compromised=(posture == DevicePosture.COMPROMISED),
            ip_reputation=sc.network.ip_reputation,
            source_ip=sc.network.source_ip,
            network_type=sc.network.network_type,
            is_vpn=sc.network.is_vpn,
            is_tor=sc.network.is_tor,
            unusual_location=sc.behavior.unusual_location,
            country=sc.network.country,
            city=sc.network.city,
            unusual_time=sc.behavior.unusual_time,
            unusual_resource=sc.behavior.unusual_resource,
            failed_attempts=sc.behavior.failed_attempts,
            recent_resource_count=sc.behavior.recent_resource_count if hasattr(sc.behavior, "recent_resource_count") else 1,
            resource_sensitivity=res_sensitivity,
            resource_name=sc.resource_name,
        )

        results.append(
            ScenarioRiskResult(
                scenario_id=sc.id,
                scenario_name=sc.name,
                description=sc.description,
                risk=risk_assessment,
            )
        )

    return results
