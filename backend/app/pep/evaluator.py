from sqlalchemy.orm import Session
from app.models.access_request import AccessRequest
from app.models.resource import Resource
from app.models.enums import PolicyEffect
from app.pep.schemas import EnforcementResult
from app.policy.service import PolicyService
from app.segmentation.evaluator import SegmentationEvaluator
from app.models.pep import EnforcementEvent

class PEPEvaluator:
    @staticmethod
    def enforce_access(db: Session, access_request_id: str) -> EnforcementResult:
        access_request = db.query(AccessRequest).filter(AccessRequest.id == access_request_id).first()
        if not access_request:
            res = EnforcementResult(
                request_id=access_request_id,
                decision="DENY",
                enforced=True,
                access_granted=False,
                resource="Unknown",
                reason="AccessRequest not found."
            )
            PEPEvaluator._save_event(db, res)
            return res
            
        resource = db.query(Resource).filter(Resource.id == access_request.resource_id).first()
        resource_name = resource.name if resource else "Unknown Resource"
        destination_segment = resource.network_segment if resource else "Unknown"
        
        # 1. PDP Evaluation (incorporating MFA verified status)
        from app.mfa.service import MFAService
        mfa_verified = MFAService.is_challenge_verified(db, access_request.id)
        
        pdp_decision = PolicyService.evaluate_access_request_by_id(access_request.id, db, mfa_verified)
        
        # 2. PEP Enforcement based on PDP decision
        if pdp_decision.decision == PolicyEffect.DENY.value:
            res = EnforcementResult(
                request_id=access_request.id,
                decision=PolicyEffect.DENY.value,
                enforced=True,
                access_granted=False,
                resource=resource_name,
                policy_id=pdp_decision.policy_id,
                policy_name=pdp_decision.policy_name,
                reason=f"Access denied by PDP policy: {pdp_decision.reason}"
            )
            PEPEvaluator._save_event(db, res, access_request.source_segment, destination_segment)
            return res
            
        if pdp_decision.decision == PolicyEffect.MFA_REQUIRED.value:
            res = EnforcementResult(
                request_id=access_request.id,
                decision=PolicyEffect.MFA_REQUIRED.value,
                enforced=False,
                access_granted=False,
                resource=resource_name,
                policy_id=pdp_decision.policy_id,
                policy_name=pdp_decision.policy_name,
                reason=f"Step-up authentication required: {pdp_decision.reason}"
            )
            PEPEvaluator._save_event(db, res, access_request.source_segment, destination_segment)
            return res
            
        # 3. Microsegmentation Check (only if PDP ALLOW)
        if pdp_decision.decision == PolicyEffect.ALLOW.value:
            segment_decision = SegmentationEvaluator.check_segment_access(
                db, 
                access_request.source_segment, 
                destination_segment
            )
            
            if segment_decision.allowed:
                res = EnforcementResult(
                    request_id=access_request.id,
                    decision=PolicyEffect.ALLOW.value,
                    enforced=True,
                    access_granted=True,
                    resource=resource_name,
                    policy_id=pdp_decision.policy_id,
                    policy_name=pdp_decision.policy_name,
                    reason="Access granted by PDP and permitted by microsegmentation.",
                    segment_check=segment_decision
                )
                PEPEvaluator._save_event(db, res, access_request.source_segment, destination_segment, segment_decision.rule_id if hasattr(segment_decision, 'rule_id') else None)
                return res
            else:
                res = EnforcementResult(
                    request_id=access_request.id,
                    decision=PolicyEffect.ALLOW.value,  # The PDP decision was ALLOW
                    enforced=True,
                    access_granted=False,  # But access is blocked
                    resource=resource_name,
                    policy_id=pdp_decision.policy_id,
                    policy_name=pdp_decision.policy_name,
                    reason=f"East-west movement blocked by microsegmentation: {segment_decision.reason}",
                    segment_check=segment_decision
                )
                PEPEvaluator._save_event(db, res, access_request.source_segment, destination_segment)
                return res

    @staticmethod
    def _save_event(db: Session, res: EnforcementResult, source_segment: str = None, destination_segment: str = None, segment_rule_id: str = None):
        event = EnforcementEvent(
            access_request_id=res.request_id,
            decision=res.decision,
            access_granted=res.access_granted,
            policy_id=res.policy_id,
            segment_rule_id=segment_rule_id,
            source_segment=source_segment,
            destination_segment=destination_segment,
            reason=res.reason
        )
        db.add(event)
        db.commit()
