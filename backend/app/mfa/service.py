import random
import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Tuple

from app.models.mfa import MFAChallenge, MFAChallengeStatus
from app.models.access_request import AccessRequest
from app.models.enums import PolicyEffect
from app.policy.service import PolicyService
from app.mfa.schemas import MFAChallengeResponse

class MFAService:
    @staticmethod
    def _hash_code(code: str) -> str:
        return hashlib.sha256(code.encode('utf-8')).hexdigest()

    @staticmethod
    def create_challenge(db: Session, request_id: str) -> MFAChallengeResponse:
        access_request = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()
        if not access_request:
            raise HTTPException(status_code=404, detail="AccessRequest not found")

        # Security Check: Ensure PDP actually requires MFA
        pdp_decision = PolicyService.evaluate_access_request_by_id(request_id, db)
        if pdp_decision.decision == PolicyEffect.DENY.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Access denied by PDP. MFA cannot override a hard deny."
            )
        if pdp_decision.decision == PolicyEffect.ALLOW.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="MFA not required for this request."
            )

        # Invalidate any existing pending challenges for this request
        existing_challenges = db.query(MFAChallenge).filter(
            MFAChallenge.request_id == request_id,
            MFAChallenge.status == MFAChallengeStatus.PENDING
        ).all()
        for challenge in existing_challenges:
            challenge.status = MFAChallengeStatus.EXPIRED
        
        # Generate simulated OTP
        otp_code = f"{random.randint(0, 999999):06d}"
        
        new_challenge = MFAChallenge(
            request_id=request_id,
            user_id=access_request.user_id,
            challenge_type="SIMULATED_OTP",
            status=MFAChallengeStatus.PENDING,
            code_hash=MFAService._hash_code(otp_code),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            max_attempts=3
        )
        db.add(new_challenge)
        db.commit()
        db.refresh(new_challenge)
        
        response = MFAChallengeResponse.model_validate(new_challenge)
        response.demo_otp = otp_code
        return response

    @staticmethod
    def verify_challenge(db: Session, challenge_id: str, code: str) -> MFAChallenge:
        challenge = db.query(MFAChallenge).filter(MFAChallenge.id == challenge_id).first()
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
            
        if challenge.status != MFAChallengeStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Challenge is already {challenge.status}")
            
        expires_at = challenge.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
            
        if datetime.now(timezone.utc) > expires_at:
            challenge.status = MFAChallengeStatus.EXPIRED
            db.commit()
            raise HTTPException(status_code=400, detail="Challenge has expired")
            
        if challenge.attempts >= challenge.max_attempts:
            challenge.status = MFAChallengeStatus.FAILED
            db.commit()
            raise HTTPException(status_code=400, detail="Maximum attempts exceeded. Challenge failed.")
            
        challenge.attempts += 1
        
        if challenge.code_hash == MFAService._hash_code(code):
            challenge.status = MFAChallengeStatus.VERIFIED
            challenge.verified_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(challenge)
            return challenge
        else:
            if challenge.attempts >= challenge.max_attempts:
                challenge.status = MFAChallengeStatus.FAILED
            db.commit()
            db.refresh(challenge)
            raise HTTPException(status_code=400, detail="Invalid OTP code")

    @staticmethod
    def is_challenge_verified(db: Session, request_id: str) -> bool:
        # Check if the latest challenge for this request is verified
        challenge = db.query(MFAChallenge).filter(
            MFAChallenge.request_id == request_id
        ).order_by(MFAChallenge.created_at.desc()).first()
        
        if not challenge or challenge.status != MFAChallengeStatus.VERIFIED:
            return False
            
        # Replay protection / Expiration check even on verified challenges
        # A verified challenge is only good if it hasn't expired
        expires_at = challenge.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
            
        if datetime.now(timezone.utc) > expires_at:
            return False
            
        return True
