from sqlalchemy.orm import Session
from app.pep.evaluator import PEPEvaluator
from app.pep.schemas import EnforcementResult
from app.models.pep import EnforcementEvent

class PEPService:
    @staticmethod
    def enforce_access(db: Session, access_request_id: str) -> EnforcementResult:
        result = PEPEvaluator.enforce_access(db, access_request_id)
        
        # Record the event
        event = EnforcementEvent(
            access_request_id=result.request_id,
            decision=result.decision,
            access_granted=result.access_granted,
            policy_id=result.policy_id,
            segment_rule_id=None,
            source_segment=result.segment_check.source_segment if result.segment_check else None,
            destination_segment=result.segment_check.destination_segment if result.segment_check else None,
            reason=result.reason
        )
        
        db.add(event)
        db.commit()
        
        return result
