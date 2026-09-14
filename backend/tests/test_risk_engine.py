import pytest
from app.risk.engine import RiskEngine
from app.risk.models import RiskLevel
from app.models.enums import (
    DevicePosture,
    IPReputation,
    NetworkType,
    ResourceSensitivity,
)
from app.seed.seed_data import seed_database
from app.models.access_request import AccessRequest

# ===========================================================================
# Unit Tests for Risk Signals & Engine
# ===========================================================================

def test_01_healthy_managed_corporate_low_risk():
    """TEST 01: Healthy managed device + corporate network + trusted IP => low risk"""
    result = RiskEngine.calculate_risk(
        device_posture=DevicePosture.HEALTHY,
        device_managed=True,
        device_encrypted=True,
        ip_reputation=IPReputation.TRUSTED,
        network_type=NetworkType.CORPORATE,
        resource_sensitivity=ResourceSensitivity.LOW,
    )
    assert result.score == 0
    assert result.level == RiskLevel.LOW
    assert len(result.factors) == 0

def test_02_unknown_device_points():
    """TEST 02: Unknown device => +15"""
    result = RiskEngine.calculate_risk(
        device_posture=DevicePosture.UNKNOWN,
        device_managed=True,
        device_encrypted=True,
        ip_reputation=IPReputation.TRUSTED,
        network_type=NetworkType.CORPORATE,
        resource_sensitivity=ResourceSensitivity.LOW,
    )
    assert result.score == 15
    factor = next(f for f in result.factors if f.name == "device_posture")
    assert factor.points == 15

def test_03_unhealthy_device_points():
    """TEST 03: Unhealthy device => +30"""
    result = RiskEngine.calculate_risk(
        device_posture=DevicePosture.UNHEALTHY,
        device_managed=True,
        device_encrypted=True,
        ip_reputation=IPReputation.TRUSTED,
        network_type=NetworkType.CORPORATE,
        resource_sensitivity=ResourceSensitivity.LOW,
    )
    assert result.score == 30
    factor = next(f for f in result.factors if f.name == "device_posture")
    assert factor.points == 30

def test_04_compromised_device_points():
    """TEST 04: Compromised device => +60"""
    result = RiskEngine.calculate_risk(
        device_posture=DevicePosture.COMPROMISED,
        device_managed=True,
        device_encrypted=True,
        ip_reputation=IPReputation.TRUSTED,
        network_type=NetworkType.CORPORATE,
        resource_sensitivity=ResourceSensitivity.LOW,
    )
    assert result.score == 60
    factor = next(f for f in result.factors if f.name == "device_posture")
    assert factor.points == 60

def test_05_suspicious_ip_points():
    """TEST 05: Suspicious IP => +30"""
    result = RiskEngine.calculate_risk(
        device_posture=DevicePosture.HEALTHY,
        ip_reputation=IPReputation.SUSPICIOUS,
        network_type=NetworkType.CORPORATE,
        resource_sensitivity=ResourceSensitivity.LOW,
    )
    assert result.score == 30
    factor = next(f for f in result.factors if f.name == "ip_reputation")
    assert factor.points == 30

def test_06_malicious_ip_points():
    """TEST 06: Malicious IP => +50"""
    result = RiskEngine.calculate_risk(
        device_posture=DevicePosture.HEALTHY,
        ip_reputation=IPReputation.MALICIOUS,
        network_type=NetworkType.CORPORATE,
        resource_sensitivity=ResourceSensitivity.LOW,
    )
    assert result.score == 50
    factor = next(f for f in result.factors if f.name == "ip_reputation")
    assert factor.points == 50

def test_07_public_wifi_points():
    """TEST 07: Public WiFi => +15"""
    result = RiskEngine.calculate_risk(
        device_posture=DevicePosture.HEALTHY,
        ip_reputation=IPReputation.TRUSTED,
        network_type=NetworkType.PUBLIC_WIFI,
        resource_sensitivity=ResourceSensitivity.LOW,
    )
    assert result.score == 15
    factor = next(f for f in result.factors if f.name == "network_type")
    assert factor.points == 15

