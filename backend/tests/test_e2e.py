import pytest
from sqlalchemy.orm import Session
from typing import Generator
from datetime import datetime, timedelta, timezone

from app.models.user import User
from app.models.device import Device
from app.models.resource import Resource
from app.models.access_request import AccessRequest
from app.models.pep import EnforcementEvent
from app.models.policy import Policy
from app.models.mfa import MFAChallenge
from app.seed.seed_data import seed_database
from app.policy.seed import seed_policies
from app.segmentation.seed import seed_segments, seed_segment_rules
from app.models.enums import PolicyEffect, DevicePosture

@pytest.fixture(autouse=True)
def setup_seed_data(db_session: Session) -> Generator:
    # Clear out all data
    db_session.query(EnforcementEvent).delete()
    db_session.query(MFAChallenge).delete()
    db_session.query(AccessRequest).delete()
    db_session.query(Policy).delete()
    
    seed_database(db_session)
    seed_policies(db_session)
    seed_segments(db_session)
    seed_segment_rules(db_session)
    
    yield
    
def get_entity_ids(db: Session, username: str, resource_name: str):
    user = db.query(User).filter(User.username == username).first()
    dev = db.query(Device).filter(Device.owner_user_id == user.id).first()
    res = db.query(Resource).filter(Resource.name == resource_name).first()
    return user.id, dev.id, res.id

def create_request(db: Session, username: str, resource_name: str, **kwargs) -> AccessRequest:
    u, d, r = get_entity_ids(db, username, resource_name)
    
    req_args = dict(
        user_id=u,
        device_id=d,
        resource_id=r,
        source_ip="10.0.0.50",
        source_segment="Development",
        network_type="CORPORATE",
        country="India",
        city="Bengaluru",
        is_tor=False,
        failed_attempts=0
    )
    req_args.update(kwargs)
    
    req = AccessRequest(**req_args)
    db.add(req)
    db.commit()
    db.refresh(req)
    return req

# =========================================================
# E2E SCENARIOS
# =========================================================

def test_scenario_a_normal_developer(alice_client, db_session: Session):
    # Scenario A: Alice -> Git Repo -> Normal -> GRANTED
    req = db_session.query(AccessRequest).filter(AccessRequest.source_ip == "10.0.4.15").first()
    
    # 1. API Enforcement
    res = alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
    assert res.status_code == 200
    data = res.json()
    assert data["access_granted"] is True, data
    assert data["decision"] == PolicyEffect.ALLOW.value, data
    
    # 2. Log API validation
    logs_res = alice_client.get(f"/api/logs?user_id={req.user_id}")
    assert logs_res.status_code == 200
    logs = logs_res.json()
    
    # At least one event
    my_logs = [l for l in logs if l["access_request_id"] == req.id]
    assert len(my_logs) >= 1
    log = my_logs[-1] # Get latest
    assert log["decision"] == "ALLOW"
    assert log["source_segment"] == "Development"
    assert log["destination_segment"] == "Development"
    assert log["access_granted"] is True

def test_scenario_b_elevated_risk_stepup(alice_client, db_session: Session):
    # Scenario B: Alice -> Git Repo -> Public Wi-Fi -> MFA -> ALLOW
    req = db_session.query(AccessRequest).filter(AccessRequest.source_ip == "198.51.100.42").first()
    
    # 1. Enforce -> MFA REQUIRED
    res1 = alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
    data1 = res1.json()
    assert data1["access_granted"] is False
    assert data1["decision"] == PolicyEffect.MFA_REQUIRED.value
    
    # Verify no final audit event says GRANTED
    logs = alice_client.get(f"/api/logs").json()
    my_logs = [l for l in logs if l["access_request_id"] == req.id]
    assert len(my_logs) >= 1
    assert my_logs[0]["decision"] == "MFA_REQUIRED"
    assert my_logs[0]["access_granted"] is False
    
    # 2. Challenge
    chal_res = alice_client.post("/api/mfa/challenge", json={"access_request_id": req.id})
    assert chal_res.status_code == 200
    chal = chal_res.json()
    chal_id = chal["id"]
    code = chal["demo_otp"] # Simulated code return
    
    # 3. Verify
    ver_res = alice_client.post("/api/mfa/verify", json={"challenge_id": chal_id, "code": code})
    assert ver_res.status_code == 200
    
    # 4. Enforce again to get final decision
    pep_res = alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
    ver = pep_res.json()
    
    # PDP Re-evaluation should allow -> PEP enforcer checks segmentation -> ALLOW -> GRANTED
    assert ver["access_granted"] is True
    assert ver["decision"] == "ALLOW"
    
    # 4. Logs -> Check that the NEW enforcement event is GRANTED
    logs2 = alice_client.get(f"/api/logs?limit=50").json()
    my_logs2 = [l for l in logs2 if l["access_request_id"] == req.id]
    # We should have events
    assert len(my_logs2) >= 2
    granted_log = next(l for l in reversed(my_logs2) if l["access_granted"] is True)
    assert granted_log["decision"] == "ALLOW"

