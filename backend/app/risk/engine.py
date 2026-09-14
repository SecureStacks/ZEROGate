from typing import List, Optional
from app.risk.models import RiskAssessment, RiskFactor, RiskLevel
from app.risk.signals import (
    evaluate_device_signals,
    evaluate_ip_signals,
    evaluate_network_signals,
    evaluate_geographic_signals,
    evaluate_behavioral_signals,
    evaluate_resource_sensitivity,
)
from app.models.enums import (
    DevicePosture,
    IPReputation,
    NetworkType,
    ResourceSensitivity,
)

class RiskEngine:
    """
    Deterministic, explainable Zero Trust Risk Engine.
    Evaluates multi-dimensional contextual signals and produces a normalized 0-100 score.
    """

    @staticmethod
    def classify_level(score: int) -> RiskLevel:
        """Deterministic boundary mapping."""
        if score <= 39:
            return RiskLevel.LOW
        elif score <= 69:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    @classmethod
    def calculate_risk(
        cls,
        # Device Signals
        device_posture: DevicePosture = DevicePosture.HEALTHY,
        device_managed: bool = True,
        device_encrypted: bool = True,
        device_compromised: bool = False,
        # Network & IP Signals
        ip_reputation: IPReputation = IPReputation.TRUSTED,
        source_ip: str = "10.0.4.15",
        network_type: NetworkType = NetworkType.CORPORATE,
        is_vpn: bool = False,
        is_tor: bool = False,
        # Geo Signals
        unusual_location: bool = False,
        country: str = "India",
        city: str = "Bengaluru",
        # Behavioral Signals
        unusual_time: bool = False,
        unusual_resource: bool = False,
        failed_attempts: int = 0,
        recent_resource_count: int = 1,
        # Resource Signals
        resource_sensitivity: ResourceSensitivity = ResourceSensitivity.MEDIUM,
        resource_name: str = "Protected Resource",
    ) -> RiskAssessment:
        factors: List[RiskFactor] = []

        # 1. Device Posture & Integrity
        factors.extend(
            evaluate_device_signals(
                posture=device_posture,
                managed=device_managed,
                encrypted=device_encrypted,
                compromised=device_compromised,
            )
        )

        # 2. IP Reputation
        factors.extend(
            evaluate_ip_signals(
                ip_rep=ip_reputation,
                source_ip=source_ip,
            )
        )

        # 3. Network Context (WiFi, VPN, TOR)
        factors.extend(
            evaluate_network_signals(
                net_type=network_type,
                is_vpn=is_vpn,
                is_tor=is_tor,
            )
        )

        # 4. Geographic Signals
        factors.extend(
            evaluate_geographic_signals(
                unusual_location=unusual_location,
                country=country,
                city=city,
            )
        )

        # 5. Behavioral Signals
        factors.extend(
            evaluate_behavioral_signals(
                unusual_time=unusual_time,
                unusual_resource=unusual_resource,
                failed_attempts=failed_attempts,
                recent_resource_count=recent_resource_count,
            )
        )

        # 6. Resource Sensitivity Modifier
        factors.extend(
            evaluate_resource_sensitivity(
                sensitivity=resource_sensitivity,
                resource_name=resource_name,
            )
        )

        # Raw Score Aggregation
        raw_score = sum(f.points for f in factors)

        # Normalized Capped Score (0-100)
        final_score = max(0, min(100, raw_score))

        # Classification
        level = cls.classify_level(final_score)

        # Executive summary
        if level == RiskLevel.LOW:
            summary = f"Low risk access context ({final_score}/100). Normal operational baseline."
        elif level == RiskLevel.MEDIUM:
            summary = f"Medium risk access context ({final_score}/100). Elevated contextual anomalies detected; candidate for Step-up MFA verification."
        else:
            summary = f"High risk access context ({final_score}/100). Critical posture/network threats identified; candidate for immediate termination."

        return RiskAssessment(
            score=final_score,
            level=level,
            raw_score=raw_score,
            factors=factors,
            summary=summary,
        )
