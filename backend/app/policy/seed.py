from sqlalchemy.orm import Session
from app.models.policy import Policy
from app.models.enums import PolicyEffect, UserRole, DevicePosture, IPReputation
from app.models.resource import Resource
import uuid

def seed_policies(db: Session):
    existing_policies = {p.name: p for p in db.query(Policy).all()}
    resources = {r.name: r for r in db.query(Resource).all()}
    
    git_repo = resources.get("Git Repository")
    hr_db = resources.get("HR Database")
    fin_db = resources.get("Finance Database")

    policies_to_seed = [
        {
            "name": "Developer Git Access",
            "effect": PolicyEffect.ALLOW,
            "required_role": UserRole.DEVELOPER,
            "required_device_posture": DevicePosture.HEALTHY,
            "require_managed_device": True,
            "resource_id": git_repo.id if git_repo else None,
            "max_risk_score": 39,
            "priority": 10
        },
        {
            "name": "Developer Elevated Risk Step-Up",
            "effect": PolicyEffect.MFA_REQUIRED,
            "required_role": UserRole.DEVELOPER,
            "resource_id": git_repo.id if git_repo else None,
            "min_risk_score": 40,
            "max_risk_score": 69,
            "priority": 20
        },
        {
            "name": "Critical Risk Block",
            "effect": PolicyEffect.DENY,
            "min_risk_score": 70,
            "priority": 5
        },
        {
            "name": "Compromised Device Block",
            "effect": PolicyEffect.DENY,
            "required_device_posture": DevicePosture.COMPROMISED,
            "priority": 1
        },
        {
            "name": "Malicious IP Block",
            "effect": PolicyEffect.DENY,
            "ip_reputation": IPReputation.MALICIOUS,
            "priority": 2
        },
        {
            "name": "HR Secure Access",
            "effect": PolicyEffect.ALLOW,
            "required_role": UserRole.HR,
            "required_device_posture": DevicePosture.HEALTHY,
            "resource_id": hr_db.id if hr_db else None,
            "max_risk_score": 29,
            "priority": 10
        },
        {
            "name": "Finance Secure Access",
            "effect": PolicyEffect.ALLOW,
            "required_role": UserRole.FINANCE,
            "required_device_posture": DevicePosture.HEALTHY,
            "resource_id": fin_db.id if fin_db else None,
            "max_risk_score": 29,
            "priority": 10
        },
        {
            "name": "Administrative Access",
            "effect": PolicyEffect.ALLOW,
            "required_role": UserRole.ADMIN,
            "required_device_posture": DevicePosture.HEALTHY,
            "max_risk_score": 39,
            "priority": 10
        }
    ]

    for p_def in policies_to_seed:
        if p_def["name"] not in existing_policies:
            policy = Policy(id=str(uuid.uuid4()), **p_def)
            db.add(policy)
            
    db.commit()
