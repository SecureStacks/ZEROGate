from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from app.risk.engine import RiskEngine
from app.risk.models import RiskAssessment
from app.models.access_request import AccessRequest
from app.models.user import User
from app.models.device import Device
from app.models.resource import Resource
from app.models.enums import (
    DevicePosture,
    IPReputation,
    NetworkType,
    ResourceSensitivity,
)

class RiskService:
    """Service layer coordinating DB entities and the Risk Engine."""

    @staticmethod
    def evaluate_access_request_by_id(request_id: str, db: Session) -> RiskAssessment:
        """Fetch AccessRequest and linked entities from DB, then evaluate risk."""
        req: Optional[AccessRequest] = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Access Request with ID '{request_id}' not found"
            )

        device: Optional[Device] = db.query(Device).filter(Device.id == req.device_id).first()
        resource: Optional[Resource] = db.query(Resource).filter(Resource.id == req.resource_id).first()

        device_posture = device.posture_status if device else DevicePosture.UNKNOWN
        device_managed = device.managed if device else False
        device_encrypted = device.encrypted if device else False
        device_compromised = device.compromised if device else False

        resource_sensitivity = resource.sensitivity if resource else ResourceSensitivity.MEDIUM
        resource_name = resource.name if resource else "Unknown Resource"

        return RiskEngine.calculate_risk(
            # Device Signals
            device_posture=device_posture,
            device_managed=device_managed,
            device_encrypted=device_encrypted,
            device_compromised=device_compromised,
            # Network & IP Signals
            ip_reputation=req.ip_reputation,
            source_ip=req.source_ip,
            network_type=req.network_type,
            is_vpn=req.is_vpn,
            is_tor=req.is_tor,
            # Geo Signals
            unusual_location=req.unusual_location,
            country=req.country,
            city=req.city,
            # Behavioral Signals
            unusual_time=req.unusual_time,
            unusual_resource=req.unusual_resource,
            failed_attempts=req.failed_attempts,
            recent_resource_count=req.recent_resource_count,
            # Resource Signals
            resource_sensitivity=resource_sensitivity,
            resource_name=resource_name,
        )

    @staticmethod
    def evaluate_context_payload(
        device_posture: DevicePosture,
        device_managed: bool,
        device_encrypted: bool,
        device_compromised: bool,
        ip_reputation: IPReputation,
        source_ip: str,
        network_type: NetworkType,
        is_vpn: bool,
        is_tor: bool,
        unusual_location: bool,
        country: str,
        city: str,
        unusual_time: bool,
        unusual_resource: bool,
        failed_attempts: int,
        recent_resource_count: int,
        resource_sensitivity: ResourceSensitivity,
        resource_name: str,
    ) -> RiskAssessment:
        """Directly calculate risk for a provided context payload without requiring a saved DB record."""
        return RiskEngine.calculate_risk(
            device_posture=device_posture,
            device_managed=device_managed,
            device_encrypted=device_encrypted,
            device_compromised=device_compromised,
            ip_reputation=ip_reputation,
            source_ip=source_ip,
            network_type=network_type,
            is_vpn=is_vpn,
            is_tor=is_tor,
            unusual_location=unusual_location,
            country=country,
            city=city,
            unusual_time=unusual_time,
            unusual_resource=unusual_resource,
            failed_attempts=failed_attempts,
            recent_resource_count=recent_resource_count,
            resource_sensitivity=resource_sensitivity,
            resource_name=resource_name,
        )
