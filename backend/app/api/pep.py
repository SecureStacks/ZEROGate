from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.pep.service import PEPService
from app.pep.schemas import EnforcementResult

from app.api.dependencies import get_current_user
from app.models.enums import UserRole
from app.models.user import User

router = APIRouter(prefix="/pep", tags=["pep"])

class EnforcementRequest(BaseModel):
    access_request_id: str

@router.post("/enforce", response_model=EnforcementResult)
def enforce_access(req: EnforcementRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        from app.models.access_request import AccessRequest
        access_req = db.query(AccessRequest).filter(AccessRequest.id == req.access_request_id).first()
        if access_req and current_user.role != UserRole.ADMIN and access_req.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        return PEPService.enforce_access(db, req.access_request_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
