from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.policy.schemas import PolicyCreate, PolicyUpdate, PolicyRead
from app.policy.service import PolicyService
from app.policy.models import PolicyDecision
from pydantic import BaseModel

router = APIRouter(prefix="/policies", tags=["Policies"])

class EvaluatePreviewRequest(BaseModel):
    access_request_id: str

from app.api.dependencies import get_current_user, require_admin
from app.models.user import User

@router.post("/evaluate-preview", response_model=PolicyDecision)
def evaluate_preview(req: EvaluatePreviewRequest, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    # This evaluates the policy logic ONLY (not microsegmentation)
    return PolicyService.evaluate_access_request_by_id(req.access_request_id, db)

@router.get("", response_model=List[PolicyRead])
def get_policies(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return PolicyService.get_policies(db)

@router.get("/{policy_id}", response_model=PolicyRead)
def get_policy(policy_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    policy = PolicyService.get_policy(db, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy

@router.post("", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
def create_policy(policy_in: PolicyCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return PolicyService.create_policy(db, policy_in)

@router.patch("/{policy_id}", response_model=PolicyRead)
def update_policy(policy_id: str, policy_in: PolicyUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    policy = PolicyService.update_policy(db, policy_id, policy_in)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy

@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(policy_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    if not PolicyService.delete_policy(db, policy_id):
        raise HTTPException(status_code=404, detail="Policy not found")
    return None
