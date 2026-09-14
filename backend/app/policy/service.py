from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import HTTPException, status

from app.models.policy import Policy
from app.models.access_request import AccessRequest
from app.models.user import User
from app.models.device import Device
from app.models.resource import Resource

from app.risk.service import RiskService
from app.policy.evaluator import PolicyEvaluator
from app.policy.models import PolicyDecision
from app.policy.schemas import PolicyCreate, PolicyUpdate

import uuid

class PolicyService:
    @staticmethod
    def evaluate_access_request_by_id(request_id: str, db: Session, mfa_verified: bool = False) -> PolicyDecision:
        access_req: Optional[AccessRequest] = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()
        if not access_req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Access Request '{request_id}' not found")

        user: Optional[User] = db.query(User).filter(User.id == access_req.user_id).first()
        device: Optional[Device] = db.query(Device).filter(Device.id == access_req.device_id).first()
        resource: Optional[Resource] = db.query(Resource).filter(Resource.id == access_req.resource_id).first()

        if not user or not device or not resource:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incomplete access request context")

        risk = RiskService.evaluate_access_request_by_id(request_id, db)
        
        active_policies = db.query(Policy).filter(Policy.enabled == True).all()

        return PolicyEvaluator.evaluate_access(user, device, resource, access_req, risk, active_policies, mfa_verified)

    @staticmethod
    def create_policy(db: Session, policy_in: PolicyCreate) -> Policy:
        policy = Policy(**policy_in.model_dump(), id=str(uuid.uuid4()))
        db.add(policy)
        db.commit()
        db.refresh(policy)
        return policy

    @staticmethod
    def get_policies(db: Session) -> List[Policy]:
        return db.query(Policy).order_by(Policy.priority).all()

    @staticmethod
    def get_policy(db: Session, policy_id: str) -> Optional[Policy]:
        return db.query(Policy).filter(Policy.id == policy_id).first()

    @staticmethod
    def update_policy(db: Session, policy_id: str, policy_in: PolicyUpdate) -> Optional[Policy]:
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            return None
            
        update_data = policy_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(policy, field, value)
            
        db.commit()
        db.refresh(policy)
        return policy

    @staticmethod
    def delete_policy(db: Session, policy_id: str) -> bool:
        policy = db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            return False
            
        db.delete(policy)
        db.commit()
        return True