def test_scenario_c_high_risk_breach(alice_client, db_session: Session):
    # Scenario C: Alice -> Git Repo -> Tor -> DENY
    req = db_session.query(AccessRequest).filter(AccessRequest.is_tor == True).first()
    
    res = alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
    data = res.json()
    assert data["access_granted"] is False
    assert data["decision"] == PolicyEffect.DENY.value
    
    logs = alice_client.get(f"/api/logs").json()
    my_logs = [l for l in logs if l["access_request_id"] == req.id]
    assert len(my_logs) >= 1
    assert my_logs[-1]["decision"] == "DENY"

def test_scenario_d_mfa_success_but_segmentation_deny(alice_client, db_session: Session):
    # Scenario D: Alice -> HR DB -> MFA Success -> Segmentation Denies
    req = create_request(db_session, "alice", "HR Database", source_segment="Development", network_type="PUBLIC_WIFI", is_known_network=False, ip_reputation="UNKNOWN")
    
    # 1. Enforce -> Should hit MFA first (due to role or risk)
    # Wait, the HR DB policy might just DENY Alice outright.
    # Let's adjust policy so Alice gets MFA instead of DENY.
    # HR DB policy requires role=HR, else default deny.
    # Let's create a temporary policy to ALLOW Alice to HR Database but require MFA, just to test microsegmentation block.
    hr_res_id = db_session.query(Resource).filter(Resource.name == "HR Database").first().id
    import uuid
    p = Policy(
        id=str(uuid.uuid4()),
        name="Test MFA to HR",
        description="Allow developer to HR with MFA to test segmentation",
        effect=PolicyEffect.MFA_REQUIRED,
        priority=1000, # Highest
        enabled=True,
        required_role="Developer",
        resource_id=hr_res_id
    )
    db_session.add(p)
    db_session.commit()
    
    res1 = alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
    assert res1.json()["decision"] == "MFA_REQUIRED"
    assert res1.json()["access_granted"] is False
    
    chal_res = alice_client.post("/api/mfa/challenge", json={"access_request_id": req.id})
    chal = chal_res.json()
    chal_id = chal["id"]
    code = chal["demo_otp"]
    
    # 2. Verify MFA
    ver_res = alice_client.post("/api/mfa/verify", json={"challenge_id": chal_id, "code": code})
    assert ver_res.status_code == 200
    
    # 3. Enforce again
    pep_res = alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
    ver = pep_res.json()
    
    assert ver["decision"] == "ALLOW" # The PDP says allow now!
    assert ver["access_granted"] is False # But the PEP says no!
    assert "blocking traffic" in ver["reason"].lower() or ver["segment_check"]["allowed"] is False
    
    # Logs check
    logs = alice_client.get(f"/api/logs").json()
    my_logs = [l for l in logs if l["access_request_id"] == req.id]
    final_log = max(my_logs, key=lambda x: x["timestamp"])
    
    # Log MUST show it was blocked
    assert final_log["access_granted"] is False
    assert final_log["decision"] == "ALLOW" # Policy decision was allow
    assert final_log["destination_segment"] == "HR_Secure"

# =========================================================
# ADDITIONAL SECURITY INVARIANT TESTS
# =========================================================

def test_inv_disabled_user(alice_client, db_session: Session):
    u = db_session.query(User).filter(User.username == "alice").first()
    u.status = "DISABLED"
    db_session.commit()
    
    try:
        req = create_request(db_session, "alice", "Git Repository")
        res = alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
        assert res.json()["decision"] == "DENY", res.json()
        assert res.json()["access_granted"] is False
    finally:
        u.status = "ACTIVE"
        db_session.commit()

def test_inv_disabled_resource(alice_client, db_session: Session):
    r = db_session.query(Resource).filter(Resource.name == "Git Repository").first()
    r.enabled = False
    db_session.commit()
    
    try:
        req = create_request(db_session, "alice", "Git Repository")
        res = alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
        assert res.json()["decision"] == "DENY", res.json()
        assert res.json()["access_granted"] is False
    finally:
        r.enabled = True
        db_session.commit()

def test_inv_compromised_device(alice_client, db_session: Session):
    u = db_session.query(User).filter(User.username == "alice").first()
    d = db_session.query(Device).filter(Device.owner_user_id == u.id).first()
    d.compromised = True
    d.posture_status = DevicePosture.COMPROMISED
    db_session.commit()
    
    try:
        req = create_request(db_session, "alice", "Git Repository")
        res = alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
        assert res.json()["decision"] == "DENY", res.json()
        assert res.json()["access_granted"] is False
    finally:
        d.compromised = False
        d.posture_status = DevicePosture.HEALTHY
        db_session.commit()

def test_inv_mfa_invalid_otp(alice_client, db_session: Session):
    req = db_session.query(AccessRequest).filter(AccessRequest.source_ip == "198.51.100.42").first()
    alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
    chal = alice_client.post("/api/mfa/challenge", json={"access_request_id": req.id}).json()
    
    res = alice_client.post("/api/mfa/verify", json={"challenge_id": chal["id"], "code": "999999"})
    assert res.status_code == 400
    assert "Invalid" in res.json()["detail"]

