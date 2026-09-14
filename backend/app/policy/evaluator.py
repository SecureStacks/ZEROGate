from typing import List, Tuple
from app.models.user import User
from app.models.device import Device
from app.models.resource import Resource
from app.models.access_request import AccessRequest
from app.models.policy import Policy
from app.models.enums import PolicyEffect, UserStatus
from app.risk.models import RiskAssessment
from app.policy.models import PolicyDecision, PolicyEvaluationTrace

class PolicyEvaluator:
    @staticmethod
    def evaluate_access(
        user: User,
        device: Device,
        resource: Resource,
        access_request: AccessRequest,
        risk: RiskAssessment,
        policies: List[Policy],
        mfa_verified: bool = False
    ) -> PolicyDecision:
        traces: List[PolicyEvaluationTrace] = []
        
        # 1. Mandatory Safety Guards
        if user.status != UserStatus.ACTIVE:
            return PolicyDecision(
                decision=PolicyEffect.DENY,
                reason="User is disabled",
                risk_score=risk.score,
                risk_level=risk.level,
                evaluated_policies=[]
            )
            
        if not resource.enabled:
            return PolicyDecision(
                decision=PolicyEffect.DENY,
                reason="Resource is disabled",
                risk_score=risk.score,
                risk_level=risk.level,
                evaluated_policies=[]
            )

        # 2. Sort policies by priority (lowest number first), then ID
        sorted_policies = sorted(policies, key=lambda p: (p.priority, p.id))
        
        # 3. Evaluate each policy
        for policy in sorted_policies:
            if not policy.enabled:
                continue
                
            matched, reason = PolicyEvaluator._evaluate_conditions(policy, user, device, resource, access_request, risk)
            
            traces.append(PolicyEvaluationTrace(
                policy_name=policy.name,
                matched=matched,
                reason=reason
            ))
            
            if matched:
                effect = policy.effect
                final_reason = reason
                if effect == PolicyEffect.MFA_REQUIRED and mfa_verified:
                    effect = PolicyEffect.ALLOW
                    final_reason = f"{reason} (MFA Verified)"
                
                return PolicyDecision(
                    decision=effect,
                    policy_id=policy.id,
                    policy_name=policy.name,
                    reason=final_reason,
                    risk_score=risk.score,
                    risk_level=risk.level,
                    evaluated_policies=traces
                )

        # 4. Default Deny
        return PolicyDecision(
            decision=PolicyEffect.DENY,
            reason="No matching policy (Default Deny)",
            risk_score=risk.score,
            risk_level=risk.level,
            evaluated_policies=traces
        )

    @staticmethod
    def _evaluate_conditions(
        policy: Policy,
        user: User,
        device: Device,
        resource: Resource,
        access_request: AccessRequest,
        risk: RiskAssessment
    ) -> Tuple[bool, str]:
        
        reasons = []

        if policy.required_role and user.role != policy.required_role:
            return False, f"Role mismatch: user is {user.role}, policy requires {policy.required_role}"
        elif policy.required_role:
            reasons.append(f"Role={policy.required_role}")

        if policy.required_device_posture and device.posture_status != policy.required_device_posture:
            return False, f"Device posture mismatch: {device.posture_status}"
        elif policy.required_device_posture:
            reasons.append(f"Device={policy.required_device_posture}")

        if policy.require_managed_device and not device.managed:
            return False, "Device is unmanaged"
        elif policy.require_managed_device:
            reasons.append("Managed=True")

        if policy.resource_id and resource.id != policy.resource_id:
            return False, "Resource ID mismatch"
        elif policy.resource_id:
            reasons.append(f"Resource={resource.name}")

        if policy.min_risk_score is not None and risk.score < policy.min_risk_score:
            return False, f"Risk score {risk.score} is below minimum {policy.min_risk_score}"
        elif policy.min_risk_score is not None:
            reasons.append(f"Risk>={policy.min_risk_score}")

        if policy.max_risk_score is not None and risk.score > policy.max_risk_score:
            return False, f"Risk score {risk.score} exceeds maximum {policy.max_risk_score}"
        elif policy.max_risk_score is not None:
            reasons.append(f"Risk<={policy.max_risk_score}")

        if policy.network_type and access_request.network_type != policy.network_type:
            return False, f"Network type mismatch: {access_request.network_type}"
        elif policy.network_type:
            reasons.append(f"Network={policy.network_type}")

        if policy.ip_reputation and access_request.ip_reputation != policy.ip_reputation:
            return False, f"IP Reputation mismatch: {access_request.ip_reputation}"
        elif policy.ip_reputation:
            reasons.append(f"IPRep={policy.ip_reputation}")

        if policy.require_known_network and not access_request.is_known_network:
            return False, "Unknown network"
        elif policy.require_known_network:
            reasons.append("KnownNetwork=True")

        reason_str = ", ".join(reasons) if reasons else "Match all"
        return True, reason_str