def test_08_tor_modifier_points():
    """TEST 08: TOR => +25"""
    result = RiskEngine.calculate_risk(
        device_posture=DevicePosture.HEALTHY,
        ip_reputation=IPReputation.TRUSTED,
        network_type=NetworkType.CORPORATE,
        is_tor=True,
        resource_sensitivity=ResourceSensitivity.LOW,
    )
    assert result.score == 25
    factor = next(f for f in result.factors if f.name == "tor_anonymizer")
    assert factor.points == 25

def test_09_unusual_location_points():
    """TEST 09: Unusual location => +20"""
    result = RiskEngine.calculate_risk(
        device_posture=DevicePosture.HEALTHY,
        ip_reputation=IPReputation.TRUSTED,
        network_type=NetworkType.CORPORATE,
        unusual_location=True,
        resource_sensitivity=ResourceSensitivity.LOW,
    )
    assert result.score == 20
    factor = next(f for f in result.factors if f.name == "unusual_location")
    assert factor.points == 20

def test_10_unusual_time_points():
    """TEST 10: Unusual time => +10"""
    result = RiskEngine.calculate_risk(
        device_posture=DevicePosture.HEALTHY,
        ip_reputation=IPReputation.TRUSTED,
        network_type=NetworkType.CORPORATE,
        unusual_time=True,
        resource_sensitivity=ResourceSensitivity.LOW,
    )
    assert result.score == 10
    factor = next(f for f in result.factors if f.name == "unusual_time")
    assert factor.points == 10

def test_11_failed_attempts_scaling():
    """TEST 11: Failed attempts (0 => +0, 1-2 => +10, 3-4 => +20, 5+ => +30)"""
    r0 = RiskEngine.calculate_risk(failed_attempts=0, resource_sensitivity=ResourceSensitivity.LOW)
    assert r0.score == 0

    r1 = RiskEngine.calculate_risk(failed_attempts=1, resource_sensitivity=ResourceSensitivity.LOW)
    assert r1.score == 10

    r3 = RiskEngine.calculate_risk(failed_attempts=4, resource_sensitivity=ResourceSensitivity.LOW)
    assert r3.score == 20

    r5 = RiskEngine.calculate_risk(failed_attempts=6, resource_sensitivity=ResourceSensitivity.LOW)
    assert r5.score == 30

def test_12_recent_resource_count_scaling():
    """TEST 12: Recent resource count (0-3 => +0, 4-6 => +5, 7+ => +10)"""
    r2 = RiskEngine.calculate_risk(recent_resource_count=2, resource_sensitivity=ResourceSensitivity.LOW)
    assert r2.score == 0

    r5 = RiskEngine.calculate_risk(recent_resource_count=5, resource_sensitivity=ResourceSensitivity.LOW)
    assert r5.score == 5

    r8 = RiskEngine.calculate_risk(recent_resource_count=8, resource_sensitivity=ResourceSensitivity.LOW)
    assert r8.score == 10

def test_13_resource_sensitivity_modifiers():
    """TEST 13: Resource sensitivity (Low => +0, Medium => +5, High => +10, Critical => +15)"""
    low = RiskEngine.calculate_risk(resource_sensitivity=ResourceSensitivity.LOW)
    assert low.score == 0

    med = RiskEngine.calculate_risk(resource_sensitivity=ResourceSensitivity.MEDIUM)
    assert med.score == 5

    high = RiskEngine.calculate_risk(resource_sensitivity=ResourceSensitivity.HIGH)
    assert high.score == 10

    crit = RiskEngine.calculate_risk(resource_sensitivity=ResourceSensitivity.CRITICAL)
    assert crit.score == 15

def test_14_to_17_risk_boundaries():
    """TEST 14-17: Boundary conditions (39 -> LOW, 40 -> MEDIUM, 69 -> MEDIUM, 70 -> HIGH)"""
    assert RiskEngine.classify_level(0) == RiskLevel.LOW
    assert RiskEngine.classify_level(39) == RiskLevel.LOW
    assert RiskEngine.classify_level(40) == RiskLevel.MEDIUM
    assert RiskEngine.classify_level(69) == RiskLevel.MEDIUM
    assert RiskEngine.classify_level(70) == RiskLevel.HIGH
    assert RiskEngine.classify_level(100) == RiskLevel.HIGH