def test_inv_mfa_expired(alice_client, db_session: Session):
    req = db_session.query(AccessRequest).filter(AccessRequest.source_ip == "198.51.100.42").first()
    alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
    chal = alice_client.post("/api/mfa/challenge", json={"access_request_id": req.id}).json()
    
    # manually expire
    db_chal = db_session.query(MFAChallenge).filter(MFAChallenge.id == chal["id"]).first()
    db_chal.expires_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db_session.commit()
    
    res = alice_client.post("/api/mfa/verify", json={"challenge_id": chal["id"], "code": chal["demo_otp"]})
    assert res.status_code == 400
    assert "expired" in res.json()["detail"].lower()

def test_inv_mfa_replay(alice_client, db_session: Session):
    req = db_session.query(AccessRequest).filter(AccessRequest.source_ip == "198.51.100.42").first()
    alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
    chal = alice_client.post("/api/mfa/challenge", json={"access_request_id": req.id}).json()
    
    # First verify is OK
    res1 = alice_client.post("/api/mfa/verify", json={"challenge_id": chal["id"], "code": chal["demo_otp"]})
    assert res1.status_code == 200
    
    # Second verify of same OTP -> blocked
    res2 = alice_client.post("/api/mfa/verify", json={"challenge_id": chal["id"], "code": chal["demo_otp"]})
    assert res2.status_code == 400
    assert "verified" in res2.json()["detail"].lower() or "used" in res2.json()["detail"].lower()

def test_inv_mfa_verified_but_pdp_re_eval_deny(alice_client, db_session: Session):
    # If the risk increases drastically right after MFA, the re-eval should catch it.
    req = db_session.query(AccessRequest).filter(AccessRequest.source_ip == "198.51.100.42").first()
    alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
    chal = alice_client.post("/api/mfa/challenge", json={"access_request_id": req.id}).json()
    
    # simulate device compromised before verify
    d = db_session.query(Device).filter(Device.id == req.device_id).first()
    d.compromised = True
    d.posture_status = DevicePosture.COMPROMISED
    db_session.commit()
    
    try:
        ver_res = alice_client.post("/api/mfa/verify", json={"challenge_id": chal["id"], "code": chal["demo_otp"]})
        assert ver_res.status_code == 200
        
        pep_res = alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
        res = pep_res.json()
        assert res["decision"] == "DENY", res
        assert res["access_granted"] is False
    finally:
        d.compromised = False
        d.posture_status = DevicePosture.HEALTHY
        db_session.commit()

def test_inv_default_deny(alice_client, db_session: Session):
    # Disable all policies
    db_session.query(Policy).update({"enabled": False})
    db_session.commit()
    
    try:
        req = create_request(db_session, "alice", "Git Repository")
        res = alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
        assert res.json()["decision"] == "DENY", res.json()
        assert res.json()["access_granted"] is False
    finally:
        db_session.query(Policy).update({"enabled": True})
        db_session.commit()

def test_inv_disabled_policy(alice_client, db_session: Session):
    # There's a policy allowing Git access. Let's disable it.
    p = db_session.query(Policy).filter(Policy.name == "Developer Git Access").first()
    p.enabled = False
    db_session.commit()
    
    try:
        req = create_request(db_session, "alice", "Git Repository")
        res = alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
        # Since only Developer Git Access allows Alice to Git Repository (and Admin Everything),
        # disabling it should result in default deny.
        assert res.json()["decision"] == "DENY", res.json()
        assert res.json()["access_granted"] is False
    finally:
        p.enabled = True
        db_session.commit()
    
def test_inv_policy_priority(alice_client, db_session: Session):
    # Add a DENY policy with higher priority
    r = db_session.query(Resource).filter(Resource.name == "Git Repository").first()
    import uuid
    p = Policy(
        id=str(uuid.uuid4()),
        name="High Priority Deny",
        description="Deny all",
        effect=PolicyEffect.DENY,
        priority=0, # Lowest number = highest priority
        enabled=True,
        resource_id=r.id
    )
    db_session.add(p)
    db_session.commit()
    
    try:
        req = create_request(db_session, "alice", "Git Repository")
        res = alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
        assert res.json()["decision"] == "DENY", res.json()
    finally:
        db_session.delete(p)
        db_session.commit()

def test_api_topology_and_dashboard_integrity(alice_client, admin_client, db_session: Session):
    req = create_request(db_session, "alice", "Git Repository")
    alice_client.post("/api/pep/enforce", json={"access_request_id": req.id})
    
    # Topology should return this edge
    topo = alice_client.get("/api/topology").json()
    assert len(topo["nodes"]) > 0
    assert len(topo["edges"]) > 0
    
    # Dashboard summary should have >= 1 allowed request (Admin only)
    dash = admin_client.get("/api/dashboard/summary").json()
    assert "metrics" in dash, dash
    assert dash["metrics"]["total_requests"] >= 1
    
    # Dashboard recent activity should have it (Admin only)
    act = admin_client.get("/api/dashboard/recent-activity").json()
    assert len(act) > 0
    assert "id" in act[0], act[0]
