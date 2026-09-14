from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.mfa.schemas import MFAChallengeCreateRequest, MFAChallengeVerifyRequest, MFAChallengeResponse
from app.mfa.service import MFAService

from app.api.dependencies import get_current_user
from app.models.enums import UserRole
from app.models.user import User

router = APIRouter(prefix="/mfa", tags=["MFA (Simulated)"])

@router.post("/challenge", response_model=MFAChallengeResponse)
def create_mfa_challenge(request: MFAChallengeCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a simulated MFA challenge for a given access request."""
    from app.models.access_request import AccessRequest
    req = db.query(AccessRequest).filter(AccessRequest.id == request.access_request_id).first()
    if req and current_user.role != UserRole.ADMIN and req.user_id != current_user.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not authorized")
    return MFAService.create_challenge(db, request.access_request_id)

@router.post("/verify", response_model=MFAChallengeResponse)
def verify_mfa_challenge(request: MFAChallengeVerifyRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Verify an MFA challenge using the provided OTP."""
    from fastapi import HTTPException
    from app.models.mfa import MFAChallenge
    from app.models.access_request import AccessRequest
    challenge_obj = db.query(MFAChallenge).filter(MFAChallenge.id == request.challenge_id).first()
    if challenge_obj:
        req = db.query(AccessRequest).filter(AccessRequest.id == challenge_obj.request_id).first()
        if req and current_user.role != UserRole.ADMIN and req.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
            
    challenge = MFAService.verify_challenge(db, request.challenge_id, request.code)
    return MFAChallengeResponse.model_validate(challenge)

@router.get("/challenge/{challenge_id}", response_model=MFAChallengeResponse)
def get_mfa_challenge(challenge_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve the status of an MFA challenge."""
    from fastapi import HTTPException
    from app.models.mfa import MFAChallenge
    from app.models.access_request import AccessRequest
    challenge = db.query(MFAChallenge).filter(MFAChallenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
        
    req = db.query(AccessRequest).filter(AccessRequest.id == challenge.request_id).first()
    if req and current_user.role != UserRole.ADMIN and req.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return MFAChallengeResponse.model_validate(challenge)