def test_18_score_capping_at_100():
    """TEST 18: Score never exceeds 100 even if raw sum is much higher"""
    result = RiskEngine.calculate_risk(
        device_posture=DevicePosture.COMPROMISED, # 60
        ip_reputation=IPReputation.MALICIOUS,     # 50
        is_tor=True,                              # 25
        unusual_location=True,                    # 20
        failed_attempts=5,                        # 30
        resource_sensitivity=ResourceSensitivity.CRITICAL # 15
    )
    assert result.raw_score == 200
    assert result.score == 100
    assert result.level == RiskLevel.HIGH

def test_19_score_never_below_zero():
    """TEST 19: Score never goes below 0"""
    result = RiskEngine.calculate_risk(
        device_posture=DevicePosture.HEALTHY,
        ip_reputation=IPReputation.TRUSTED,
        network_type=NetworkType.CORPORATE,
        resource_sensitivity=ResourceSensitivity.LOW,
    )
    assert result.score >= 0

def test_20_deterministic_evaluation():
    """TEST 20: Exact same input context produces exact same score and factors"""
    args = dict(
        device_posture=DevicePosture.UNKNOWN,
        ip_reputation=IPReputation.SUSPICIOUS,
        network_type=NetworkType.PUBLIC_WIFI,
        resource_sensitivity=ResourceSensitivity.HIGH,
    )
    res1 = RiskEngine.calculate_risk(**args)
    res2 = RiskEngine.calculate_risk(**args)
    assert res1.score == res2.score
    assert res1.level == res2.level
    assert res1.raw_score == res2.raw_score
    assert len(res1.factors) == len(res2.factors)

def test_21_scenario_a_is_low(admin_client, db_session):
    """TEST 21: Scenario A evaluates to LOW risk"""
    seed_database(db_session)
    response = admin_client.get("/api/risk/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    sc_a = next(s for s in scenarios if s["scenario_id"] == "scenario-a")
    assert sc_a["risk"]["level"] == "LOW"
    assert sc_a["risk"]["score"] < 40

def test_22_scenario_b_is_medium(admin_client, db_session):
    """TEST 22: Scenario B evaluates to MEDIUM risk (40-69)"""
    seed_database(db_session)
    response = admin_client.get("/api/risk/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    sc_b = next(s for s in scenarios if s["scenario_id"] == "scenario-b")
    assert sc_b["risk"]["level"] == "MEDIUM"
    assert 40 <= sc_b["risk"]["score"] <= 69

def test_23_scenario_c_is_high(admin_client, db_session):
    """TEST 23: Scenario C evaluates to HIGH risk (70-100)"""
    seed_database(db_session)
    response = admin_client.get("/api/risk/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    sc_c = next(s for s in scenarios if s["scenario_id"] == "scenario-c")
    assert sc_c["risk"]["level"] == "HIGH"
    assert sc_c["risk"]["score"] >= 70

def test_24_api_evaluate_by_id_and_direct_payload(admin_client, db_session):
    """TEST 24: POST /api/risk/evaluate with valid ID and direct payload"""
    seed_database(db_session)
    req = db_session.query(AccessRequest).first()
    assert req is not None

    # Test by ID
    res1 = admin_client.post("/api/risk/evaluate", json={"access_request_id": req.id})
    assert res1.status_code == 200
    data1 = res1.json()
    assert "score" in data1
    assert "level" in data1
    assert "factors" in data1

    # Test direct payload
    res2 = admin_client.post(
        "/api/risk/evaluate",
        json={
            "device_posture": "Unknown",
            "ip_reputation": "Suspicious",
            "network_type": "Public WiFi",
        },
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["score"] == 65 # 15 + 30 + 15 + 5 (med resource default)
    assert data2["level"] == "MEDIUM"

    # Test invalid ID
    res_err = admin_client.post("/api/risk/evaluate", json={"access_request_id": "nonexistent-id"})
    assert res_err.status_code == 404
