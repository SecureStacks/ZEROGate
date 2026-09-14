from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.policy.models import PolicyDecision
from app.policy.service import PolicyService

from app.api.dependencies import get_current_user
from app.models.enums import UserRole
from app.models.user import User

router = APIRouter(prefix="/pdp", tags=["Policy Decision Point"])

class EvaluateRequest(BaseModel):
    access_request_id: str

@router.post("/evaluate", response_model=PolicyDecision)
def evaluate_pdp(request: EvaluateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Evaluate access request against active policies."""
    from app.models.access_request import AccessRequest
    req = db.query(AccessRequest).filter(AccessRequest.id == request.access_request_id).first()
    if req and current_user.role != UserRole.ADMIN and req.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return PolicyService.evaluate_access_request_by_id(request.access_request_id, db)
