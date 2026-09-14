from typing import List, Optional
from app.risk.models import RiskFactor
from app.models.enums import (
    DevicePosture,
    IPReputation,
    NetworkType,
    ResourceSensitivity,
)

# ---------------------------------------------------------------------------
# Signal Weight Constants (Deterministic Hackathon Simulation Values)
# ---------------------------------------------------------------------------

DEVICE_POSTURE_WEIGHTS = {
    DevicePosture.HEALTHY: 0,
    DevicePosture.UNKNOWN: 15,
    DevicePosture.UNHEALTHY: 30,
    DevicePosture.COMPROMISED: 60,
}

UNMANAGED_DEVICE_WEIGHT = 10
UNENCRYPTED_DEVICE_WEIGHT = 5

IP_REPUTATION_WEIGHTS = {
    IPReputation.TRUSTED: 0,
    IPReputation.UNKNOWN: 10,
    IPReputation.SUSPICIOUS: 30,
    IPReputation.MALICIOUS: 50,
}

NETWORK_TYPE_WEIGHTS = {
    NetworkType.CORPORATE: 0,
    NetworkType.HOME: 5,
    NetworkType.MOBILE: 10,
    NetworkType.PUBLIC_WIFI: 15,
    NetworkType.UNKNOWN: 20,
}

VPN_WEIGHT = 5
TOR_WEIGHT = 25

UNUSUAL_LOCATION_WEIGHT = 20
UNUSUAL_TIME_WEIGHT = 10
UNUSUAL_RESOURCE_WEIGHT = 15

RESOURCE_SENSITIVITY_WEIGHTS = {
    ResourceSensitivity.LOW: 0,
    ResourceSensitivity.MEDIUM: 5,
    ResourceSensitivity.HIGH: 10,
    ResourceSensitivity.CRITICAL: 15,
}

# ---------------------------------------------------------------------------
# Signal Evaluators
# ---------------------------------------------------------------------------

def evaluate_device_signals(
    posture: DevicePosture,
    managed: bool = True,
    encrypted: bool = True,
    compromised: bool = False,
) -> List[RiskFactor]:
    factors: List[RiskFactor] = []

    # 1. Posture state
    pts = DEVICE_POSTURE_WEIGHTS.get(posture, 15)
    if pts > 0:
        factors.append(
            RiskFactor(
                name="device_posture",
                category="device",
                value=posture.value if hasattr(posture, "value") else str(posture),
                points=pts,
                reason=f"Device security posture is evaluated as {posture.value if hasattr(posture, 'value') else posture}",
            )
        )

    # 2. Management status
    if not managed:
        factors.append(
            RiskFactor(
                name="unmanaged_device",
                category="device",
                value="Unmanaged",
                points=UNMANAGED_DEVICE_WEIGHT,
                reason="Device is unmanaged and not enrolled in corporate MDM",
            )
        )

    # 3. Encryption status
    if not encrypted:
        factors.append(
            RiskFactor(
                name="unencrypted_storage",
                category="device",
                value="Unencrypted",
                points=UNENCRYPTED_DEVICE_WEIGHT,
                reason="Full disk encryption is disabled or missing on the device",
            )
        )

    return factors


def evaluate_ip_signals(ip_rep: IPReputation, source_ip: str) -> List[RiskFactor]:
    factors: List[RiskFactor] = []
    pts = IP_REPUTATION_WEIGHTS.get(ip_rep, 10)
    if pts > 0:
        factors.append(
            RiskFactor(
                name="ip_reputation",
                category="ip",
                value=ip_rep.value if hasattr(ip_rep, "value") else str(ip_rep),
                points=pts,
                reason=f"Source IP {source_ip} exhibits {ip_rep.value if hasattr(ip_rep, 'value') else ip_rep} reputation",
            )
        )
    return factors


def evaluate_network_signals(
    net_type: NetworkType,
    is_vpn: bool = False,
    is_tor: bool = False,
) -> List[RiskFactor]:
    factors: List[RiskFactor] = []

    pts = NETWORK_TYPE_WEIGHTS.get(net_type, 20)
    if pts > 0:
        factors.append(
            RiskFactor(
                name="network_type",
                category="network",
                value=net_type.value if hasattr(net_type, "value") else str(net_type),
                points=pts,
                reason=f"Request originated from {net_type.value if hasattr(net_type, 'value') else net_type} network",
            )
        )

    if is_vpn:
        factors.append(
            RiskFactor(
                name="vpn_tunnel",
                category="network",
                value="VPN Active",
                points=VPN_WEIGHT,
                reason="Connection established over an external VPN / proxy tunnel",
            )
        )

    if is_tor:
        factors.append(
            RiskFactor(
                name="tor_anonymizer",
                category="network",
                value="TOR Active",
                points=TOR_WEIGHT,
                reason="Connection routed through TOR anonymizing exit relay",
            )
        )

    return factors


def evaluate_geographic_signals(unusual_location: bool, country: str, city: str) -> List[RiskFactor]:
    factors: List[RiskFactor] = []
    if unusual_location:
        factors.append(
            RiskFactor(
                name="unusual_location",
                category="geo",
                value=f"{city}, {country}",
                points=UNUSUAL_LOCATION_WEIGHT,
                reason=f"Geographic location anomaly detected from {city}, {country}",
            )
        )
    return factors


def evaluate_behavioral_signals(
    unusual_time: bool = False,
    unusual_resource: bool = False,
    failed_attempts: int = 0,
    recent_resource_count: int = 1,
) -> List[RiskFactor]:
    factors: List[RiskFactor] = []

    if unusual_time:
        factors.append(
            RiskFactor(
                name="unusual_time",
                category="behavior",
                value="Off-hours Access",
                points=UNUSUAL_TIME_WEIGHT,
                reason="Access request initiated outside normal operating hours",
            )
        )

    if unusual_resource:
        factors.append(
            RiskFactor(
                name="unusual_resource",
                category="behavior",
                value="Atypical Target",
                points=UNUSUAL_RESOURCE_WEIGHT,
                reason="Target resource deviates significantly from user's standard activity profile",
            )
        )

    # Failed attempts
    if failed_attempts >= 5:
        factors.append(
            RiskFactor(
                name="excessive_failed_attempts",
                category="behavior",
                value=f"{failed_attempts} attempts",
                points=30,
                reason=f"5+ recent failed authentication attempts ({failed_attempts})",
            )
        )
    elif failed_attempts >= 3:
        factors.append(
            RiskFactor(
                name="multiple_failed_attempts",
                category="behavior",
                value=f"{failed_attempts} attempts",
                points=20,
                reason=f"3–4 recent failed authentication attempts ({failed_attempts})",
            )
        )
    elif failed_attempts >= 1:
        factors.append(
            RiskFactor(
                name="failed_attempts",
                category="behavior",
                value=f"{failed_attempts} attempts",
                points=10,
                reason=f"1–2 recent failed authentication attempts ({failed_attempts})",
            )
        )

    # Recent resource count
    if recent_resource_count >= 7:
        factors.append(
            RiskFactor(
                name="high_resource_spread",
                category="behavior",
                value=f"{recent_resource_count} resources",
                points=10,
                reason=f"Rapid access burst across 7+ distinct internal resources ({recent_resource_count})",
            )
        )
    elif recent_resource_count >= 4:
        factors.append(
            RiskFactor(
                name="moderate_resource_spread",
                category="behavior",
                value=f"{recent_resource_count} resources",
                points=5,
                reason=f"Access across 4–6 distinct resources in short time window ({recent_resource_count})",
            )
        )

    return factors


def evaluate_resource_sensitivity(sensitivity: ResourceSensitivity, resource_name: str) -> List[RiskFactor]:
    factors: List[RiskFactor] = []
    pts = RESOURCE_SENSITIVITY_WEIGHTS.get(sensitivity, 5)
    if pts > 0:
        factors.append(
            RiskFactor(
                name="resource_sensitivity",
                category="resource",
                value=sensitivity.value if hasattr(sensitivity, "value") else str(sensitivity),
                points=pts,
                reason=f"Target resource '{resource_name}' holds {sensitivity.value if hasattr(sensitivity, 'value') else sensitivity} sensitivity classification",
            )
        )
    return factors
